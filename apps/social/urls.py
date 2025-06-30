from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.social_views import (
    SocialProfileViewSet,
    SocialPostViewSet,
    SocialCommentViewSet,
    SocialFriendRequestViewSet,
    SocialNotificationViewSet,
    StoryViewSet
)
from .views.dm_views import ConversationViewSet, DirectMessageViewSet

router = DefaultRouter()
router.register(r'profiles', SocialProfileViewSet, basename='profile')
router.register(r'posts', SocialPostViewSet, basename='post')
router.register(r'comments', SocialCommentViewSet, basename='comment')
router.register(r'friend-requests', SocialFriendRequestViewSet, basename='friend-request')
router.register(r'notifications', SocialNotificationViewSet, basename='notification')
router.register(r'stories', StoryViewSet, basename='story')
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', DirectMessageViewSet, basename='message')

app_name = 'social'

urlpatterns = [
    path('', include(router.urls)),
]
