from celery import shared_task
from .management.commands import expired_events  
import logging

log_file_path = 'C:/Users/h/Desktop/Project_1/celery_task_logs.log'
logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

@shared_task
def expire_events_task():
    logging.info("Task execution started.")
    try:
        print('executed')
        expired_events.Command().handle()
    except Exception as e:
        # Log the error or handle it appropriately
        print(f"An error occurred: {e}")



# from celery import shared_task
# import logging
# from django.utils import timezone
# from events.models import Event, Ticket

# # Configure logging
# log_file_path = 'C:/Users/h/Desktop/Project_1/expired_events.log'
# logging.basicConfig(filename=log_file_path, level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# @shared_task
# def expire_events_task():
#     print('hai')
#     current_date = timezone.now()
#     expired_events = Event.objects.exclude(status='completed').filter(end_date__lt=current_date)
#     for event in expired_events:
#         # Log the name of the expired event
#         logging.info(f'Expiring event: {event.event_name}')
#         # Update event status to 'expired'
#         event.status = 'completed'
#         event.save(update_fields=['status'])
#         # Update tickets associated with the expired event
#         ticket_types = event.ticket_types.all()
#         for ticket_type in ticket_types:
#             Ticket.objects.filter(ticket_type=ticket_type, ticket_status__in=['active', 'pending']).update(ticket_status='used')

#     logging.info('Expired events and tickets updated successfully.')