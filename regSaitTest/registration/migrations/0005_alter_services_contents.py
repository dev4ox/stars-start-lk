# Generated by Django 5.0.7 on 2024-08-26 17:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_alter_services_contents'),
    ]

    operations = [
        migrations.AlterField(
            model_name='services',
            name='contents',
            field=models.JSONField(default=list),
        ),
    ]