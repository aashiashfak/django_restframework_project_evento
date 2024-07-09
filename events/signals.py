from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from .models import Event
from accounts.models import CustomUser


@receiver(post_save, sender=Event)
def send_event_notification(sender, instance, created, **kwargs):
    if created:
        vendor = instance.vendor.vendor_details
        print('vendor........', vendor)
        followers = CustomUser.objects.filter(following__vendor=vendor)
        print('followers........', followers)

        # Prepare email details
        subject = f"New Event: {instance.event_name}"
        event_url = f"{settings.SITE_URL}event-details/{instance.id}/"
        event_image_url = instance.event_img_1
        context = {
            'event': instance,
            'vendor': vendor,
            'event_url': event_url,
            'event_image_url': event_image_url,
            'current_year': datetime.now().year,
        }

        # Render HTML template
        html_message = render_to_string('event_notification.html', context)

        recipient_list = [user.email for user in followers]

        # Send email
        email = EmailMessage(
            subject,
            html_message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list
        )
        email.content_subtype = "html"  
        email.send()
