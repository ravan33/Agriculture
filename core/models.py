from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Supports both Farmers and Experts with additional fields.
    """
    USER_TYPE_CHOICES = [
        ('farmer', _('Farmer')),
        ('expert', _('Expert')),
        ('admin', _('Administrator')),
    ]
    
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPE_CHOICES, 
        default='farmer',
        help_text=_('Type of user: Farmer, Expert, or Administrator')
    )
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        help_text=_('Contact phone number')
    )
    address = models.TextField(
        blank=True, 
        null=True,
        help_text=_('Physical address')
    )
    city = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text=_("City for weather forecast, e.g., Hyderabad")
    )
    badges = models.JSONField(
        default=list, 
        blank=True,
        help_text=_('Badges earned by the user')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_user_type_display()})"
    
    @property
    def is_farmer(self):
        return self.user_type == 'farmer'
    
    @property
    def is_expert(self):
        return self.user_type == 'expert'
    
    @property
    def is_admin_user(self):
        return self.user_type == 'admin' or self.is_superuser or self.is_staff
    
    def save(self, *args, **kwargs):
        # Automatically set user_type for superusers and staff
        if self.is_superuser or self.is_staff:
            if self.user_type not in ['admin', 'expert']:
                self.user_type = 'admin'
        super().save(*args, **kwargs)


class Query(models.Model):
    """
    Model representing a farmer's query/request for expert advice.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('answered', 'Answered'),
        ('closed', 'Closed'),
    ]
    
    farmer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='queries',
        help_text='Farmer who submitted the query'
    )
    title = models.CharField(
        max_length=200,
        help_text='Brief title/summary of the issue'
    )
    description = models.TextField(
        help_text='Detailed description of the crop issue or symptoms'
    )
    crop_image = models.ImageField(
        upload_to='query_images/',
        help_text='Image of the affected crop'
    )
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        help_text='Current status of the query'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Queries'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Query by {self.farmer.get_full_name()}: {self.title[:50]}"
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_answered(self):
        return self.status == 'answered'


class Advice(models.Model):
    """
    Model representing expert's advice for a farmer's query.
    """
    query = models.ForeignKey(
        Query, 
        on_delete=models.CASCADE, 
        related_name='advice_responses',
        help_text='Query this advice responds to'
    )
    expert = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='given_advice',
        help_text='Expert who provided the advice'
    )
    content = models.TextField(
        help_text='Expert advice and recommendations'
    )
    confidence_level = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        default='medium',
        help_text='Expert confidence in the advice'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Advice by {self.expert.get_full_name()} for Query #{self.query.id}"
    
    def save(self, *args, **kwargs):
        """
        Auto-update query status to 'answered' when advice is provided.
        """
        super().save(*args, **kwargs)
        if self.query.status == 'pending':
            self.query.status = 'answered'
            self.query.save()


class AIDisease(models.Model):
    """
    Model to store AI disease diagnosis results.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='ai_diagnoses',
        help_text='User who requested the AI diagnosis'
    )
    crop_image = models.ImageField(
        upload_to='ai_diagnosis/',
        help_text='Image used for AI diagnosis'
    )
    predicted_disease = models.CharField(
        max_length=200,
        help_text='AI predicted disease name'
    )
    confidence_score = models.FloatField(
        null=True,
        blank=True,
        default=0.0,
        help_text='AI confidence score (0-1)'
    )
    remedies = models.TextField(
        blank=True,
        null=True,
        help_text='Suggested remedies for the predicted disease'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def confidence_score_display(self):
        """Return confidence score, defaulting to 0.0 if None"""
        return self.confidence_score if self.confidence_score is not None else 0.0
    
    def save(self, *args, **kwargs):
        """Override save to ensure confidence_score has a default value"""
        if self.confidence_score is None:
            self.confidence_score = 0.0
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'AI Disease Diagnosis'
        verbose_name_plural = 'AI Disease Diagnoses'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"AI Diagnosis for {self.user.get_full_name()}: {self.predicted_disease}"


class Notification(models.Model):
    """
    Model for in-app notifications.
    """
    NOTIFICATION_TYPES = [
        ('advice_received', 'Advice Received'),
        ('query_answered', 'Query Answered'),
        ('account_activated', 'Account Activated'),
        ('new_query', 'New Query Available'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        help_text='User to receive the notification'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        help_text='Type of notification'
    )
    title = models.CharField(
        max_length=200,
        help_text='Notification title'
    )
    message = models.TextField(
        help_text='Notification message content'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the notification has been read'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.user.get_full_name()}: {self.title}"


class Rating(models.Model):
    """
    Model for rating expert advice.
    """
    advice = models.OneToOneField(
        Advice,
        on_delete=models.CASCADE,
        related_name='rating',
        help_text='Advice being rated'
    )
    farmer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='given_ratings',
        help_text='Farmer who gave the rating'
    )
    score = models.IntegerField(
        choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), 
                (4, '4 Stars'), (5, '5 Stars')],
        help_text='Rating score from 1 to 5 stars'
    )
    comment = models.TextField(
        blank=True,
        null=True,
        help_text='Optional comment about the advice'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('advice', 'farmer')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.score}-star rating by {self.farmer.get_full_name()}"


class InventoryItem(models.Model):
    """
    Model for farmer's inventory management.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='inventory_items',
        help_text='Owner of the inventory item'
    )
    name = models.CharField(
        max_length=200,
        help_text='Name of the inventory item'
    )
    quantity = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text='Quantity in stock'
    )
    unit = models.CharField(
        max_length=20, 
        help_text="Unit of measurement (e.g., kg, liters, bags)"
    )
    category = models.CharField(
        max_length=50,
        choices=[
            ('seeds', 'Seeds'),
            ('fertilizers', 'Fertilizers'),
            ('pesticides', 'Pesticides'),
            ('tools', 'Tools'),
            ('other', 'Other'),
        ],
        default='other',
        help_text='Category of the inventory item'
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"{self.name} - {self.quantity} {self.unit}"
