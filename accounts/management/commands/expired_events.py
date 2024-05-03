import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event, Ticket

# Configure logging
logging.basicConfig(filename='C:/Users/h/Desktop/Project_1/expired_events.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Command(BaseCommand):
    help = 'Expire events and associated tickets whose end date has passed'

    def handle(self, *args, **kwargs):
        current_date = timezone.now()
        expired_events = Event.objects.exclude(status='completed').filter(end_date__lt=current_date)
        for event in expired_events:
            # Log the name of the expired event
            logging.info(f'Expiring event: {event.event_name}')
            # Update event status to 'expired'
            event.status = 'completed'
            event.save(update_fields=['status'])
            # Update tickets associated with the expired event
            ticket_types = event.ticket_types.all()
            for ticket_type in ticket_types:
                Ticket.objects.filter(ticket_type=ticket_type, ticket_status__in=['active', 'pending']).update(ticket_status='used')
        self.stdout.write(self.style.SUCCESS('Expired events and tickets updated successfully.'))

