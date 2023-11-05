from django.contrib import admin
from .models import *
# Register your models here.

@admin.register(CPU)
@admin.register(InitialRec)
@admin.register(CartItem)
@admin.register(Profile)
class YourModelAdmin(admin.ModelAdmin):
    search_fields = ['id']

