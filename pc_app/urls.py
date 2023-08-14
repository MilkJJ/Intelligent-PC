from django.urls import path
from . import views
from .views import CPUListView, GPUListView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.SignupPage, name='signup'),
    path('login/', views.LoginPage, name='login'),
    path('logout/', views.LogoutPage, name='logout'),
    path('home/', views.HomePage, name='home'),
    path('profile/', views.profile, name='profile'),

    path('cpu/', CPUListView.as_view(), name='cpu_list'),
    path('cpu/<int:pk>/', views.cpu_detail, name='cpu_detail'),
    path('cpu/<int:pk1>/<int:pk2>/', views.cpu_comparison, name='cpu_comparison'),

    path('gpu/', GPUListView.as_view(), name='gpu_list'),
    path('gpu/<int:pk>/', views.gpu_detail, name='gpu_detail'),
    path('gpu/<int:pk1>/<int:pk2>/', views.gpu_comparison, name='gpu_comparison'),

    path('upgrade/', views.upgrade, name='upgrade'),

    path('favorited_builds/', views.favorited_builds, name='favorited_builds'),

    path('toggle_favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    path('delete_favorited_build/<int:build_id>/', views.delete_favorited_build, name='delete_favorited_build'),
    
    path('get_cpu_info/<int:cpu_id>/', views.get_cpu_info, name='get_cpu_info'),
    path('get_gpu_info/<int:gpu_id>/', views.get_gpu_info, name='get_gpu_info'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)