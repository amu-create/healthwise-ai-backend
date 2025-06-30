from rest_framework import serializers
from apps.core.models import NotificationSettings, NotificationLog


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """알림 설정 시리얼라이저"""
    reminder_days_list = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationSettings
        fields = [
            'id',
            'fcm_token',
            'fcm_token_updated_at',
            'enable_workout_reminders',
            'enable_goal_achievement_notif',
            'enable_social_activity_notif',
            'enable_weekly_summary',
            'reminder_time',
            'reminder_days',
            'reminder_days_list',
            'quiet_hours_start',
            'quiet_hours_end',
            'notification_language',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'fcm_token_updated_at', 'created_at', 'updated_at']
    
    def get_reminder_days_list(self, obj):
        """알림 요일을 리스트로 반환"""
        return obj.get_reminder_days_list()
    
    def validate_reminder_days(self, value):
        """알림 요일 유효성 검사"""
        try:
            days = [int(day) for day in value.split(',')]
            if not all(0 <= day <= 6 for day in days):
                raise serializers.ValidationError("요일은 0-6 사이의 값이어야 합니다.")
            return value
        except ValueError:
            raise serializers.ValidationError("잘못된 요일 형식입니다.")


class NotificationLogSerializer(serializers.ModelSerializer):
    """알림 로그 시리얼라이저"""
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', 
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', 
        read_only=True
    )
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'username',
            'notification_type',
            'notification_type_display',
            'title',
            'body',
            'status',
            'status_display',
            'error_message',
            'fcm_message_id',
            'fcm_response',
            'data',
            'created_at',
            'sent_at'
        ]
        read_only_fields = [
            'id', 'username', 'notification_type_display', 
            'status_display', 'created_at'
        ]


class SendNotificationSerializer(serializers.Serializer):
    """알림 전송 시리얼라이저"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="알림을 받을 사용자 ID 리스트"
    )
    notification_type = serializers.ChoiceField(
        choices=NotificationLog.NOTIFICATION_TYPES,
        required=True
    )
    title = serializers.CharField(max_length=200, required=True)
    body = serializers.CharField(required=True)
    data = serializers.JSONField(required=False, default=dict)
    send_to_all = serializers.BooleanField(
        default=False,
        help_text="모든 사용자에게 전송"
    )
    
    def validate(self, attrs):
        """유효성 검사"""
        if not attrs.get('send_to_all') and not attrs.get('user_ids'):
            raise serializers.ValidationError(
                "user_ids 또는 send_to_all 중 하나는 필수입니다."
            )
        return attrs


class BulkNotificationSerializer(serializers.Serializer):
    """대량 알림 전송 시리얼라이저"""
    topic = serializers.CharField(
        required=False,
        help_text="토픽 이름 (all_users, workout_reminders 등)"
    )
    filters = serializers.JSONField(
        required=False,
        default=dict,
        help_text="사용자 필터 조건"
    )
    title = serializers.CharField(max_length=200, required=True)
    body = serializers.CharField(required=True)
    data = serializers.JSONField(required=False, default=dict)
    scheduled_time = serializers.DateTimeField(
        required=False,
        help_text="예약 전송 시간"
    )
