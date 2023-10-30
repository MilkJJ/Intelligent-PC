# Generated by Django 4.2.5 on 2023-10-30 01:17

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_price', models.FloatField(default=0.0)),
                ('is_purchased', models.BooleanField(default=False)),
                ('ready_pickup', models.BooleanField(default=False)),
                ('is_completed', models.BooleanField(default=False)),
                ('order_date', models.DateTimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CPU',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Unknown', max_length=200)),
                ('price', models.FloatField()),
                ('core_count', models.PositiveIntegerField(default=0, verbose_name='Core Count')),
                ('core_clock', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Core Clock')),
                ('boost_clock', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Boost Clock')),
                ('tdp', models.PositiveIntegerField(verbose_name='TDP')),
                ('graphics', models.CharField(default='None', max_length=100, verbose_name='Integrated Graphics')),
                ('smt', models.BooleanField(default='False', verbose_name='Multithreading')),
                ('socket', models.CharField(default='Unknown', max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='GPU',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='Unknown', max_length=200)),
                ('price', models.FloatField()),
                ('chipset', models.CharField(max_length=100)),
                ('memory', models.FloatField()),
                ('core_clock', models.BigIntegerField(verbose_name='Core Clock')),
                ('boost_clock', models.BigIntegerField(verbose_name='Boost Clock')),
                ('color', models.CharField(max_length=100)),
                ('length', models.DecimalField(decimal_places=2, max_digits=5)),
            ],
        ),
        migrations.CreateModel(
            name='Memory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('price', models.FloatField()),
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
        migrations.CreateModel(
            name='Motherboard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.FloatField()),
                ('socket', models.CharField(max_length=50)),
                ('form_factor', models.CharField(max_length=50)),
                ('max_memory', models.IntegerField()),
                ('memory_slots', models.IntegerField()),
                ('color', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='PCase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.FloatField()),
                ('type', models.CharField(max_length=50)),
                ('color', models.CharField(max_length=50)),
                ('psu', models.IntegerField()),
                ('side_panel', models.CharField(max_length=100)),
                ('external_525_bays', models.IntegerField()),
                ('internal_35_bays', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='PSU',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.FloatField()),
                ('type', models.CharField(max_length=50)),
                ('efficiency', models.CharField(max_length=50)),
                ('wattage', models.IntegerField()),
                ('modular', models.CharField(max_length=50)),
                ('color', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='StorageDrive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.FloatField()),
                ('capacity', models.IntegerField()),
                ('price_per_gb', models.DecimalField(decimal_places=3, max_digits=10)),
                ('type', models.CharField(max_length=50)),
                ('cache', models.IntegerField(blank=True, null=True)),
                ('form_factor', models.CharField(max_length=50)),
                ('interface', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='StoragePivotTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ratings', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('storage', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.storagedrive')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RecommendedBuild',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_price', models.FloatField(default=0.0)),
                ('cpu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.cpu')),
                ('gpu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.gpu')),
                ('mboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.motherboard')),
            ],
        ),
        migrations.CreateModel(
            name='RAMPivotTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ratings', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('ram', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.memory')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PSUPivotTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ratings', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('psu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.psu')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_picture', models.ImageField(blank=True, null=True, upload_to='profile_pics/')),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True)),
                ('forgot_password_token', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_password_reset_token_used', models.BooleanField(default='False')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PCasePivotTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ratings', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('case', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.pcase')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderRating',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField()),
                ('comment', models.TextField(blank=True, null=True)),
                ('date_added', models.DateTimeField(auto_now_add=True)),
                ('order_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.cartitem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='MotherboardPivotTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ratings', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('mboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.motherboard')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GPUPivotTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ratings', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('gpu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.gpu')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.PositiveIntegerField()),
                ('feedbacks', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FavouritedPC',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total_price', models.FloatField(default=0.0)),
                ('case', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.pcase')),
                ('cpu', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.cpu')),
                ('gpu', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.gpu')),
                ('mboard', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.motherboard')),
                ('psu', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.psu')),
                ('ram', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.memory')),
                ('storage', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.storagedrive')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CPUPivotTable',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ratings', models.DecimalField(decimal_places=0, default=0, max_digits=5)),
                ('cpu', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pc_app.cpu')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='cartitem',
            name='case',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.pcase'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='cpu',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.cpu'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='gpu',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.gpu'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='mboard',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.motherboard'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='order_rating',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='pc_app.orderrating'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='psu',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.psu'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='ram',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.memory'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='storage',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='pc_app.storagedrive'),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
