# Generated by Django 4.2.4 on 2023-09-08 03:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pc_app', '0018_alter_cartitem_total_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memory',
            name='price',
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name='motherboard',
            name='price',
            field=models.FloatField(),
        ),
    ]
