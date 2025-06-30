import json
import logging
from typing import Dict, Any, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from asgiref.sync import sync_to_async

from ..models import Conversation, DirectMessage, MessageReaction
from ..serializers import DirectMessageSerializer, ConversationSerializer

User = get_user_model()
logger = logging.getLogger('channels.dm')


class DirectMessageConsumer(AsyncWebsocketConsumer):
    """Direct Message WebSocket Consumer"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.conversation_id = None
        self.conversation_group_name = None
        self.user_group_name = None
    
    async def connect(self):
        """WebSocket 연결 처리"""
        # 사용자 인증 확인
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # URL에서 conversation_id 추출
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        
        # 사용자별 그룹 (모든 DM 알림용)
        self.user_group_name = f'dm_user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        # 특정 대화방에 참여하는 경우
        if self.conversation_id:
            # 대화방 접근 권한 확인
            has_access = await self.check_conversation_access(self.conversation_id)
            if not has_access:
                await self.close()
                return
            
            self.conversation_group_name = f'dm_conversation_{self.conversation_id}'
            await self.channel_layer.group_add(
                self.conversation_group_name,
                self.channel_name
            )
            
            # 대화방의 읽지 않은 메시지 읽음 처리
            await self.mark_messages_as_read(self.conversation_id)
        
        await self.accept()
        
        # 연결 성공 메시지
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to DM WebSocket'
        }))
        
        logger.info(f"User {self.user.username} connected to DM WebSocket")
    
    async def disconnect(self, close_code):
        """WebSocket 연결 해제 처리"""
        # 그룹에서 제거
        if self.user_group_name:
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        if self.conversation_group_name:
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
        
        logger.info(f"User {self.user.username if self.user else 'Unknown'} disconnected from DM WebSocket")
    
    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'send_message':
                await self.handle_send_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'mark_read':
                await self.handle_mark_read(data)
            elif message_type == 'add_reaction':
                await self.handle_add_reaction(data)
            elif message_type == 'remove_reaction':
                await self.handle_remove_reaction(data)
            elif message_type == 'heartbeat':
                await self.send_heartbeat_ack()
            else:
                await self.send_error(f"Unknown message type: {message_type}")
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            await self.send_error(f"Error: {str(e)}")
    
    async def handle_send_message(self, data: Dict[str, Any]):
        """메시지 전송 처리"""
        conversation_id = data.get('conversation_id')
        content = data.get('content', '').strip()
        recipient_id = data.get('recipient_id')  # 새 대화 시작용
        
        if not content:
            await self.send_error("Message content is required")
            return
        
        try:
            # 새 대화 시작 또는 기존 대화 가져오기
            if not conversation_id and recipient_id:
                conversation = await self.get_or_create_conversation(recipient_id)
                conversation_id = conversation.id
            elif conversation_id:
                conversation = await self.get_conversation(conversation_id)
                if not conversation:
                    await self.send_error("Conversation not found")
                    return
            else:
                await self.send_error("Either conversation_id or recipient_id is required")
                return
            
            # 메시지 생성
            message = await self.create_message(
                conversation=conversation,
                content=content,
                media_file=data.get('media_file'),
                media_type=data.get('media_type'),
                message_type=data.get('message_type', 'text'),
                referenced_story_id=data.get('referenced_story_id'),
                referenced_post_id=data.get('referenced_post_id')
            )
            
            # 메시지 직렬화
            message_data = await self.serialize_message(message)
            
            # 대화 참여자들에게 메시지 전송
            await self.channel_layer.group_send(
                f'dm_conversation_{conversation_id}',
                {
                    'type': 'new_message',
                    'message': message_data
                }
            )
            
            # 수신자에게 알림 전송
            recipients = await self.get_conversation_recipients(conversation, self.user)
            for recipient in recipients:
                await self.channel_layer.group_send(
                    f'dm_user_{recipient.id}',
                    {
                        'type': 'dm_notification',
                        'message': message_data,
                        'conversation_id': conversation_id
                    }
                )
            
            # 전송 확인
            await self.send(text_data=json.dumps({
                'type': 'message_sent',
                'message': message_data
            }))
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            await self.send_error(f"Failed to send message: {str(e)}")
    
    async def handle_typing(self, data: Dict[str, Any]):
        """타이핑 상태 처리"""
        conversation_id = data.get('conversation_id')
        is_typing = data.get('is_typing', False)
        
        if not conversation_id:
            return
        
        # 대화방 참여자들에게 타이핑 상태 전송
        await self.channel_layer.group_send(
            f'dm_conversation_{conversation_id}',
            {
                'type': 'typing_status',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def handle_mark_read(self, data: Dict[str, Any]):
        """메시지 읽음 처리"""
        conversation_id = data.get('conversation_id')
        message_ids = data.get('message_ids', [])
        
        if conversation_id:
            # 대화방의 모든 메시지 읽음 처리
            await self.mark_messages_as_read(conversation_id)
        elif message_ids:
            # 특정 메시지들만 읽음 처리
            await self.mark_specific_messages_as_read(message_ids)
        
        # 읽음 상태 업데이트 알림
        await self.send(text_data=json.dumps({
            'type': 'messages_marked_read',
            'conversation_id': conversation_id,
            'message_ids': message_ids
        }))
    
    async def handle_add_reaction(self, data: Dict[str, Any]):
        """메시지 반응 추가"""
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        if not message_id or not emoji:
            await self.send_error("Message ID and emoji are required")
            return
        
        try:
            reaction = await self.add_reaction(message_id, emoji)
            
            # 반응 데이터
            reaction_data = {
                'message_id': message_id,
                'user_id': self.user.id,
                'username': self.user.username,
                'emoji': emoji,
                'created_at': reaction.created_at.isoformat()
            }
            
            # 대화방 참여자들에게 반응 알림
            message = await self.get_message(message_id)
            if message:
                await self.channel_layer.group_send(
                    f'dm_conversation_{message.conversation_id}',
                    {
                        'type': 'reaction_added',
                        'reaction': reaction_data
                    }
                )
        except Exception as e:
            await self.send_error(f"Failed to add reaction: {str(e)}")
    
    async def handle_remove_reaction(self, data: Dict[str, Any]):
        """메시지 반응 제거"""
        message_id = data.get('message_id')
        emoji = data.get('emoji')
        
        if not message_id or not emoji:
            await self.send_error("Message ID and emoji are required")
            return
        
        try:
            await self.remove_reaction(message_id, emoji)
            
            # 반응 제거 데이터
            reaction_data = {
                'message_id': message_id,
                'user_id': self.user.id,
                'emoji': emoji
            }
            
            # 대화방 참여자들에게 반응 제거 알림
            message = await self.get_message(message_id)
            if message:
                await self.channel_layer.group_send(
                    f'dm_conversation_{message.conversation_id}',
                    {
                        'type': 'reaction_removed',
                        'reaction': reaction_data
                    }
                )
        except Exception as e:
            await self.send_error(f"Failed to remove reaction: {str(e)}")
    
    # WebSocket 이벤트 핸들러
    async def new_message(self, event):
        """새 메시지 전송"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))
    
    async def dm_notification(self, event):
        """DM 알림 전송"""
        await self.send(text_data=json.dumps({
            'type': 'dm_notification',
            'message': event['message'],
            'conversation_id': event['conversation_id']
        }))
    
    async def typing_status(self, event):
        """타이핑 상태 전송"""
        # 자신의 타이핑 상태는 무시
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing_status',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def reaction_added(self, event):
        """반응 추가 알림"""
        await self.send(text_data=json.dumps({
            'type': 'reaction_added',
            'reaction': event['reaction']
        }))
    
    async def reaction_removed(self, event):
        """반응 제거 알림"""
        await self.send(text_data=json.dumps({
            'type': 'reaction_removed',
            'reaction': event['reaction']
        }))
    
    # 헬퍼 메서드
    async def send_heartbeat_ack(self):
        """하트비트 응답"""
        await self.send(text_data=json.dumps({
            'type': 'heartbeat_ack',
            'timestamp': timezone.now().isoformat()
        }))
    
    async def send_error(self, message: str):
        """에러 메시지 전송"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))
    
    # 데이터베이스 관련 메서드
    @database_sync_to_async
    def check_conversation_access(self, conversation_id: int) -> bool:
        """대화방 접근 권한 확인"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_conversation(self, conversation_id: int) -> Optional[Conversation]:
        """대화방 가져오기"""
        try:
            return Conversation.objects.get(
                id=conversation_id,
                participants=self.user
            )
        except Conversation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_or_create_conversation(self, recipient_id: int) -> Conversation:
        """대화방 가져오기 또는 생성"""
        try:
            recipient = User.objects.get(id=recipient_id)
            
            # 기존 대화방 찾기
            conversation = Conversation.objects.filter(
                participants=self.user
            ).filter(
                participants=recipient
            ).first()
            
            if not conversation:
                # 새 대화방 생성
                conversation = Conversation.objects.create()
                conversation.participants.add(self.user, recipient)
            
            return conversation
        except User.DoesNotExist:
            raise ValueError("Recipient not found")
    
    @database_sync_to_async
    def create_message(self, **kwargs) -> DirectMessage:
        """메시지 생성"""
        return DirectMessage.objects.create(
            conversation=kwargs['conversation'],
            sender=self.user,
            content=kwargs['content'],
            media_file=kwargs.get('media_file'),
            media_type=kwargs.get('media_type'),
            message_type=kwargs.get('message_type', 'text'),
            referenced_story_id=kwargs.get('referenced_story_id'),
            referenced_post_id=kwargs.get('referenced_post_id')
        )
    
    @database_sync_to_async
    def serialize_message(self, message: DirectMessage) -> Dict[str, Any]:
        """메시지 직렬화"""
        serializer = DirectMessageSerializer(message)
        return serializer.data
    
    @database_sync_to_async
    def get_conversation_recipients(self, conversation: Conversation, exclude_user: User) -> list:
        """대화 참여자 중 특정 사용자를 제외한 나머지 가져오기"""
        return list(conversation.participants.exclude(id=exclude_user.id))
    
    @database_sync_to_async
    def mark_messages_as_read(self, conversation_id: int):
        """대화방의 읽지 않은 메시지 모두 읽음 처리"""
        DirectMessage.objects.filter(
            conversation_id=conversation_id,
            is_read=False
        ).exclude(
            sender=self.user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    @database_sync_to_async
    def mark_specific_messages_as_read(self, message_ids: list):
        """특정 메시지들 읽음 처리"""
        DirectMessage.objects.filter(
            id__in=message_ids,
            is_read=False
        ).exclude(
            sender=self.user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
    
    @database_sync_to_async
    def get_message(self, message_id: int) -> Optional[DirectMessage]:
        """메시지 가져오기"""
        try:
            return DirectMessage.objects.get(id=message_id)
        except DirectMessage.DoesNotExist:
            return None
    
    @database_sync_to_async
    def add_reaction(self, message_id: int, emoji: str) -> MessageReaction:
        """메시지 반응 추가"""
        message = DirectMessage.objects.get(id=message_id)
        
        # 대화 참여자인지 확인
        if not message.conversation.participants.filter(id=self.user.id).exists():
            raise ValueError("You are not a participant in this conversation")
        
        reaction, created = MessageReaction.objects.get_or_create(
            message=message,
            user=self.user,
            emoji=emoji
        )
        return reaction
    
    @database_sync_to_async
    def remove_reaction(self, message_id: int, emoji: str):
        """메시지 반응 제거"""
        MessageReaction.objects.filter(
            message_id=message_id,
            user=self.user,
            emoji=emoji
        ).delete()
