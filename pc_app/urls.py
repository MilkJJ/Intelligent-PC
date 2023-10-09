from django.urls import path
from . import views_recommend, views_upgrade, views
from .views import *
from .context_processors import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Homepage / Recommendation
    path('home/', views_recommend.HomePage, name='home'),

    # User Authentication Page
    path('', views.SignupPage, name='signup'),
    path('login/', views.LoginPage, name='login'),
    path('logout/', views.LogoutPage, name='logout'),

    # Profile
    path('update-profile-picture/', views.update_profile_picture, name='update_profile_picture'),
    path('profile/', views.profile, name='change_password'),

    path('forgot-password/', views.ForgotPassword, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),

    # Component Displays
    path('cpu/', CPUListView.as_view(), name='cpu_list'),
    path('cpu/<int:pk>/', views.cpu_detail, name='cpu_detail'),
    path('cpu/<int:pk1>/<int:pk2>/', views.cpu_comparison, name='cpu_comparison'),

    path('gpu/', GPUListView.as_view(), name='gpu_list'),
    path('gpu/<int:pk>/', views.gpu_detail, name='gpu_detail'),
    path('gpu/<int:pk1>/<int:pk2>/', views.gpu_comparison, name='gpu_comparison'),

    path('mboard/', MBoardListView.as_view(), name='mboard_list'),
    path('mboard/<int:pk>/', views.mboard_detail, name='mboard_detail'),
    path('mboard/<int:pk1>/<int:pk2>/', views.mboard_comparison, name='mboard_comparison'),

    #Upgrade
    path('upgrade/', views_upgrade.upgrade, name='upgrade'),

    # Order Build
    path('completed_order/', views.completed_order_view, name='completed_order'),
    path('ongoing_order/', views.ongoing_order_view, name='ongoing_order'),
    path('checkout/', views.checkout, name='checkout'),
    path('place_order/', views.place_order, name='place_order'),

    # Order Ratings
    path('rate-order/<int:item_id>/', views.rate_order, name='rate_order'),
    path('item/<int:item_id>/', views.rating_detail, name='item_detail'),

    # Favourite build
    path('toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('favorited_builds/', views.favorited_builds, name='favorited_builds'),
    path('delete_favorited_build/<int:build_id>/', views.delete_favorited_build, name='delete_favorited_build'),

    # Add to cart
    path('cart_items/', views.cart_items, name='cart_items'),
    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('add_to_cart/<int:build_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Get Component Info for Build Customization
    path('get_cpu_info/<int:cpu_id>/', views.get_cpu_info, name='get_cpu_info'),
    path('get_gpu_info/<int:gpu_id>/', views.get_gpu_info, name='get_gpu_info'),
    path('get_mboard_info/<int:mboard_id>/', views.get_mboard_info, name='get_mboard_info'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)