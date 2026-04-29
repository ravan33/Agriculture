"""
Custom middleware for enhanced session management and security.
"""
import time
import logging
from django.contrib.auth import logout
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)

class SessionSecurityMiddleware:
    """
    Enhanced session security middleware that handles:
    1. Session timeout
    2. Server restart detection
    3. Automatic logout on security issues
    4. Session activity tracking
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.server_start_time = self._get_or_set_server_start_time()

    def _get_or_set_server_start_time(self):
        """Persist server start time in a file so it remains consistent across requests and restarts."""
        import os
        import pathlib
        base_dir = pathlib.Path(__file__).resolve().parent.parent
        file_path = os.path.join(base_dir, 'server_start_time.txt')
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return f.read().strip()
        else:
            start_time = str(time.time())
            with open(file_path, 'w') as f:
                f.write(start_time)
            return start_time
        
    def __call__(self, request):
        # Process request before view
        self.process_request(request)
        response = self.get_response(request)
        # Process response after view
        self.process_response(request, response)
        return response

    def process_request(self, request):
        """Process incoming request for session security."""
        # Check if user attribute exists (after AuthenticationMiddleware)
        if not hasattr(request, 'user'):
            return
        if request.user.is_authenticated:
            current_time = timezone.now()
            # Check if session has server start time marker
            session_server_start = request.session.get('server_start_time')
            if session_server_start is not None and session_server_start != self.server_start_time:
                # Server was restarted, force logout
                logger.info(f"Server restart detected for user {request.user.username}, forcing logout")
                request.session['force_logout_reason'] = 'server_restart'
                logout(request)
                return
            elif session_server_start is None:
                # Set session server start time if missing
                request.session['server_start_time'] = self.server_start_time
            # Check session timeout
            last_activity = request.session.get('last_activity')
            if last_activity:
                last_activity_time = timezone.datetime.fromisoformat(last_activity)
                time_diff = (current_time - last_activity_time).total_seconds()
                if time_diff > settings.SESSION_COOKIE_AGE:
                    logger.info(f"Session timeout for user {request.user.username}")
                    request.session['force_logout_reason'] = 'session_timeout'
                    logout(request)
                    return
            # Update last activity
            request.session['last_activity'] = current_time.isoformat()
            request.session['server_start_time'] = self.server_start_time
            # Track user activity
            request.session['page_views'] = request.session.get('page_views', 0) + 1
    
    def process_response(self, request, response):
        """Process outgoing response."""
        # Show logout reason message if set
        if hasattr(request, 'session') and request.session.get('force_logout_reason'):
            reason = request.session.pop('force_logout_reason', None)
            if reason == 'server_restart':
                messages.warning(request, _("Your session has expired due to server restart. Please log in again."))
            elif reason == 'session_timeout':
                messages.info(request, _("Your session has expired. Please log in again."))
        return response
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        return response


class SingleSessionMiddleware:
    """
    Middleware to ensure only one active session per user.
    If a user logs in from another device/browser, previous sessions are invalidated.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Check if this is a new login
            if 'session_key_verified' not in request.session:
                # This is a new session, invalidate all other sessions for this user
                self.invalidate_other_sessions(request.user, request.session.session_key)
                request.session['session_key_verified'] = True
                request.session['login_time'] = timezone.now().isoformat()
                logger.info(f"New session created for user {request.user.username}")
        
        response = self.get_response(request)
        return response
    
    def invalidate_other_sessions(self, user, current_session_key):
        """Invalidate all other sessions for the given user."""
        try:
            # Get all sessions
            sessions = Session.objects.filter(expire_date__gte=timezone.now())
            
            for session in sessions:
                session_data = session.get_decoded()
                session_user_id = session_data.get('_auth_user_id')
                
                if session_user_id and int(session_user_id) == user.id:
                    if session.session_key != current_session_key:
                        session.delete()
                        logger.info(f"Invalidated old session for user {user.username}")
        except Exception as e:
            logger.error(f"Error invalidating sessions for user {user.username}: {e}")


class ActivityTrackingMiddleware:
    """
    Middleware to track user activity and last seen timestamps.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            # Update user's last activity
            request.user.last_login = timezone.now()
            request.user.save(update_fields=['last_login'])
            
            # Store activity in session
            request.session['last_page'] = request.path
            request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:200]
            request.session['ip_address'] = self.get_client_ip(request)
        
        return response
    
    def get_client_ip(self, request):
        """Get the client's IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CSRFErrorMiddleware:
    """
    Custom middleware to handle CSRF errors gracefully.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Handle CSRF token errors."""
        if isinstance(exception, Exception) and 'CSRF' in str(exception):
            messages.error(request, _("Security token expired. Please try again."))
            return HttpResponseRedirect(request.path)
        return None
