from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_api, name='test_api'),
    path('guest/profile/', views.guest_profile, name='guest_profile'),
    path('auth/csrf/', views.auth_csrf, name='auth_csrf'),
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('auth/register/', views.auth_register, name='auth_register'),
    
    # Health check endpoint
    path('health/', views.api_health, name='api_health'),
    
    # Guest endpoints
    path('guest/fitness-profile/', views.guest_fitness_profile, name='guest_fitness_profile'),
    path('guest/daily-nutrition/<str:date>/', views.guest_daily_nutrition, name='guest_daily_nutrition'),
    path('guest/nutrition-statistics/', views.guest_nutrition_statistics, name='guest_nutrition_statistics'),
    path('guest/workout-logs/', views.guest_workout_logs, name='guest_workout_logs'),
    path('guest/recommendations/daily/', views.guest_recommendations_daily, name='guest_recommendations_daily'),
]
