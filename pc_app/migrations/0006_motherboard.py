# Generated by Django 4.2.4 on 2023-08-08 04:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pc_app', '0005_alter_memory_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Motherboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('socket', models.CharField(max_length=50)),
                ('form_factor', models.CharField(max_length=50)),
                ('max_memory', models.IntegerField()),
                ('memory_slots', models.IntegerField()),
                ('color', models.CharField(max_length=50)),
            ],
        ),
    ]
