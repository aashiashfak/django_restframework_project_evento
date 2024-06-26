# Generated by Django 5.0.3 on 2024-04-16 06:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0004_alter_vendor_is_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorToken',
            fields=[
                ('key', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('vendor', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='auth_token', to='vendors.vendor')),
            ],
            options={
                'verbose_name': 'Vendor Token',
                'verbose_name_plural': 'Vendor Tokens',
            },
        ),
    ]
