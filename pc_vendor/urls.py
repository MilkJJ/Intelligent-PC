# vendor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('orders/', views.vendor_order_list, name='vendor_order_list'),
    path('orders/<int:order_id>/', views.vendor_order_detail, name='vendor_order_detail'),
    path('order/<int:order_id>/mark_shipped/', views.mark_shipped, name='mark_shipped'),

    path('upload/', views.upload_csv, name='upload_csv'),
    path('success/', views.success_page, name='success_page'),
]
