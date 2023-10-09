# vendor/models.py
from django.db import models
from django.contrib.auth.models import User
from pc_app.models import CartItem

    # Add more fields as needed
# class Vendor(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)

#     def __str__(self):
#         return self.user.username
#     # Add vendor-specific fields, such as company name, contact info, etc.

# class VendorProduct(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
#     # Add fields for product details, e.g., name, price, description, etc.

# class VendorOrder(models.Model):
#     vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
#     cart_item = models.ForeignKey(CartItem, on_delete=models.CASCADE)
#     # Add fields for order details, e.g., order status, order date, etc.
