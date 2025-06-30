from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

from apps.core.models import (
    NotificationSettings, NotificationLog, UserProfile,
    WorkoutLog, User, ChatMessage
)
from apps.core.firebase_utils import (
    send_notification, send_multicast_notification,
    subscribe_to_topic, unsubscribe_from_topic
)
from apps.api.serializers_notification import (
    NotificationSettingsSerializer, NotificationLogSerializer
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_fcm_token(request):
    """FCM 토큰 등록/업데이트"""
    fcm_token = request.data.get('fcm_token')
    
    if not fcm_token:
        return Response(
            {'error': 'FCM 토큰이 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # NotificationSettings 가져오거나 생성
    settings, created = NotificationSettings.objects.get_or_create(
        user=request.user
    )
    
    # FCM 토큰 업데이트
    settings.fcm_token = fcm_token
    settings.fcm_token_updated_at = timezone.now()
    settings.save()
    
    # 기본 토픽 구독
    topics = ['all_users']
    if settings.enable_workout_reminders:
        topics.append('workout_reminders')
    if settings.enable_goal_achievement_notif:
        topics.append('goal_achievements')
    
    for topic in topics:
        subscribe_to_topic([fcm_token], topic)
    
    return Response({
        'message': 'FCM 토큰이 성공적으로 등록되었습니다.',
        'settings': NotificationSettingsSerializer(settings).data
    })


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def notification_settings_view(request):
    """알림 설정 조회/수정"""
    settings, created = NotificationSettings.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'GET':
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = NotificationSettingsSerializer(
            settings, data=request.data, partial=True
        )
        
        if serializer.is_valid():
            # 토픽 구독 상태 업데이트
            fcm_token = settings.fcm_token
            if fcm_token:
                # 운동 알림
                if 'enable_workout_reminders' in request.data:
                    if request.data['enable_workout_reminders']:
                        subscribe_to_topic([fcm_token], 'workout_reminders')
                    else:
                        unsubscribe_from_topic([fcm_token], 'workout_reminders')
                
                # 목표 달성 알림
                if 'enable_goal_achievement_notif' in request.data:
                    if request.data['enable_goal_achievement_notif']:
                        subscribe_to_topic([fcm_token], 'goal_achievements')
                    else:
                        unsubscribe_from_topic([fcm_token], 'goal_achievements')
            
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_test_notification(request):
    """테스트 알림 전송"""
    settings = NotificationSettings.objects.filter(user=request.user).first()
    
    if not settings or not settings.fcm_token:
        return Response(
            {'error': 'FCM 토큰이 등록되지 않았습니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 테스트 알림 전송
    title = "HealthWise 테스트 알림"
    body = "알림이 정상적으로 작동합니다! 🎉"
    data = {
        'type': 'test',
        'timestamp': timezone.now().isoformat()
    }
    
    message_id = send_notification(
        settings.fcm_token,
        title,
        body,
        data
    )
    
    # 알림 로그 생성
    log = NotificationLog.objects.create(
        user=request.user,
        notification_type='workout_reminder',  # 테스트용
        title=title,
        body=body,
        status='sent' if message_id else 'failed',
        fcm_message_id=message_id,
        data=data,
        sent_at=timezone.now() if message_id else None
    )
    
    if message_id:
        return Response({
            'message': '테스트 알림이 전송되었습니다.',
            'message_id': message_id
        })
    else:
        return Response(
            {'error': '알림 전송에 실패했습니다.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_logs(request):
    """알림 기록 조회"""
    # 쿼리 파라미터
    notification_type = request.GET.get('type')
    status_filter = request.GET.get('status')
    days = int(request.GET.get('days', 30))
    
    # 날짜 필터
    start_date = timezone.now() - timedelta(days=days)
    
    # 쿼리셋 생성
    queryset = NotificationLog.objects.filter(
        user=request.user,
        created_at__gte=start_date
    )
    
    # 필터 적용
    if notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # 정렬
    queryset = queryset.order_by('-created_at')
    
    # 페이지네이션
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    logs = queryset[start:end]
    total_count = queryset.count()
    
    serializer = NotificationLogSerializer(logs, many=True)
    
    return Response({
        'results': serializer.data,
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size
    })


def send_workout_reminder(user):
    """운동 알림 전송"""
    settings = NotificationSettings.objects.filter(user=user).first()
    
    if not settings or not settings.fcm_token or not settings.enable_workout_reminders:
        return None
    
    # 현재 시간과 요일 확인
    now = timezone.now()
    current_day = now.weekday()  # 0=월요일, 6=일요일
    
    # 알림 받을 요일인지 확인
    reminder_days = settings.get_reminder_days_list()
    if current_day not in reminder_days:
        return None
    
    # 조용한 시간인지 확인
    current_time = now.time()
    if settings.quiet_hours_start <= current_time or current_time <= settings.quiet_hours_end:
        return None
    
    # 오늘 운동했는지 확인
    today_workout = WorkoutLog.objects.filter(
        user=user,
        date=now.date()
    ).exists()
    
    if today_workout:
        return None
    
    # 메시지 생성
    profile = UserProfile.objects.filter(user=user).first()
    if profile:
        goal = profile.workout_days_per_week
        title = f"오늘의 운동 시간입니다! 💪"
        body = f"주 {goal}회 운동 목표를 달성하기 위해 오늘도 화이팅!"
    else:
        title = "운동할 시간입니다! 🏃‍♂️"
        body = "건강한 하루를 위해 운동을 시작해보세요!"
    
    # 알림 전송
    data = {
        'type': 'workout_reminder',
        'timestamp': now.isoformat(),
        'deep_link': '/workout'
    }
    
    message_id = send_notification(
        settings.fcm_token,
        title,
        body,
        data
    )
    
    # 로그 저장
    NotificationLog.objects.create(
        user=user,
        notification_type='workout_reminder',
        title=title,
        body=body,
        status='sent' if message_id else 'failed',
        fcm_message_id=message_id,
        data=data,
        sent_at=now if message_id else None
    )
    
    return message_id


def send_goal_achievement_notification(user, achievement_type, details):
    """목표 달성 알림 전송"""
    settings = NotificationSettings.objects.filter(user=user).first()
    
    if not settings or not settings.fcm_token or not settings.enable_goal_achievement_notif:
        return None
    
    # 메시지 생성
    if achievement_type == 'daily_steps':
        title = "일일 걸음 목표 달성! 🎯"
        body = f"{details['steps']:,}걸음을 달성하셨습니다! 축하합니다!"
    elif achievement_type == 'weekly_workout':
        title = "주간 운동 목표 달성! 🏆"
        body = f"이번 주 {details['count']}회 운동을 완료하셨습니다!"
    elif achievement_type == 'monthly_distance':
        title = "월간 거리 목표 달성! 🚀"
        body = f"이번 달 {details['distance']}km를 달성하셨습니다!"
    else:
        title = "목표 달성! 🎉"
        body = "축하합니다! 목표를 달성하셨습니다!"
    
    # 알림 전송
    data = {
        'type': 'goal_achievement',
        'achievement_type': achievement_type,
        'timestamp': timezone.now().isoformat(),
        'deep_link': '/profile/achievements'
    }
    data.update(details)
    
    message_id = send_notification(
        settings.fcm_token,
        title,
        body,
        data
    )
    
    # 로그 저장
    NotificationLog.objects.create(
        user=user,
        notification_type='goal_achievement',
        title=title,
        body=body,
        status='sent' if message_id else 'failed',
        fcm_message_id=message_id,
        data=data,
        sent_at=timezone.now() if message_id else None
    )
    
    return message_id


def send_social_activity_notification(user, activity_type, friend_user, details=None):
    """친구 활동 알림 전송"""
    settings = NotificationSettings.objects.filter(user=user).first()
    
    if not settings or not settings.fcm_token or not settings.enable_social_activity_notif:
        return None
    
    # 메시지 생성
    friend_name = friend_user.username
    
    if activity_type == 'friend_request':
        title = "새로운 친구 요청! 👥"
        body = f"{friend_name}님이 친구 요청을 보냈습니다."
    elif activity_type == 'workout_share':
        title = "친구가 운동을 공유했습니다! 💪"
        body = f"{friend_name}님이 {details.get('workout_name', '운동')}을 완료했습니다."
    elif activity_type == 'achievement_share':
        title = "친구가 성취를 달성했습니다! 🎉"
        body = f"{friend_name}님이 {details.get('achievement', '목표')}를 달성했습니다!"
    else:
        title = "친구 활동 알림"
        body = f"{friend_name}님의 새로운 활동이 있습니다."
    
    # 알림 전송
    data = {
        'type': 'social_activity',
        'activity_type': activity_type,
        'friend_id': str(friend_user.id),
        'friend_name': friend_name,
        'timestamp': timezone.now().isoformat(),
        'deep_link': '/social'
    }
    
    if details:
        data.update(details)
    
    message_id = send_notification(
        settings.fcm_token,
        title,
        body,
        data
    )
    
    # 로그 저장
    NotificationLog.objects.create(
        user=user,
        notification_type='social_activity',
        title=title,
        body=body,
        status='sent' if message_id else 'failed',
        fcm_message_id=message_id,
        data=data,
        sent_at=timezone.now() if message_id else None
    )
    
    return message_id


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request):
    """알림 읽음 처리"""
    notification_ids = request.data.get('notification_ids', [])
    
    if not notification_ids:
        return Response(
            {'error': '알림 ID가 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 사용자의 알림만 업데이트
    updated = NotificationLog.objects.filter(
        user=request.user,
        id__in=notification_ids
    ).update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return Response({
        'message': f'{updated}개의 알림이 읽음 처리되었습니다.'
    })
