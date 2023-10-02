from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    forgot_password_token = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    # Add other profile-related fields here

    def __str__(self) -> str:
        return self.user.email

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

#, db_column='Cores'
#price = models.FloatField(verbose_name='Price', db_column='Price')
# models.DecimalField(decimal_places=2, max_digits=8)

class CPU(models.Model):
    name = models.CharField(max_length=200, default='Unknown')
    price = models.FloatField()
    core_count = models.PositiveIntegerField(verbose_name='Core Count', default=0)
    core_clock = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Core Clock')
    boost_clock = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Boost Clock')
    tdp = models.PositiveIntegerField(verbose_name='TDP')
    graphics = models.CharField(max_length=100, verbose_name='Integrated Graphics', default='None')
    smt = models.BooleanField(verbose_name='Multithreading', default='False')
    socket = models.CharField(max_length=200, default='Unknown')
    
    def __str__(self):
        return f"{self.name} - {self.graphics} @ {self.core_clock}GHz"


class GPU(models.Model):
    name = models.CharField(max_length=200, default='Unknown')
    price = models.FloatField()
    chipset = models.CharField(max_length=100)
    memory = models.FloatField()
    core_clock = models.BigIntegerField(verbose_name='Core Clock')
    boost_clock = models.BigIntegerField( verbose_name='Boost Clock')
    color = models.CharField(max_length=100)
    length = models.DecimalField(decimal_places=2, max_digits=5)

    def __str__(self):
        return f"{self.name} - {self.chipset} - {self.memory}GB"


class Memory(models.Model):
    name = models.CharField(max_length=200)
    price = models.FloatField()
    ddr_type = models.CharField(max_length=10)  # For example, "DDR4"
    speed_mhz = models.PositiveIntegerField()  # MHz speed
    num_modules = models.PositiveIntegerField()  # Number of memory modules
    memory_size = models.PositiveIntegerField()  # Memory size in GB
    price_per_gb = models.DecimalField(max_digits=6, decimal_places=3)
    color = models.CharField(max_length=50)
    first_word_latency = models.PositiveIntegerField()
    cas_latency = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.memory_size}GB + {self.speed_mhz}Mhz)"

class Motherboard(models.Model):
    name = models.CharField(max_length=255)
    price = models.FloatField()
    socket = models.CharField(max_length=50)
    form_factor = models.CharField(max_length=50)
    max_memory = models.IntegerField()
    memory_slots = models.IntegerField()
    color = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class PSU(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=50)
    efficiency = models.CharField(max_length=50)
    wattage = models.IntegerField()
    modular = models.CharField(max_length=50)
    color = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    

class StorageDrive(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    capacity = models.IntegerField()
    price_per_gb = models.DecimalField(max_digits=10, decimal_places=3)
    type = models.CharField(max_length=50)
    cache = models.IntegerField(blank=True, null=True)
    form_factor = models.CharField(max_length=50)
    interface = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class PCase(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=50)
    color = models.CharField(max_length=50)
    psu = models.IntegerField()
    side_panel = models.CharField(max_length=100)
    external_525_bays = models.IntegerField()
    internal_35_bays = models.IntegerField()

    def __str__(self):
        return self.name


class FavouritedPC(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cpu = models.ForeignKey(CPU, on_delete=models.CASCADE)
    gpu = models.ForeignKey(GPU, on_delete=models.CASCADE)
    total_price = models.FloatField(default=0.0)
    # Add other fields as needed

    def __str__(self):
        return f"Favourited PC {self.id} - {self.user.username}"
    
class OrderRating(models.Model):
    order_item = models.ForeignKey('CartItem', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    comment = models.TextField(blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating for Order Item: {self.order_item.id}"

class CartItem(models.Model):
    cpu = models.ForeignKey(CPU, on_delete=models.CASCADE, null=True)
    gpu = models.ForeignKey(GPU, on_delete=models.CASCADE, null=True)
    total_price = models.FloatField(default=0.0)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_purchased = models.BooleanField(default=False)
    ready_pickup = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    order_date = models.DateTimeField(null=True, blank=True)  # Add this field
    order_rating = models.OneToOneField(OrderRating, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        return f"Order {self.id}"  # You can customize the string representation

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    feedbacks = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
