# Generated by Django 5.0.3 on 2024-04-21 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0002_alter_event_event_img_1_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='status',
            field=models.CharField(choices=[('active', 'Active'), ('completed', 'Completed'), ('disabled', 'Disabled')], default='active', max_length=20),
        ),
        migrations.AddField(
            model_name='event',
            name='time',
            field=models.TimeField(default='17:00'),
        ),
    ]
