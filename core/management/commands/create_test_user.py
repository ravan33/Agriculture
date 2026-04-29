from django.core.management.base import BaseCommand
from core.models import User

class Command(BaseCommand):
    help = 'Create a test farmer and expert user (active) for dashboard testing.'

    def handle(self, *args, **options):
        # Create test farmer
        farmer, created = User.objects.get_or_create(
            username='testfarmer',
            defaults={
                'email': 'testfarmer@example.com',
                'user_type': 'farmer',
                'is_active': True,
            }
        )
        if created:
            farmer.set_password('testpass123')
            farmer.save()
            self.stdout.write(self.style.SUCCESS('Created test farmer user.'))
        else:
            self.stdout.write('Test farmer user already exists.')

        # Create test expert
        expert, created = User.objects.get_or_create(
            username='testexpert',
            defaults={
                'email': 'testexpert@example.com',
                'user_type': 'expert',
                'is_active': True,
            }
        )
        if created:
            expert.set_password('testpass123')
            expert.save()
            self.stdout.write(self.style.SUCCESS('Created test expert user.'))
        else:
            self.stdout.write('Test expert user already exists.')

        self.stdout.write(self.style.SUCCESS('Test users are ready for dashboard and login testing.'))
