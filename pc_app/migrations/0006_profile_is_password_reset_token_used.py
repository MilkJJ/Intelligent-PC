# Generated by Django 4.2.5 on 2023-10-06 06:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pc_app', '0005_favouritedpc_mboard'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_password_reset_token_used',
            field=models.BooleanField(default='False'),
        ),
    ]
