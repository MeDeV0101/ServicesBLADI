from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Test email configuration'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address to send test to')

    def handle(self, *args, **options):
        test_email = options['email'] or settings.EMAIL_HOST_USER
        
        try:
            self.stdout.write(f"Attempting to send test email to {test_email}...")
            
            send_mail(
                subject='Test Email from ServiceBladi',
                message='This is a test email to verify your email configuration.',
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[test_email],
                fail_silently=False,
            )
            
            self.stdout.write(self.style.SUCCESS(f"Successfully sent test email to {test_email}"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send test email: {str(e)}"))
            logger.error(f"Email test failed: {str(e)}") 