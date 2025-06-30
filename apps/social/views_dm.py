from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Max, F
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import Conversation, DirectMessage, MessageReaction
from .serializers import (
    ConversationSerializer, DirectMessageSerializer, 
    MessageReactionSerializer, CreateConversationSerializer,
    SendMessageSerializer
)
from .websocket_utils import send_notification_to_user

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """대화 ViewSet"""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')
    
    def create(self, request):
        """새 대화 생성 또는 기존 대화 반환"""
        serializer = CreateConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        participant_id = serializer.validated_data['participant_id']
        participant = get_object_or_404(User, id=participant_id)
        
        # 자기 자신과는 대화 불가
        if participant == request.user:
            return Response(
                {'error': '자기 자신과는 대화할 수 없습니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 기존 대화가 있는지 확인
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=participant
        ).annotate(
            participant_count=Count('participants')
        ).filter(
            participant_count=2
        ).first()
        
        if not conversation:
            # 새 대화 생성
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, participant)
        
        serializer = self.get_serializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """대화의 메시지 목록"""
        conversation = self.get_object()
        
        # 읽지 않은 메시지를 읽음으로 표시
        DirectMessage.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        messages = DirectMessage.objects.filter(
            conversation=conversation
        ).select_related('sender').prefetch_related('reactions')
        
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = DirectMessageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = DirectMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """메시지 전송"""
        conversation = self.get_object()
        
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = DirectMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            **serializer.validated_data
        )
        
        # 대화 업데이트 시간 갱신
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # 상대방에게 실시간 알림 전송
        other_participant = conversation.get_other_participant(request.user)
        if other_participant:
            # WebSocket으로 메시지 전송
            send_notification_to_user(other_participant.id, {
                'type': 'new_message',
                'message': DirectMessageSerializer(message, context={'request': request}).data,
                'conversation_id': conversation.id,
                'timestamp': timezone.now().isoformat()
            })
        
        return Response(
            DirectMessageSerializer(message, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """전체 읽지 않은 메시지 수"""
        count = DirectMessage.objects.filter(
            conversation__participants=request.user,
            is_read=False
        ).exclude(
            sender=request.user
        ).count()
        
        return Response({'unread_count': count})


class DirectMessageViewSet(viewsets.ModelViewSet):
    """다이렉트 메시지 ViewSet"""
    serializer_class = DirectMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DirectMessage.objects.filter(
            Q(sender=self.request.user) | 
            Q(conversation__participants=self.request.user)
        ).select_related('sender', 'conversation').prefetch_related('reactions')
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """메시지 읽음 처리"""
        message = self.get_object()
        
        # 본인이 보낸 메시지는 읽음 처리 불가
        if message.sender == request.user:
            return Response(
                {'error': '본인이 보낸 메시지입니다.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message.mark_as_read()
        return Response({'status': 'marked as read'})
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """메시지에 반응 추가"""
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response(
                {'error': '이모지를 선택해주세요.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 기존 반응 확인
        existing_reaction = MessageReaction.objects.filter(
            message=message,
            user=request.user,
            emoji=emoji
        ).first()
        
        if existing_reaction:
            # 기존 반응 제거
            existing_reaction.delete()
            return Response({'status': 'reaction removed'})
        else:
            # 새 반응 추가
            reaction = MessageReaction.objects.create(
                message=message,
                user=request.user,
                emoji=emoji
            )
            
            # 메시지 발신자에게 알림
            if message.sender != request.user:
                send_notification_to_user(message.sender.id, {
                    'type': 'message_reaction',
                    'reaction': {
                        'user': request.user.username,
                        'emoji': emoji,
                        'message_id': message.id
                    },
                    'timestamp': timezone.now().isoformat()
                })
            
            serializer = MessageReactionSerializer(reaction)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def delete_message(self, request, pk=None):
        """메시지 삭제 (본인 메시지만)"""
        message = self.get_object()
        
        if message.sender != request.user:
            return Response(
                {'error': '본인의 메시지만 삭제할 수 있습니다.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        message.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
