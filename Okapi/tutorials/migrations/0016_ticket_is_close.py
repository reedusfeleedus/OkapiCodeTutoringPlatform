# Generated by Django 5.1.2 on 2024-12-18 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tutorials', '0015_ticket_date_ticket_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='is_close',
            field=models.BooleanField(default=False),
        ),
    ]
