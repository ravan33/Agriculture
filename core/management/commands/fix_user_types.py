from django.core.management.base import BaseCommand
from django.db import models
from core.models import User

class Command(BaseCommand):
    help = 'Fix user types for existing users'

    def handle(self, *args, **options):
        self.stdout.write('Fixing user types...')
        
        # Fix admin users
        admin_users = User.objects.filter(
            models.Q(is_superuser=True) | models.Q(is_staff=True)
        ).exclude(user_type='admin')
        
        admin_count = admin_users.count()
        admin_users.update(user_type='admin')
        
        self.stdout.write(
            self.style.SUCCESS(f'Updated {admin_count} users to admin type')
        )
        
        # Show current user type distribution
        self.stdout.write('\nCurrent user type distribution:')
        for user_type, display_name in User.USER_TYPE_CHOICES:
            count = User.objects.filter(user_type=user_type).count()
            self.stdout.write(f'  {display_name}: {count} users')
        
        self.stdout.write(
            self.style.SUCCESS('User types have been fixed successfully!')
        )
