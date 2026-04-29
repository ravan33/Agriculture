"""
Management command to clear all active sessions.
This is useful for forcing all users to re-login after server restart.
"""
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Clear all active sessions and force users to re-login'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear all sessions including future ones',
        )
        parser.add_argument(
            '--expired-only',
            action='store_true',
            help='Clear only expired sessions',
        )
    
    def handle(self, *args, **options):
        if options['expired_only']:
            # Clear only expired sessions
            expired_sessions = Session.objects.filter(expire_date__lt=timezone.now())
            count = expired_sessions.count()
            expired_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared {count} expired sessions')
            )
            logger.info(f'Cleared {count} expired sessions')
        
        elif options['all']:
            # Clear all sessions
            count = Session.objects.count()
            Session.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared all {count} sessions')
            )
            logger.info(f'Cleared all {count} sessions')
        
        else:
            # Clear active sessions (default behavior)
            active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
            count = active_sessions.count()
            active_sessions.delete()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully cleared {count} active sessions')
            )
            logger.info(f'Cleared {count} active sessions')
            
        self.stdout.write(
            self.style.WARNING('All affected users will need to log in again')
        )
