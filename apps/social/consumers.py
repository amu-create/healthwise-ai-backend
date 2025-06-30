import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        # Get user from scope (provided by AuthMiddlewareStack)
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            # Reject connection for anonymous users
            await self.close()
            return
            
        # Create a unique channel name for this user
        self.room_group_name = f"notifications_{self.user.id}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Accept WebSocket connection
        await self.accept()
        
        # Send initial connection confirmation
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected to notification service",
            "timestamp": datetime.now().isoformat()
        }))
        
        logger.info(f"WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        logger.info(f"WebSocket disconnected for user {self.user.username if hasattr(self, 'user') else 'Unknown'}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'heartbeat':
                # Respond to heartbeat
                await self.send(text_data=json.dumps({
                    "type": "heartbeat_ack",
                    "timestamp": datetime.now().isoformat()
                }))
            elif message_type == 'mark_read':
                # Mark notification as read
                notification_id = data.get('notification_id')
                if notification_id:
                    await self.mark_notification_read(notification_id)
            else:
                # Echo message back (for testing)
                await self.send(text_data=json.dumps({
                    "type": "echo",
                    "message": data.get('message', ''),
                    "timestamp": datetime.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error in receive: {e}")
            await self.send(text_data=json.dumps({
                "type": "error", 
                "message": "Server error occurred",
                "timestamp": datetime.now().isoformat()
            }))
    
    # Receive notification from channel layer
    async def notification_message(self, event):
        """Handle notification messages from channel layer"""
        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            "type": "notification",
            "notification": event["notification"],
            "timestamp": datetime.now().isoformat()
        }))
    
    async def achievement_unlocked(self, event):
        """Handle achievement unlock notifications"""
        await self.send(text_data=json.dumps({
            "type": "achievement",
            "achievement": event["achievement"],
            "timestamp": datetime.now().isoformat()
        }))
    
    async def level_up(self, event):
        """Handle level up notifications"""
        await self.send(text_data=json.dumps({
            "type": "level_up",
            "level": event["level"],
            "timestamp": datetime.now().isoformat()
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark a notification as read in the database"""
        from apps.social.models import Notification
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=self.user
            )
            notification.is_read = True
            notification.save()
            return True
        except Notification.DoesNotExist:
            return False


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for direct messages"""
    
    async def connect(self):
        """Handle WebSocket connection for chat"""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # Get conversation ID from URL route
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        
        if self.conversation_id:
            # Check if user is participant of this conversation
            is_participant = await self.check_conversation_participant()
            if not is_participant:
                await self.close()
                return
            
            self.room_group_name = f"chat_{self.conversation_id}"
        else:
            # Personal chat channel for receiving messages from any conversation
            self.room_group_name = f"chat_user_{self.user.id}"
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected to chat service",
            "timestamp": datetime.now().isoformat()
        }))
        
        logger.info(f"Chat WebSocket connected for user {self.user.username}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
        logger.info(f"Chat WebSocket disconnected for user {self.user.username if hasattr(self, 'user') else 'Unknown'}")
    
    async def receive(self, text_data):
        """Handle messages from WebSocket client"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'message':
                # Send message
                await self.handle_message(data)
            elif message_type == 'typing':
                # Broadcast typing indicator
                await self.handle_typing(data)
            elif message_type == 'read':
                # Mark messages as read
                await self.handle_read(data)
            elif message_type == 'reaction':
                # Add reaction to message
                await self.handle_reaction(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format",
                "timestamp": datetime.now().isoformat()
            }))
        except Exception as e:
            logger.error(f"Error in chat receive: {e}")
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Server error occurred",
                "timestamp": datetime.now().isoformat()
            }))
    
    async def handle_message(self, data):
        """Handle sending a new message"""
        content = data.get('content')
        conversation_id = data.get('conversation_id', self.conversation_id)
        
        if not content or not conversation_id:
            return
        
        # Save message to database
        message = await self.save_message(conversation_id, content)
        
        if message:
            # Broadcast to conversation participants
            await self.channel_layer.group_send(
                f"chat_{conversation_id}",
                {
                    "type": "chat_message",
                    "message": message
                }
            )
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        conversation_id = data.get('conversation_id', self.conversation_id)
        is_typing = data.get('is_typing', False)
        
        if conversation_id:
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                f"chat_{conversation_id}",
                {
                    "type": "typing_indicator",
                    "user_id": self.user.id,
                    "username": self.user.username,
                    "is_typing": is_typing
                }
            )
    
    async def handle_read(self, data):
        """Handle marking messages as read"""
        message_ids = data.get('message_ids', [])
        
        if message_ids:
            await self.mark_messages_read(message_ids)
    
    async def handle_reaction(self, data):
        """Handle adding reaction to message"""
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        if message_id and emoji:
            reaction = await self.add_reaction(message_id, emoji)
            if reaction:
                # Broadcast reaction update
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "reaction_update",
                        "reaction": reaction
                    }
                )
    
    # Receive message from channel layer
    async def chat_message(self, event):
        """Handle chat messages from channel layer"""
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"],
            "timestamp": datetime.now().isoformat()
        }))
    
    async def typing_indicator(self, event):
        """Handle typing indicator from channel layer"""
        # Don't send typing indicator to the sender
        if event["user_id"] != self.user.id:
            await self.send(text_data=json.dumps({
                "type": "typing",
                "user_id": event["user_id"],
                "username": event["username"],
                "is_typing": event["is_typing"],
                "timestamp": datetime.now().isoformat()
            }))
    
    async def reaction_update(self, event):
        """Handle reaction updates from channel layer"""
        await self.send(text_data=json.dumps({
            "type": "reaction",
            "reaction": event["reaction"],
            "timestamp": datetime.now().isoformat()
        }))
    
    @database_sync_to_async
    def check_conversation_participant(self):
        """Check if user is participant of the conversation"""
        from apps.social.models import Conversation
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, conversation_id, content):
        """Save message to database"""
        from apps.social.models import DirectMessage, Conversation
        from apps.social.serializers import DirectMessageSerializer
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            message = DirectMessage.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            # Update conversation timestamp
            conversation.updated_at = datetime.now()
            conversation.save()
            
            # Serialize message
            serializer = DirectMessageSerializer(message)
            return serializer.data
        except Conversation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        """Mark messages as read"""
        from apps.social.models import DirectMessage
        DirectMessage.objects.filter(
            id__in=message_ids,
            conversation__participants=self.user
        ).exclude(
            sender=self.user
        ).update(
            is_read=True,
            read_at=datetime.now()
        )
    
    @database_sync_to_async
    def add_reaction(self, message_id, emoji):
        """Add reaction to message"""
        from apps.social.models import DirectMessage, MessageReaction
        from apps.social.serializers import MessageReactionSerializer
        try:
            message = DirectMessage.objects.get(
                id=message_id,
                conversation__participants=self.user
            )
            reaction, created = MessageReaction.objects.get_or_create(
                message=message,
                user=self.user,
                emoji=emoji
            )
            if not created:
                # Remove existing reaction
                reaction.delete()
                return None
            
            serializer = MessageReactionSerializer(reaction)
            return serializer.data
        except DirectMessage.DoesNotExist:
            return None
