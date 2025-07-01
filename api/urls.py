from django.urls import path
from . import views

urlpatterns = [
    # 기존 API
    path('test/', views.test_api, name='test_api'),
    path('guest/profile/', views.guest_profile, name='guest_profile'),
    path('guest/login/', views.guest_login, name='guest_login'),
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
    
    # 🏥 인증된 사용자 엔드포인트 (누락된 것들 추가)
    path('fitness-profile/', views.fitness_profile, name='fitness_profile'),
    path('daily-nutrition/<str:date>/', views.daily_nutrition, name='daily_nutrition'),
    path('nutrition-statistics/', views.nutrition_statistics, name='nutrition_statistics'),
    path('workout-logs/', views.workout_logs, name='workout_logs'),
    path('recommendations/daily/', views.recommendations_daily, name='recommendations_daily'),
    
    # 소셜 기능 추가 엔드포인트
    path('social/conversations/unread_count/', views.social_unread_count, name='social_unread_count'),
    path('social/posts/feed/', views.social_posts_feed, name='social_posts_feed'),
    path('social/stories/', views.social_stories, name='social_stories'),
    path('user-level/', views.user_level, name='user_level'),
    
    # 채팅봇 엔드포인트
    path('chatbot/', views.chatbot, name='chatbot'),  # 메인 채팅봇 API
    path('chatbot/status/', views.chatbot_status, name='chatbot_status'),
    path('chatbot/sessions/', views.chatbot_sessions, name='chatbot_sessions'),
    path('chatbot/sessions/active/', views.chatbot_sessions_active, name='chatbot_sessions_active'),
    
    # 누락된 소셜 알림 엔드포인트
    path('social/notifications/unread_count/', views.social_notifications_unread_count, name='social_notifications_unread_count'),
    
    # AI 기반 추천 엔드포인트
    path('ai/workout-recommendation/', views.ai_workout_recommendation, name='ai_workout_recommendation'),
    path('ai/nutrition-recommendation/', views.ai_nutrition_recommendation, name='ai_nutrition_recommendation'),
]
