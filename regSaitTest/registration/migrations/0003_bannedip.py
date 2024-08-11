# Generated by Django 5.0.7 on 2024-08-11 14:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_customuser_last_password_reset_request'),
    ]

    operations = [
        migrations.CreateModel(
            name='BannedIP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]