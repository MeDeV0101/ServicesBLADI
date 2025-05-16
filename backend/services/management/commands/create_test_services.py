from django.core.management.base import BaseCommand
from services.models import ServiceCategory, ServiceType, Service

class Command(BaseCommand):
    help = 'Create test services for each category'

    def handle(self, *args, **options):
        # Get all service categories
        categories = ServiceCategory.objects.all()
        self.stdout.write(f"Found {len(categories)} categories")

        # Create services for each category
        for cat in categories:
            # Create or get a service type for this category
            service_type, created = ServiceType.objects.get_or_create(
                category=cat,
                name=f'{cat.name} Services',
                defaults={
                    'description': f'Service types for {cat.name} category',
                    'price': 100.0
                }
            )
            
            # Create or get a service for this service type
            service, created = Service.objects.get_or_create(
                service_type=service_type,
                title=f'{cat.name} Basic Service',
                defaults={
                    'description': f'Basic service for {cat.name} category',
                    'price': 100.0,
                    'is_active': True,
                    'status': 'active'
                }
            )
            
            if created:
                self.stdout.write(f'Created new service for {cat.name}')
            else:
                # Make sure the service is active
                if not service.is_active:
                    service.is_active = True
                    service.save()
                    self.stdout.write(f'Activated existing service for {cat.name}')
                else:
                    self.stdout.write(f'Service for {cat.name} already exists and is active')

        # Verify active services
        active_services = Service.objects.filter(is_active=True)
        self.stdout.write(f"Total active services: {len(active_services)}")
        for service in active_services:
            self.stdout.write(f"ID: {service.id}, Title: {service.title}, Category: {service.service_type.category.name}")
