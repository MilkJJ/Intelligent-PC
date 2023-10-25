# Generated by Django 4.2.5 on 2023-10-20 11:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pc_app', '0009_cartitem_case_cartitem_psu_cartitem_ram_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cpupivottable',
            name='ratings',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='gpupivottable',
            name='ratings',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='motherboardpivottable',
            name='ratings',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='pcasepivottable',
            name='ratings',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='psupivottable',
            name='ratings',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='rampivottable',
            name='ratings',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='storagepivottable',
            name='ratings',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=5),
        ),
    ]
