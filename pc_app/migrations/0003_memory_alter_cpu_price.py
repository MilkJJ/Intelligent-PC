# Generated by Django 4.2.4 on 2023-08-08 04:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pc_app', '0002_alter_gpu_price'),
    ]

    operations = [
        migrations.CreateModel(
            name='Memory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('ddr_type', models.CharField(max_length=10)),
                ('speed_mhz', models.PositiveIntegerField()),
                ('num_modules', models.PositiveIntegerField()),
                ('memory_size', models.PositiveIntegerField()),
                ('price_per_gb', models.DecimalField(decimal_places=3, max_digits=6)),
                ('color', models.CharField(max_length=50)),
                ('first_word_latency', models.PositiveIntegerField()),
                ('cas_latency', models.PositiveIntegerField()),
            ],
        ),
        migrations.AlterField(
            model_name='cpu',
            name='price',
            field=models.FloatField(),
        ),
    ]
