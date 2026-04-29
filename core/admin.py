from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.contrib import messages
from .models import User, Query, Advice, AIDisease, Notification
from .email_utils import send_activation_email


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for User model with enhanced display and filtering.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'address')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('user_type', 'phone_number', 'address')}),
    )
    
    actions = ['activate_users', 'deactivate_users', 'send_activation_emails']
    
    def activate_users(self, request, queryset):
        """Bulk activate selected users and send activation emails."""
        activated_count = 0
        email_count = 0
        
        for user in queryset:
            if not user.is_active:
                user.is_active = True
                user.save()
                activated_count += 1
                
                # Send activation email
                if send_activation_email(user):
                    email_count += 1
        
        self.message_user(
            request, 
            f'{activated_count} users have been activated. {email_count} activation emails sent.',
            messages.SUCCESS
        )
    activate_users.short_description = "Activate selected users and send emails"
    
    def deactivate_users(self, request, queryset):
        """Bulk deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users have been deactivated.')
    deactivate_users.short_description = "Deactivate selected users"
    
    def send_activation_emails(self, request, queryset):
        """Send activation emails to selected active users."""
        email_count = 0
        
        for user in queryset.filter(is_active=True):
            if send_activation_email(user):
                email_count += 1
        
        self.message_user(
            request,
            f'Activation emails sent to {email_count} users.',
            messages.SUCCESS
        )
    send_activation_emails.short_description = "Send activation emails to selected users"


@admin.register(Query)
class QueryAdmin(admin.ModelAdmin):
    """
    Admin configuration for Query model.
    """
    list_display = ('id', 'farmer', 'title', 'status', 'created_at', 'advice_count')
    list_filter = ('status', 'created_at')
    search_fields = ('farmer__username', 'farmer__email', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('farmer', 'title', 'description', 'crop_image', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def advice_count(self, obj):
        """Display number of advice responses for this query."""
        count = obj.advice_responses.count()
        if count > 0:
            return format_html('<span style="color: green;">{}</span>', count)
        return format_html('<span style="color: red;">0</span>')
    advice_count.short_description = 'Advice Count'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('farmer')


@admin.register(Advice)
class AdviceAdmin(admin.ModelAdmin):
    """
    Admin configuration for Advice model.
    """
    list_display = ('id', 'query', 'expert', 'confidence_level', 'created_at')
    list_filter = ('confidence_level', 'created_at')
    search_fields = ('expert__username', 'expert__email', 'query__title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('query', 'expert', 'content', 'confidence_level')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('query', 'expert')


@admin.register(AIDisease)
class AIDiseaseAdmin(admin.ModelAdmin):
    """
    Admin configuration for AI Disease model.
    """
    list_display = ('id', 'user', 'predicted_disease', 'confidence_score', 'created_at')
    list_filter = ('predicted_disease', 'created_at')
    search_fields = ('user__username', 'user__email', 'predicted_disease')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for Notification model.
    """
    list_display = ('id', 'user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        """Mark selected notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        """Mark selected notifications as unread."""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
