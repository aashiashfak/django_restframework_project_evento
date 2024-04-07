# In delete_expired_pending_users.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import PendingUser
import logging
logging.basicConfig(filename='C:/Users/h/Desktop/Project_1/delete_expired_users.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Command(BaseCommand):
    help = 'Deletes expired pending users'

    def handle(self, *args, **options):
       
        current_time = timezone.now()      
        expired_users = PendingUser.objects.filter(expiry_time__lt=current_time)
        num_deleted = expired_users.count()
        expired_users.delete()
        logging.info(f'Deleted {num_deleted} expired pending users.')


        self.stdout.write(self.style.SUCCESS('Expired pending users deleted successfully.'))
