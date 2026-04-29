"""
Email utility functions for the AgriVision AI agricultural advisory platform.
Handles sending various types of notifications to users.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site
import logging

logger = logging.getLogger(__name__)

def get_site_url():
    """Get the base site URL for email links."""
    try:
        current_site = Site.objects.get_current()
        return f"http://{current_site.domain}"
    except:
        return "http://127.0.0.1:8000"  # Fallback for development

def send_welcome_email(user):
    """
    Send welcome email to newly registered user pending admin approval.
    """
    try:
        site_url = get_site_url()
        context = {
            'user': user,
            'site_url': site_url,
            'login_url': f"{site_url}{reverse('core:login')}",
        }
        
        # Render HTML email
        html_content = render_to_string('emails/welcome_pending_activation.html', context)
        text_content = strip_tags(html_content)
        
        subject = f"Welcome to AgriVision AI - Account Pending Approval"
        
        # Create email message
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Send email
        msg.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        return False

def send_activation_email(user):
    """
    Send account activation confirmation email.
    """
    try:
        site_url = get_site_url()
        context = {
            'user': user,
            'site_url': site_url,
            'login_url': f"{site_url}{reverse('core:login')}",
            'dashboard_url': f"{site_url}{reverse('core:dashboard')}",
            'profile_url': f"{site_url}{reverse('core:update_profile')}",
        }
        
        # Render HTML email
        html_content = render_to_string('emails/account_activated.html', context)
        text_content = strip_tags(html_content)
        
        subject = f"Account Activated - Welcome to AgriVision AI!"
        
        # Create email message
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Send email
        msg.send()
        
        logger.info(f"Activation email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send activation email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(user, reset_link):
    """
    Send password reset email with secure reset link.
    """
    try:
        site_url = get_site_url()
        context = {
            'user': user,
            'password_reset_url': reset_link,
            'site_url': site_url,
            'support_email': settings.DEFAULT_FROM_EMAIL,
            'login_url': f"{site_url}{reverse('core:login')}",
        }
        
        # Render HTML email
        html_content = render_to_string('emails/password_reset.html', context)
        text_content = strip_tags(html_content)
        
        subject = f"Password Reset Request - AgriVision AI"
        
        # Create email message
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Send email
        msg.send()
        
        logger.info(f"Password reset email sent to {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

def send_new_advice_notification(query, advice):
    """
    Send notification to farmer when expert provides new advice.
    """
    try:
        site_url = get_site_url()
        context = {
            'query': query,
            'advice': advice,
            'site_url': site_url,
            'advice_url': f"{site_url}{reverse('core:query_detail', kwargs={'pk': query.pk})}",
            'new_query_url': f"{site_url}{reverse('core:create_query')}",
            'expert_total_advice': 50,  # This would come from actual count
            'response_time': '12h',  # This would be calculated
            'farmer_rating': '4.8',  # This would come from actual ratings
        }
        
        # Render HTML email
        html_content = render_to_string('emails/new_advice_notification.html', context)
        text_content = strip_tags(html_content)
        
        subject = f"New Expert Advice for Your Query | आपके प्रश्न के लिए विशेषज्ञ सलाह"
        
        # Create email message
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[query.farmer.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Send email
        msg.send()
        
        logger.info(f"New advice notification sent to {query.farmer.email} for query {query.pk}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send advice notification to {query.farmer.email}: {str(e)}")
        return False

def send_query_received_notification(query):
    """
    Send confirmation email to farmer when query is received.
    """
    try:
        site_url = get_site_url()
        
        subject = f"Query Received - We're Finding an Expert | प्रश्न प्राप्त हुआ - हम विशेषज्ञ खोज रहे हैं"
        
        message = f"""
        Dear {query.farmer.get_full_name() or query.farmer.username},
        
        Your agricultural query "{query.title}" has been successfully received.
        
        Query Details:
        - Title: {query.title}
        - Description: {query.description[:100]}...
        - Submitted: {query.created_at.strftime('%B %d, %Y at %I:%M %p')}
        
        Our agricultural experts will review your query and provide professional advice soon.
        You will receive an email notification when an expert responds.
        
        Track your query: {site_url}{reverse('core:query_detail', kwargs={'pk': query.pk})}
        
        Thank you for using AgriVision AI!
        
        Best regards,
        The AgriVision AI Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[query.farmer.email],
            fail_silently=False,
        )
        
        logger.info(f"Query confirmation sent to {query.farmer.email} for query {query.pk}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send query confirmation to {query.farmer.email}: {str(e)}")
        return False

def send_expert_new_query_notification(expert, query):
    """
    Send notification to expert about new query in their area of expertise.
    """
    try:
        site_url = get_site_url()
        
        subject = f"New Agricultural Query | नया कृषि प्रश्न"
        
        message = f"""
        Dear {expert.get_full_name() or expert.username},
        
        A new agricultural query has been submitted that matches your expertise:
        
        Query Details:
        - Farmer: {query.farmer.get_full_name() or query.farmer.username}
        - Title: {query.title}
        - Description: {query.description[:150]}...
        - Submitted: {query.created_at.strftime('%B %d, %Y at %I:%M %p')}
        
        Please review and provide your expert advice to help the farmer.
        
        Respond to query: {site_url}{reverse('core:pending_queries')}
        
        Thank you for your valuable contribution to the farming community!
        
        Best regards,
        The AgriVision AI Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[expert.email],
            fail_silently=False,
        )
        
        logger.info(f"New query notification sent to expert {expert.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send query notification to expert {expert.email}: {str(e)}")
        return False

def send_admin_user_registration_notification(user):
    """
    Send notification to admin when new user registers.
    """
    try:
        admin_emails = [admin[1] for admin in settings.ADMINS]
        if not admin_emails:
            return True  # No admins configured
            
        site_url = get_site_url()
        
        subject = f"New User Registration - Approval Required | नया उपयोगकर्ता पंजीकरण"
        
        message = f"""
        A new user has registered on AgriVision AI and is pending approval:
        
        User Details:
        - Name: {user.get_full_name() or 'Not provided'}
        - Username: {user.username}
        - Email: {user.email}
        - User Type: {user.get_user_type_display()}
        - Phone: {user.phone_number or 'Not provided'}
        - Address: {user.address or 'Not provided'}
        - Registration Date: {user.date_joined.strftime('%B %d, %Y at %I:%M %p')}
        
        Please review and approve/reject this user account.
        
        Admin Panel: {site_url}/admin/
        
        Best regards,
        AgriVision AI System
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )
        
        logger.info(f"Admin notification sent for new user registration: {user.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send admin notification for user {user.email}: {str(e)}")
        return False
