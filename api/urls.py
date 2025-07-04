from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import views_nutrition
from . import views_auth
from .views_modules.nutrition_summary import nutrition_summary
from .views_modules.workout_db import workout_logs_db, workout_logs_create_db
from .views_modules.social_endpoints import (
    social_notifications, social_notifications_unread_count,
    social_posts_feed, social_posts_create, social_posts_popular,
    social_posts_recommended, social_stories, social_unread_count,
    social_conversations_unread_count, mark_all_notifications_as_read,
    upload_profile_image, like_post
)

# DRF Router for ViewSets
router = DefaultRouter()

urlpatterns = [
    # 인증 관련 API (JWT 기반)
    path('auth/register/', views_auth.register, name='auth_register'),
    path('auth/login/', views_auth.login, name='auth_login'),
    path('auth/logout/', views_auth.logout, name='auth_logout'),
    path('auth/user/', views_auth.get_user, name='auth_user'),
    path('auth/user/update/', views_auth.update_user, name='auth_user_update'),
    path('auth/refresh/', views_auth.refresh_token, name='auth_refresh'),
    path('auth/guest/', views_auth.guest_login, name='auth_guest'),
    
    # 기존 엔드포인트 유지 (하위 호환성)
    path('test/', views.test_api, name='test_api'),
    path('guest/profile/', views.guest_profile, name='guest_profile'),
    path('auth/csrf/', views.auth_csrf, name='auth_csrf'),
    
    # Health check endpoints
    path('health/', views.api_health, name='api_health'),
    path('health-check/', views.health_check, name='health_check'),
    
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
    path('music/ai-keywords/', views.youtube_music_recommendations, name='music_ai_keywords'),
    path('music/youtube-search/', views.youtube_search, name='youtube_search'),
    path('music/save-feedback/', views.music_save_feedback, name='music_save_feedback'),
    
    # 🥗 영양 관련 API - 기본 기능
    path('nutrition/analyze/', views.analyze_nutrition, name='analyze_nutrition'),
    path('nutrition/tracking/', views.nutrition_tracking, name='nutrition_tracking'),
    path('nutrition-summary/<str:date_str>/', nutrition_summary, name='nutrition_summary'),
    
    # AI 영양 분석 API - views_nutrition.py의 함수들
    path('ai-nutrition/', views_nutrition.ai_nutrition_analysis, name='ai_nutrition_analysis'),
    path('ai-nutrition/analyze/', views_nutrition.ai_nutrition_analysis_only, name='ai_nutrition_analysis_only'),
    path('food-analyses/', views_nutrition.food_analysis_list, name='food_analysis_list'),
    path('food-analyses/<int:pk>/', views_nutrition.food_analysis_detail, name='food_analysis_detail'),
    path('daily-nutrition/', views_nutrition.daily_nutrition_list, name='daily_nutrition_list'),
    path('daily-nutrition/<str:date_str>/', views_nutrition.daily_nutrition_detail, name='daily_nutrition_detail'),
    path('nutrition-statistics/', views_nutrition.nutrition_statistics, name='nutrition_statistics'),
    path('nutrition-complete/', views_nutrition.nutrition_complete, name='nutrition_complete'),
    
    # 👥 소셜 기능 API - 모듈화된 엔드포인트
    path('social/feed/', views.social_feed, name='social_feed'),
    path('social/posts/<int:post_id>/like/', like_post, name='like_post'),
    path('social/posts/feed/', social_posts_feed, name='social_posts_feed'),
    path('social/posts/', social_posts_create, name='social_posts_create'),
    path('social/posts/popular/', social_posts_popular, name='social_posts_popular'),
    path('social/posts/recommended/', social_posts_recommended, name='social_posts_recommended'),
    path('social/stories/', social_stories, name='social_stories'),
    path('social/notifications/', social_notifications, name='social_notifications'),
    path('social/notifications/unread_count/', social_notifications_unread_count, name='social_notifications_unread_count'),
    path('social/notifications/mark_all_as_read/', mark_all_notifications_as_read, name='mark_all_notifications_as_read'),
    path('social/conversations/unread_count/', social_conversations_unread_count, name='social_conversations_unread_count'),
    path('social/unread_count/', social_unread_count, name='social_unread_count'),
    path('auth/profile/upload-image/', upload_profile_image, name='upload_profile_image'),
    
    # 🩺 AI 건강 상담 API
    path('health/consultation/', views.health_consultation, name='health_consultation'),
    
    # 🏥 인증된 사용자 엔드포인트
    path('profile/', views.user_profile, name='user_profile'),
    path('fitness-profile/', views.fitness_profile, name='fitness_profile'),
    path('workout-logs/', workout_logs_db, name='workout_logs_db'),  # 🔥 DB 연동 API (GET)
    path('workout-logs/create/', workout_logs_create_db, name='workout_logs_create_db'),  # 🔥 DB 연동 API (POST)
    path('workout-logs/legacy/', views.workout_logs, name='workout_logs_legacy'),  # 기존 API 백업
    path('recommendations/daily/', views.recommendations_daily, name='recommendations_daily'),
    
    # 레벨 시스템
    path('user-level/', views.user_level, name='user_level'),
    
    # 채팅봇 엔드포인트
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/status/', views.chatbot_status, name='chatbot_status'),
    path('chatbot/sessions/', views.chatbot_sessions, name='chatbot_sessions'),
    path('chatbot/sessions/active/', views.chatbot_sessions_active, name='chatbot_sessions_active'),
    
    # 운동 관련 추가 엔드포인트
    path('workout-videos/', views.workout_videos_list, name='workout_videos_list'),
    path('ai-workout/', views.ai_workout, name='ai_workout'),
    
    # AI 기반 추천 엔드포인트
    path('ai/workout-recommendation/', views.ai_workout_recommendation, name='ai_workout_recommendation'),
    path('ai/nutrition-recommendation/', views.ai_nutrition_recommendation, name='ai_nutrition_recommendation'),
    
    # Router URLs
    path('', include(router.urls)),
]
