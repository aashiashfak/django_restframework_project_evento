# Generated by Django 5.0.3 on 2024-04-21 11:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0004_delete_ticket'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('ticket_count', models.PositiveIntegerField(default=1)),
                ('qr_code', models.ImageField(blank=True, null=True, upload_to='qr_codes/')),
                ('booking_date', models.DateTimeField(auto_now_add=True)),
                ('ticket_status', models.CharField(choices=[('active', 'Active'), ('canceled', 'Canceled'), ('used', 'Used')], default='active', max_length=10)),
                ('ticket_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to='events.tickettype')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tickets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
