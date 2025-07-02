from django.urls import path
# 기존 views.py import
from . import views
# 모듈화된 views import
from .views_modules.health import health_options, api_health
from . import views_nutrition

urlpatterns = [
    # 기존 API
    path('test/', views.test_api, name='test_api'),
    path('guest/profile/', views.guest_profile, name='guest_profile'),
    path('guest/login/', views.guest_login, name='guest_login'),
    path('auth/csrf/', views.auth_csrf, name='auth_csrf'),
    path('auth/login/', views.auth_login, name='auth_login'),
    path('auth/logout/', views.auth_logout, name='auth_logout'),
    path('auth/register/', views.auth_register, name='auth_register'),
    
    # Health check endpoints
    path('health/', api_health, name='api_health'),  # 모듈화된 함수
    path('health-check/', views.health_check, name='health_check'),
    
    # 건강 선택지 API
    path('health/options/', health_options, name='health_options'),  # 모듈화된 함수
    
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
    path('music/ai-keywords/', views.youtube_music_recommendations, name='music_ai_keywords'),  # 프론트엔드가 기대하는 엔드포인트
    path('music/youtube-search/', views.youtube_search, name='youtube_search'),
    path('music/save-feedback/', views.music_save_feedback, name='music_save_feedback'),  # 피드백 저장
    
    # 🥗 영양 관련 API - 기본 기능
    path('nutrition/analyze/', views.analyze_nutrition, name='analyze_nutrition'),
    path('nutrition/tracking/', views.nutrition_tracking, name='nutrition_tracking'),
    
    # AI 영양 분석 API - views_nutrition.py의 함수들
    path('ai-nutrition/', views_nutrition.ai_nutrition_analysis, name='ai_nutrition_analysis'),
    path('ai-nutrition/analyze/', views_nutrition.ai_nutrition_analysis_only, name='ai_nutrition_analysis_only'),
    path('food-analyses/', views_nutrition.food_analysis_list, name='food_analysis_list'),
    path('food-analyses/<int:pk>/', views_nutrition.food_analysis_detail, name='food_analysis_detail'),
    path('daily-nutrition/', views_nutrition.daily_nutrition_list, name='daily_nutrition_list'),
    path('daily-nutrition/<str:date_str>/', views_nutrition.daily_nutrition_detail, name='daily_nutrition_detail'),
    path('nutrition-statistics/', views_nutrition.nutrition_statistics, name='nutrition_statistics'),
    path('nutrition-complete/', views_nutrition.nutrition_complete, name='nutrition_complete'),
    
    # 👥 소셜 기능 API
    path('social/feed/', views.social_feed, name='social_feed'),
    path('social/posts/<int:post_id>/like/', views.like_post, name='like_post'),
    
    # 🩺 AI 건강 상담 API
    path('health/consultation/', views.health_consultation, name='health_consultation'),
    
    # 🏥 인증된 사용자 엔드포인트 (누락된 것들 추가)
    path('profile/', views.user_profile, name='user_profile'),  # 프로필 API 추가
    path('fitness-profile/', views.fitness_profile, name='fitness_profile'),
    # views.py의 daily_nutrition과 충돌하므로 제거 (views_nutrition.py 것을 사용)
    # path('daily-nutrition/<str:date>/', views.daily_nutrition, name='daily_nutrition'),
    # path('nutrition-statistics/', views.nutrition_statistics, name='nutrition_statistics'),
    path('workout-logs/', views.workout_logs, name='workout_logs'),
    path('workout-logs/create/', views.workout_logs_create, name='workout_logs_create'),
    path('recommendations/daily/', views.recommendations_daily, name='recommendations_daily'),
    
    # 소셜 기능 추가 엔드포인트
    path('social/conversations/unread_count/', views.social_unread_count, name='social_unread_count'),
    path('social/posts/feed/', views.social_posts_feed, name='social_posts_feed'),
    path('social/posts/', views.social_posts_create, name='social_posts_create'),
    path('social/stories/', views.social_stories, name='social_stories'),
    path('user-level/', views.user_level, name='user_level'),
    
    # 채팅봇 엔드포인트
    path('chatbot/', views.chatbot, name='chatbot'),  # 메인 채팅봇 API
    path('chatbot/status/', views.chatbot_status, name='chatbot_status'),
    path('chatbot/sessions/', views.chatbot_sessions, name='chatbot_sessions'),
    path('chatbot/sessions/active/', views.chatbot_sessions_active, name='chatbot_sessions_active'),
    
    # 누락된 소셜 알림 엔드포인트
    path('social/notifications/', views.social_notifications, name='social_notifications'),
    path('social/notifications/unread_count/', views.social_notifications_unread_count, name='social_notifications_unread_count'),
    
    # 누락된 운동 관련 엔드포인트
    path('workout-videos/', views.workout_videos_list, name='workout_videos_list'),
    path('ai-workout/', views.ai_workout, name='ai_workout'),
    
    # AI 기반 추천 엔드포인트
    path('ai/workout-recommendation/', views.ai_workout_recommendation, name='ai_workout_recommendation'),
    path('ai/nutrition-recommendation/', views.ai_nutrition_recommendation, name='ai_nutrition_recommendation'),
    
    # 소셜 피드 추가 엔드포인트
    path('social/posts/popular/', views.social_posts_popular, name='social_posts_popular'),
    path('social/posts/recommended/', views.social_posts_recommended, name='social_posts_recommended'),
]
