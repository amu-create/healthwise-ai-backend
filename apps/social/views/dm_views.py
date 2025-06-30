from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count, Exists, OuterRef, Max
from django.contrib.auth import get_user_model
from django.utils import timezone

from ..models import Conversation, DirectMessage, MessageReaction
from ..serializers import (
    ConversationSerializer, DirectMessageSerializer,
    CreateConversationSerializer, SendMessageSerializer,
    MessageReactionSerializer
)

User = get_user_model()


class ConversationViewSet(viewsets.ModelViewSet):
    """대화 관리 ViewSet"""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_queryset(self):
        """사용자가 참여 중인 대화 목록"""
        user = self.request.user
        
        # 마지막 메시지 시간으로 정렬
        return Conversation.objects.filter(
            participants=user
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')
    
    def create(self, request):
        """새 대화 생성 또는 기존 대화 반환"""
        serializer = CreateConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        participant_id = serializer.validated_data['participant_id']
        participant = get_object_or_404(User, id=participant_id)
        
        # 자기 자신과의 대화 방지
        if participant == request.user:
            return Response(
                {"error": "자기 자신과는 대화할 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 기존 대화 찾기
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(
            participants=participant
        ).first()
        
        if not conversation:
            # 새 대화 생성
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, participant)
        
        serializer = ConversationSerializer(conversation, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """메시지 전송"""
        conversation = self.get_object()
        
        # 대화 참여자인지 확인
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "이 대화에 참여할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 메시지 생성
        message = DirectMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            **serializer.validated_data
        )
        
        # 대화 업데이트 시간 갱신
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # WebSocket으로 실시간 전송 (consumer에서 처리)
        
        response_serializer = DirectMessageSerializer(
            message, 
            context={'request': request}
        )
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """대화의 메시지 목록"""
        conversation = self.get_object()
        
        # 대화 참여자인지 확인
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "이 대화에 참여할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 페이지네이션
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        messages = conversation.messages.select_related(
            'sender', 'referenced_story', 'referenced_post'
        ).prefetch_related(
            'reactions__user'
        ).order_by('-created_at')
        
        # 페이지네이션 적용
        start = (page - 1) * page_size
        end = start + page_size
        messages = messages[start:end]
        
        # 읽지 않은 메시지 읽음 처리
        unread_messages = [
            msg for msg in messages 
            if not msg.is_read and msg.sender != request.user
        ]
        if unread_messages:
            DirectMessage.objects.filter(
                id__in=[msg.id for msg in unread_messages]
            ).update(is_read=True, read_at=timezone.now())
        
        serializer = DirectMessageSerializer(
            messages, 
            many=True, 
            context={'request': request}
        )
        
        return Response({
            'results': serializer.data,
            'page': page,
            'page_size': page_size,
            'has_next': conversation.messages.count() > end
        })
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """대화의 모든 메시지를 읽음으로 표시"""
        conversation = self.get_object()
        
        # 대화 참여자인지 확인
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "이 대화에 참여할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 읽지 않은 메시지 읽음 처리
        updated_count = DirectMessage.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        return Response({
            'message': f'{updated_count}개의 메시지를 읽음으로 표시했습니다.'
        })
    
    @action(detail=True, methods=['delete'])
    def leave(self, request, pk=None):
        """대화 나가기"""
        conversation = self.get_object()
        
        # 대화 참여자인지 확인
        if not conversation.participants.filter(id=request.user.id).exists():
            return Response(
                {"error": "이 대화에 참여하고 있지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 대화에서 나가기
        conversation.participants.remove(request.user)
        
        # 참여자가 없으면 대화 삭제
        if conversation.participants.count() == 0:
            conversation.delete()
            
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """읽지 않은 메시지 수"""
        user = request.user
        
        # 사용자가 참여 중인 대화에서 읽지 않은 메시지 수 계산
        unread_count = DirectMessage.objects.filter(
            conversation__participants=user,
            is_read=False
        ).exclude(
            sender=user
        ).count()
        
        return Response({
            'unread_count': unread_count
        })


class DirectMessageViewSet(viewsets.ModelViewSet):
    """다이렉트 메시지 ViewSet"""
    serializer_class = DirectMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_queryset(self):
        """사용자가 참여 중인 대화의 메시지"""
        return DirectMessage.objects.filter(
            conversation__participants=self.request.user
        ).select_related(
            'sender', 'conversation', 'referenced_story', 'referenced_post'
        ).prefetch_related(
            'reactions__user'
        )
    
    @action(detail=True, methods=['post'])
    def add_reaction(self, request, pk=None):
        """메시지에 반응 추가"""
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response(
                {"error": "이모지를 선택해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 이미 같은 반응이 있는지 확인
        existing_reaction = MessageReaction.objects.filter(
            message=message,
            user=request.user,
            emoji=emoji
        ).first()
        
        if existing_reaction:
            # 이미 있으면 제거 (토글)
            existing_reaction.delete()
            return Response(
                {"message": "반응이 제거되었습니다."},
                status=status.HTTP_204_NO_CONTENT
            )
        
        # 새 반응 추가
        reaction = MessageReaction.objects.create(
            message=message,
            user=request.user,
            emoji=emoji
        )
        
        serializer = MessageReactionSerializer(
            reaction,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete'])
    def remove_reaction(self, request, pk=None):
        """메시지 반응 제거"""
        message = self.get_object()
        emoji = request.data.get('emoji')
        
        if not emoji:
            return Response(
                {"error": "이모지를 선택해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 반응 삭제
        deleted_count, _ = MessageReaction.objects.filter(
            message=message,
            user=request.user,
            emoji=emoji
        ).delete()
        
        if deleted_count == 0:
            return Response(
                {"error": "해당 반응을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """메시지 검색"""
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response(
                {"error": "검색어를 입력해주세요."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 사용자가 참여 중인 대화의 메시지만 검색
        messages = self.get_queryset().filter(
            content__icontains=query
        ).order_by('-created_at')[:50]
        
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
