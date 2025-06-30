from django.urls import path, include
from .views import (
    RegisterView, LoginView, LogoutView, UserProfileView,
    ChangePasswordView, health_options, check_email, get_csrf_token,
    ChatbotView, clear_chat_history, chatbot_status, daily_recommendations,
    ChatSessionView
)
from .views_sessions import (
    get_session_messages, get_active_session
)
from .views_profile_image import (
    upload_profile_image, delete_profile_image, get_profile_image
)
from .views_notification import (
    register_fcm_token, notification_settings_view, send_test_notification,
    notification_logs, mark_notification_read
)
from .views_workout import (
    exercise_list, routine_list, routine_detail, ai_workout_recommendation,
    fitness_profile, workout_log_list, workout_log_detail
)
from .views_nutrition import (
    ai_nutrition_analysis, ai_nutrition_analysis_only, food_analysis_list, food_analysis_detail,
    daily_nutrition_list, daily_nutrition_detail, nutrition_statistics, nutrition_complete
)
from .views_achievement import (
    AchievementViewSet, UserGoalViewSet, UserLevelViewSet
)
from apps.social.views import (
    SocialProfileViewSet, SocialFriendRequestViewSet, SocialPostViewSet, SocialCommentViewSet,
    SocialNotificationViewSet
)
from rest_framework.routers import DefaultRouter
from .views.image_proxy import ImageProxyView
from .views_youtube import workout_videos
from .views_guest import (
    guest_token, check_auth_status, guest_recommendations,
    convert_guest_to_member
)
from .views_guest_reset import (
    reset_guest_limits, get_guest_usage_status
)
from .views_auth_test import test_login
from . import views_ai_workout_guest, views_music_guest
from . import views_youtube_guest, views_profile_guest, views_chatbot_guest
from . import views_dashboard_guest

app_name = 'api'

# ViewSet Router 설정
router = DefaultRouter()
router.register(r'achievements', AchievementViewSet, basename='achievement')
router.register(r'user-goals', UserGoalViewSet, basename='user-goal')
router.register(r'user-level', UserLevelViewSet, basename='user-level')
router.register(r'social/profiles', SocialProfileViewSet, basename='social-profile')
router.register(r'social/friend-requests', SocialFriendRequestViewSet, basename='friend-request')
router.register(r'social/posts', SocialPostViewSet, basename='social-post')
router.register(r'social/comments', SocialCommentViewSet, basename='social-comment')
router.register(r'social/notifications', SocialNotificationViewSet, basename='social-notification')

urlpatterns = [
    # 인증 관련
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/check-email/', check_email, name='check_email'),
    path('auth/csrf/', get_csrf_token, name='get_csrf_token'),
    path('auth/status/', check_auth_status, name='check_auth_status'),
    path('auth/test-login/', test_login, name='test_login'),
    
    # 게스트 관련
    path('guest/token/', guest_token, name='guest_token'),
    path('guest/recommendations/', guest_recommendations, name='guest_recommendations'),
    path('guest/convert/', convert_guest_to_member, name='convert_guest'),
    
    # 게스트 제한 리셋 (개발/테스트용)
    path('guest/reset-limits/', reset_guest_limits, name='reset_guest_limits'),
    path('guest/usage-status/', get_guest_usage_status, name='guest_usage_status'),
    
    # 게스트 AI 기능 (제한적)
    path('guest/ai-workout/', views_ai_workout_guest.ai_workout_recommendation_guest, name='ai_workout_guest'),
    path('guest/ai-keywords/', views_music_guest.ai_keywords_guest, name='ai_keywords_guest'),
    path('guest/youtube-search/', views_youtube_guest.youtube_search_guest, name='youtube_search_guest'),
    
    # 게스트 프로필 및 루틴
    path('guest/profile/', views_profile_guest.guest_profile, name='guest_profile'),
    path('guest/routines/', views_profile_guest.guest_routines, name='guest_routines'),
    path('guest/fitness-profile/', views_profile_guest.guest_fitness_profile, name='guest_fitness_profile'),
    
    # 게스트 대시보드
    path('guest/daily-nutrition/<str:date_str>/', views_dashboard_guest.guest_daily_nutrition, name='guest_daily_nutrition'),
    path('guest/nutrition-statistics/', views_dashboard_guest.guest_nutrition_statistics, name='guest_nutrition_statistics'),
    path('guest/workout-logs/', views_dashboard_guest.guest_workout_logs, name='guest_workout_logs'),
    path('guest/recommendations/daily/', views_dashboard_guest.guest_daily_recommendations, name='guest_daily_recommendations'),
    
    # 게스트 챗봇
    path('guest/chatbot/', views_chatbot_guest.guest_chatbot, name='guest_chatbot'),
    path('guest/chatbot/sessions/', views_chatbot_guest.guest_chatbot_sessions, name='guest_chatbot_sessions'),
    path('guest/chatbot/sessions/active/', views_chatbot_guest.guest_chatbot_active_session, name='guest_chatbot_active_session'),
    path('guest/chatbot/status/', views_chatbot_guest.guest_chatbot_status, name='guest_chatbot_status'),
    
    # 사용자 프로필
    path('user/profile/', UserProfileView.as_view(), name='profile'),
    path('user/change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # 프로필 이미지
    path('auth/profile/upload-image/', upload_profile_image, name='upload_profile_image'),
    path('auth/profile/delete-image/', delete_profile_image, name='delete_profile_image'),
    path('auth/profile/image/', get_profile_image, name='get_profile_image'),
    
    # 옵션 데이터
    path('options/health/', health_options, name='health_options'),
    
    # AI 챗봇
    path('chatbot/', ChatbotView.as_view(), name='chatbot'),
    path('chatbot/history/clear/', clear_chat_history, name='clear_chat_history'),
    path('chatbot/status/', chatbot_status, name='chatbot_status'),
    
    # 대화 세션 관리
    path('chatbot/sessions/', ChatSessionView.as_view(), name='chat_sessions'),
    path('chatbot/sessions/<int:session_id>/', ChatSessionView.as_view(), name='chat_session_detail'),
    path('chatbot/sessions/<int:session_id>/messages/', get_session_messages, name='chat_session_messages'),
    path('chatbot/sessions/active/', get_active_session, name='get_active_session'),
    
    # 일일 추천
    path('recommendations/daily/', daily_recommendations, name='daily_recommendations'),
    
    # Map & Music 기능
    path('map/', include('apps.api.map.urls')),
    path('music/', include('apps.api.music.urls')),
    
    # 푸시 알림
    path('notifications/register-token/', register_fcm_token, name='register_fcm_token'),
    path('notifications/settings/', notification_settings_view, name='notification_settings'),
    path('notifications/test/', send_test_notification, name='send_test_notification'),
    path('notifications/logs/', notification_logs, name='notification_logs'),
    path('notifications/mark-read/', mark_notification_read, name='mark_notification_read'),
    
    # 운동 관련
    path('exercises/', exercise_list, name='exercise_list'),
    path('routines/', routine_list, name='routine_list'),
    path('routines/<int:pk>/', routine_detail, name='routine_detail'),
    path('ai-workout/', ai_workout_recommendation, name='ai_workout_recommendation'),
    path('fitness-profile/', fitness_profile, name='fitness_profile'),
    path('workout-logs/', workout_log_list, name='workout_log_list'),
    path('workout-logs/<int:pk>/', workout_log_detail, name='workout_log_detail'),
    
    # 영양 분석 관련
    path('ai-nutrition/', ai_nutrition_analysis, name='ai_nutrition_analysis'),
    path('ai-nutrition/analyze/', ai_nutrition_analysis_only, name='ai_nutrition_analysis_only'),
    path('food-analyses/', food_analysis_list, name='food_analysis_list'),
    path('food-analyses/<int:pk>/', food_analysis_detail, name='food_analysis_detail'),
    path('daily-nutrition/', daily_nutrition_list, name='daily_nutrition_list'),
    path('daily-nutrition/<str:date_str>/', daily_nutrition_detail, name='daily_nutrition_detail'),
    path('nutrition-statistics/', nutrition_statistics, name='nutrition_statistics'),
    path('nutrition-complete/', nutrition_complete, name='nutrition_complete'),
    
    # 운동 영상
    path('workout-videos/', workout_videos, name='workout_videos'),
    
    # 이미지 프록시
    path('proxy/image/', ImageProxyView.as_view(), name='image_proxy'),
    
    # Social 앱 URLs
    path('social/', include('apps.social.urls')),
    
    # 업적 시스템 - ViewSet으로 자동 생성
    path('', include(router.urls)),
]
