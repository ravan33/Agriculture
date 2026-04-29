"""
Session management utilities and views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import gettext as _
import logging

logger = logging.getLogger(__name__)

@login_required
def session_management(request):
    """View for users to manage their active sessions."""
    user_sessions = []
    current_session_key = request.session.session_key
    
    try:
        # Get all active sessions
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        
        for session in sessions:
            session_data = session.get_decoded()
            session_user_id = session_data.get('_auth_user_id')
            
            if session_user_id and int(session_user_id) == request.user.id:
                session_info = {
                    'session_key': session.session_key,
                    'is_current': session.session_key == current_session_key,
                    'last_activity': session_data.get('last_activity'),
                    'login_time': session_data.get('login_time'),
                    'ip_address': session_data.get('ip_address', 'Unknown'),
                    'user_agent': session_data.get('user_agent', 'Unknown')[:100],
                    'page_views': session_data.get('page_views', 0),
                    'expire_date': session.expire_date,
                }
                user_sessions.append(session_info)
    
    except Exception as e:
        logger.error(f"Error retrieving sessions for user {request.user.username}: {e}")
        messages.error(request, _("Error retrieving session information."))
    
    context = {
        'user_sessions': user_sessions,
        'total_sessions': len(user_sessions),
    }
    
    return render(request, 'core/session_management.html', context)

@login_required
@require_POST
@csrf_protect
def terminate_session(request):
    """Terminate a specific session."""
    session_key = request.POST.get('session_key')
    current_session_key = request.session.session_key
    
    if not session_key:
        return JsonResponse({'success': False, 'error': 'No session key provided'})
    
    if session_key == current_session_key:
        return JsonResponse({'success': False, 'error': 'Cannot terminate current session'})
    
    try:
        session = Session.objects.get(session_key=session_key)
        session_data = session.get_decoded()
        session_user_id = session_data.get('_auth_user_id')
        
        # Verify the session belongs to the current user
        if session_user_id and int(session_user_id) == request.user.id:
            session.delete()
            logger.info(f"Session {session_key} terminated by user {request.user.username}")
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Unauthorized'})
    
    except Session.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Session not found'})
    except Exception as e:
        logger.error(f"Error terminating session {session_key}: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'})

@login_required
@require_POST
@csrf_protect
def terminate_all_sessions(request):
    """Terminate all sessions except the current one."""
    current_session_key = request.session.session_key
    terminated_count = 0
    
    try:
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        
        for session in sessions:
            if session.session_key != current_session_key:
                session_data = session.get_decoded()
                session_user_id = session_data.get('_auth_user_id')
                
                if session_user_id and int(session_user_id) == request.user.id:
                    session.delete()
                    terminated_count += 1
        
        logger.info(f"User {request.user.username} terminated {terminated_count} sessions")
        return JsonResponse({
            'success': True, 
            'terminated_count': terminated_count
        })
    
    except Exception as e:
        logger.error(f"Error terminating sessions for user {request.user.username}: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'})

def force_logout_all_users():
    """Utility function to force logout all users (for admin use)."""
    try:
        Session.objects.all().delete()
        logger.info("All user sessions terminated")
        return True
    except Exception as e:
        logger.error(f"Error terminating all sessions: {e}")
        return False

@login_required
def session_info_ajax(request):
    """AJAX endpoint to get current session information."""
    try:
        session_info = {
            'session_key': request.session.session_key,
            'last_activity': request.session.get('last_activity'),
            'login_time': request.session.get('login_time'),
            'page_views': request.session.get('page_views', 0),
            'ip_address': request.session.get('ip_address'),
            'expires_in': (timezone.now() + timezone.timedelta(seconds=request.session.get_expiry_age())).isoformat(),
        }
        return JsonResponse({'success': True, 'session_info': session_info})
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        return JsonResponse({'success': False, 'error': 'Server error'})
