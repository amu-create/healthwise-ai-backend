# 뷰 모듈 패키지
from .base import (
    test_api, guest_profile, guest_login, guest_fitness_profile,
    guest_workout_logs, guest_recommendations_daily,
    fitness_profile, recommendations_daily, user_level
)
from .auth import (
    auth_csrf, auth_login, auth_logout, auth_register, csrf_failure
)
from .user_profile import user_profile
from .health import (
    health_check, health_options, api_health, 
    health_consultation, chatbot_status, chatbot_sessions,
    chatbot_sessions_active, chatbot
)
from .workout import (
    exercise_list, workout_routines, workout_videos,
    workout_logs, workout_logs_create, workout_videos_list,
    ai_workout_recommendation, ai_workout
)
from .nutrition_summary import (
    guest_daily_nutrition, guest_nutrition_statistics,
    daily_nutrition, nutrition_statistics, nutrition_tracking,
    analyze_nutrition, ai_nutrition_recommendation
)
from .social_endpoints import (
    social_feed, social_posts_feed, social_posts_create,
    social_posts_popular, social_posts_recommended,
    social_stories, social_notifications, social_notifications_unread_count,
    like_post, social_unread_count
)

__all__ = [
    # Base
    'test_api', 'guest_profile', 'guest_login', 'guest_fitness_profile',
    'guest_workout_logs', 'guest_recommendations_daily',
    'fitness_profile', 'recommendations_daily', 'user_level',
    # Auth
    'auth_csrf', 'auth_login', 'auth_logout', 'auth_register', 'csrf_failure',
    # User Profile
    'user_profile',
    # Health
    'health_check', 'health_options', 'api_health', 
    'health_consultation', 'chatbot_status', 'chatbot_sessions',
    'chatbot_sessions_active', 'chatbot',
    # Workout
    'exercise_list', 'workout_routines', 'workout_videos',
    'workout_logs', 'workout_logs_create', 'workout_videos_list',
    'ai_workout_recommendation', 'ai_workout',
    # Nutrition
    'guest_daily_nutrition', 'guest_nutrition_statistics',
    'daily_nutrition', 'nutrition_statistics', 'nutrition_tracking',
    'analyze_nutrition', 'ai_nutrition_recommendation',
    # Social
    'social_feed', 'social_posts_feed', 'social_posts_create',
    'social_posts_popular', 'social_posts_recommended',
    'social_stories', 'social_notifications', 'social_notifications_unread_count',
    'like_post', 'social_unread_count'
]
