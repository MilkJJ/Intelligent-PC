# vendor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.vendor_order_list, name='vendor_order_list'),
    path('orders/completed', views.vendor_completed_order, name='vendor_completed_order'),
    path('orders/<int:order_id>/', views.vendor_order_detail, name='vendor_order_detail'),
    path('order/<int:order_id>/mark_completed/', views.mark_completed, name='mark_completed'),
    path('order/<int:order_id>/mark_ready_pickup/', views.mark_ready_pickup, name='mark_ready_pickup'),
    
    path('upload/', views.upload_csv, name='upload_csv'),
]
