"""
WebSocket consumer for real-time notifications
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # Create room name for this user
        self.room_name = f"notifications_{self.user.id}"
        self.room_group_name = f"notifications_{self.user.id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        if message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))

    # Receive message from room group
    async def notification_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
    
    async def achievement_unlocked(self, event):
        # Send achievement notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'achievement_unlocked',
            'achievement': event['achievement']
        }))
    
    async def level_up(self, event):
        # Send level up notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'level_up',
            'level': event['level'],
            'rewards': event.get('rewards', [])
        }))
