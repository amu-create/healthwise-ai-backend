from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_api, name='test_api'),
    path('guest/profile/', views.guest_profile, name='guest_profile'),
    path('auth/csrf/', views.auth_csrf, name='auth_csrf'),
]