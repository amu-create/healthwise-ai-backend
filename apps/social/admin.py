from django.contrib import admin
from .models import SocialProfile, SocialPost, SocialComment, SocialFriendRequest, SocialNotification


@admin.register(SocialProfile)
class SocialProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_posts', 'total_workouts', 'created_at']
    list_filter = ['is_private', 'created_at']
    search_fields = ['user__username', 'bio']
    filter_horizontal = ['followers']


@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'visibility', 'exercise_name', 'created_at']
    list_filter = ['visibility', 'media_type', 'created_at']
    search_fields = ['user__username', 'content', 'exercise_name']
    filter_horizontal = ['likes']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SocialComment)
class SocialCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(SocialFriendRequest)
class SocialFriendRequestAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['from_user__username', 'to_user__username']


@admin.register(SocialNotification)
class SocialNotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'type', 'title', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'title', 'message']
