"""
Direct Messages WebSocket Consumer
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.social.models import DirectMessage
from apps.social.serializers import DirectMessageSerializer

User = get_user_model()


class DirectMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # Create room name for this user
        self.room_name = f"dm_{self.user.id}"
        self.room_group_name = f"dm_{self.user.id}"

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
        
        if message_type == 'send_message':
            # Handle sending a new message
            recipient_id = text_data_json.get('recipient_id')
            content = text_data_json.get('content')
            
            if recipient_id and content:
                # Create message in database
                message = await self.create_message(recipient_id, content)
                
                if message:
                    # Send message to sender
                    await self.send(text_data=json.dumps({
                        'type': 'message_sent',
                        'message': message
                    }))
                    
                    # Send message to recipient
                    await self.channel_layer.group_send(
                        f"dm_{recipient_id}",
                        {
                            'type': 'new_message',
                            'message': message
                        }
                    )
        
        elif message_type == 'mark_read':
            # Mark message as read
            message_id = text_data_json.get('message_id')
            if message_id:
                await self.mark_message_read(message_id)
                
        elif message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))

    # Receive message from room group
    async def new_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))
    
    @database_sync_to_async
    def create_message(self, recipient_id, content):
        try:
            recipient = User.objects.get(id=recipient_id)
            message = DirectMessage.objects.create(
                sender=self.user,
                recipient=recipient,
                content=content
            )
            # Serialize the message
            serializer = DirectMessageSerializer(message)
            return serializer.data
        except User.DoesNotExist:
            return None
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            message = DirectMessage.objects.get(
                id=message_id,
                recipient=self.user
            )
            if not message.is_read:
                message.is_read = True
                message.read_at = timezone.now()
                message.save()
            return True
        except DirectMessage.DoesNotExist:
            return False
