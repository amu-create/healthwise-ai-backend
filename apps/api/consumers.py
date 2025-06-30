import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """실시간 알림을 위한 WebSocket Consumer"""
    
    async def connect(self):
        # 사용자 인증 확인
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        # 사용자별 알림 채널 그룹
        self.room_group_name = f'notifications_{self.user.id}'
        
        # 채널 그룹에 참가
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # 연결 시 읽지 않은 알림 개수 전송
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'unread_count': unread_count
        }))
    
    async def disconnect(self, close_code):
        # 채널 그룹에서 나가기
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'mark_read':
            # 알림을 읽음으로 표시
            notification_id = data.get('notification_id')
            await self.mark_notification_read(notification_id)
        elif message_type == 'mark_all_read':
            # 모든 알림을 읽음으로 표시
            await self.mark_all_notifications_read()
    
    async def notification_message(self, event):
        """알림 메시지를 WebSocket으로 전송"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    async def achievement_unlocked(self, event):
        """업적 달성 알림"""
        await self.send(text_data=json.dumps({
            'type': 'achievement_unlocked',
            'achievement': event['achievement'],
            'animation': True
        }))
    
    async def level_up(self, event):
        """레벨업 알림"""
        await self.send(text_data=json.dumps({
            'type': 'level_up',
            'level': event['level'],
            'title': event['title'],
            'animation': True
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(
            user=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user=self.user
            )
            notification.is_read = True
            notification.save()
        except Notification.DoesNotExist:
            pass
    
    @database_sync_to_async
    def mark_all_notifications_read(self):
        Notification.objects.filter(
            user=self.user,
            is_read=False
        ).update(is_read=True)
