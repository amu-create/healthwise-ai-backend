import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
import logging

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = 'general'
        self.room_group_name = f'chat_{self.room_name}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection success message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to chat'
        }))
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        user = self.scope["user"]
        
        username = user.username if user.is_authenticated else f'Guest_{self.scope["session"].session_key[:8]}'
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'username': username
            }
        )
    
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': message,
            'username': username
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if user.is_authenticated:
            self.user_group_name = f'notifications_{user.id}'
        else:
            # Guest 사용자를 위한 세션 기반 그룹
            session_key = self.scope["session"].session_key
            self.user_group_name = f'notifications_guest_{session_key}'
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def notification_message(self, event):
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'data': event['data']
        }))


class WorkoutConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.workout_session_id = self.scope['url_route']['kwargs'].get('session_id', 'default')
        self.workout_group_name = f'workout_{self.workout_session_id}'
        
        await self.channel_layer.group_add(
            self.workout_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.workout_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')
        
        if action == 'update_progress':
            await self.channel_layer.group_send(
                self.workout_group_name,
                {
                    'type': 'workout_update',
                    'data': text_data_json.get('data', {})
                }
            )
    
    async def workout_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'workout_progress',
            'data': event['data']
        }))
