# Generated by Django 5.0.3 on 2024-04-19 06:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_remove_customuser_vendor_id_remove_vendor_is_active_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vendor_details', to=settings.AUTH_USER_MODEL),
        ),
    ]
