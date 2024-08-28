# Generated by Django 5.0.3 on 2024-08-19 08:54

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0010_event_location_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='payment',
            name='ticket',
        ),
        migrations.AddField(
            model_name='payment',
            name='ticket_type',
            field=models.ForeignKey(default=0, on_delete=django.db.models.deletion.CASCADE, to='events.tickettype'),
        ),
    ]
