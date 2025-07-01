from django.urls import path
from . import views

urlpatterns = [
    # 기존 API
    path('test/', views.test_api, name='test_api'),
    path('guest/profile/', views.guest_profile, name='guest_profile'),
    path('auth/csrf/', views.auth_csrf, name='auth_csrf'),
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('auth/register/', views.auth_register, name='auth_register'),
    
    # Health check endpoint
    path('health/', views.api_health, name='api_health'),
    
    # 건강 선택지 API
    path('health/options/', views.health_options, name='health_options'),
    
    # Guest endpoints
    path('guest/fitness-profile/', views.guest_fitness_profile, name='guest_fitness_profile'),
    path('guest/daily-nutrition/<str:date>/', views.guest_daily_nutrition, name='guest_daily_nutrition'),
    path('guest/nutrition-statistics/', views.guest_nutrition_statistics, name='guest_nutrition_statistics'),
    path('guest/workout-logs/', views.guest_workout_logs, name='guest_workout_logs'),
    path('guest/recommendations/daily/', views.guest_recommendations_daily, name='guest_recommendations_daily'),
    
    # 🏋️ 운동 관련 API
    path('exercises/', views.exercise_list, name='exercise_list'),
    path('routines/', views.workout_routines, name='workout_routines'),
    path('workout/videos/', views.workout_videos, name='workout_videos'),
    
    # 🎵 유튜브 음악 추천 API
    path('youtube/music/', views.youtube_music_recommendations, name='youtube_music'),
    path('music/youtube-search/', views.youtube_search, name='youtube_search'),
    
    # 🥗 영양 관련 API
    path('nutrition/analyze/', views.analyze_nutrition, name='analyze_nutrition'),
    path('nutrition/tracking/', views.nutrition_tracking, name='nutrition_tracking'),
    
    # 👥 소셜 기능 API
    path('social/feed/', views.social_feed, name='social_feed'),
    path('social/posts/<int:post_id>/like/', views.like_post, name='like_post'),
    
    # 🩺 AI 건강 상담 API
    path('health/consultation/', views.health_consultation, name='health_consultation'),
]
