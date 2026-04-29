"""
Custom authentication backend with enhanced security features.
"""
import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
import hashlib

logger = logging.getLogger(__name__)
User = get_user_model()

class SecureAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend with additional security features:
    - Rate limiting for failed login attempts
    - Account lockout after multiple failed attempts
    - Login attempt logging
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        # Check if account is temporarily locked
        if self.is_account_locked(username):
            logger.warning(f"Login attempt on locked account: {username}")
            return None
        
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            # Still check password to prevent timing attacks
            User().check_password(password)
            self.record_failed_attempt(username)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            # Reset failed attempts on successful login
            self.reset_failed_attempts(username)
            
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            logger.info(f"Successful login for user: {username}")
            return user
        else:
            # Record failed attempt
            self.record_failed_attempt(username)
            logger.warning(f"Failed login attempt for user: {username}")
            return None
    
    def get_cache_key(self, username):
        """Generate cache key for failed attempts."""
        username_hash = hashlib.md5(username.encode()).hexdigest()
        return f"failed_login_{username_hash}"
    
    def is_account_locked(self, username):
        """Check if account is temporarily locked due to failed attempts."""
        cache_key = self.get_cache_key(username)
        failed_attempts = cache.get(cache_key, 0)
        return failed_attempts >= 5  # Lock after 5 failed attempts
    
    def record_failed_attempt(self, username):
        """Record a failed login attempt."""
        cache_key = self.get_cache_key(username)
        failed_attempts = cache.get(cache_key, 0) + 1
        
        # Lock account for 15 minutes after 5 failed attempts
        timeout = 900 if failed_attempts >= 5 else 300  # 15 min or 5 min
        cache.set(cache_key, failed_attempts, timeout)
        
        logger.warning(f"Failed attempt #{failed_attempts} for username: {username}")
    
    def reset_failed_attempts(self, username):
        """Reset failed login attempts for successful login."""
        cache_key = self.get_cache_key(username)
        cache.delete(cache_key)
    
    def user_can_authenticate(self, user):
        """Check if user is allowed to authenticate."""
        # Add additional checks here if needed
        return getattr(user, 'is_active', True)


class EmailAuthenticationBackend(SecureAuthenticationBackend):
    """
    Authentication backend that allows login with email address.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
        
        # Try to authenticate with email
        return super().authenticate(request, username, password, **kwargs)
