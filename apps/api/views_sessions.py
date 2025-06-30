from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Max, Q
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from apps.core.models import ChatSession, ChatMessage
from .authentication import CsrfExemptSessionAuthentication
import logging
from datetime import timedelta
import re

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class ChatSessionView(APIView):
    """대화 세션 관리 API"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [CsrfExemptSessionAuthentication]
    
    def get(self, request):
        """대화 세션 목록 조회"""
        try:
            # 사용자 검증 로깅
            logger.info(f"Session list requested by user: {request.user.id} ({request.user.email})")
            
            limit = int(request.query_params.get('limit', 7))
            offset = int(request.query_params.get('offset', 0))
            
            # 명시적으로 현재 사용자의 세션만 조회
            sessions = ChatSession.objects.filter(
                user__id=request.user.id  # 명시적 ID 매칭
            ).select_related('user').annotate(
                message_count=Count('messages', filter=Q(messages__user=request.user)),
                last_message_time=Max('messages__created_at', filter=Q(messages__user=request.user))
            ).order_by('-started_at')[offset:offset+limit]
            
            # 세션 데이터 구성
            session_list = []
            for session in sessions:
                # 세션의 첫 번째 사용자 메시지를 기반으로 제목 생성
                first_user_message = session.messages.filter(
                    sender='user'
                ).order_by('created_at').first()
                
                if first_user_message:
                    # 제목 생성 (첫 메시지에서 요약)
                    title = self._generate_session_title(first_user_message.message)
                else:
                    # 사용자별 세션 번호 사용
                    title = f"대화 세션 #{session.user_session_number}"
                
                # 세션에 저장된 제목이 있으면 사용
                if session.summary:
                    title = session.summary
                
                session_data = {
                    'id': session.id,
                    'session_number': session.user_session_number,
                    'title': title,
                    'started_at': session.started_at.isoformat(),
                    'ended_at': session.ended_at.isoformat() if session.ended_at else None,
                    'is_active': session.is_active,
                    'message_count': session.message_count,
                    'last_message_time': session.last_message_time.isoformat() if session.last_message_time else None,
                }
                session_list.append(session_data)
            
            # 전체 세션 수
            total_sessions = ChatSession.objects.filter(user=request.user).count()
            
            return Response({
                'sessions': session_list,
                'total': total_sessions,
                'has_more': offset + limit < total_sessions
            })
            
        except Exception as e:
            logger.error(f"세션 목록 조회 오류: {str(e)}")
            return Response({
                'error': '세션 목록을 불러올 수 없습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """새 대화 세션 생성"""
        try:
            # 기존 활성 세션 종료
            ChatSession.objects.filter(
                user=request.user,
                is_active=True
            ).update(
                is_active=False,
                ended_at=timezone.now()
            )
            
            # 새 세션 생성
            session = ChatSession.objects.create(
                user=request.user,
                is_active=True
            )
            
            return Response({
                'session_id': session.id,
                'message': '새 대화 세션이 생성되었습니다.'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"세션 생성 오류: {str(e)}")
            return Response({
                'error': '세션 생성 중 오류가 발생했습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request, session_id=None):
        """세션 정보 수정 (제목 변경 등)"""
        try:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user
            )
            
            # 제목 수정
            if 'title' in request.data:
                session.summary = request.data['title']
                session.save()
            
            # 세션 종료
            if 'end_session' in request.data and request.data['end_session']:
                session.end_session()
            
            return Response({
                'message': '세션이 업데이트되었습니다.',
                'session_id': session.id
            })
            
        except ChatSession.DoesNotExist:
            return Response({
                'error': '세션을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"세션 수정 오류: {str(e)}")
            return Response({
                'error': '세션 수정 중 오류가 발생했습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, session_id=None):
        """세션 삭제"""
        try:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user
            )
            
            # 세션과 관련된 메시지도 함께 삭제
            session.delete()
            
            return Response({
                'message': '세션이 삭제되었습니다.'
            })
            
        except ChatSession.DoesNotExist:
            return Response({
                'error': '세션을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"세션 삭제 오류: {str(e)}")
            return Response({
                'error': '세션 삭제 중 오류가 발생했습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_session_title(self, first_message):
        """첫 메시지를 기반으로 세션 제목 생성"""
        # 메시지가 너무 길면 자르기
        if len(first_message) > 50:
            title = first_message[:47] + "..."
        else:
            title = first_message
        
        # 줄바꿈 제거
        title = title.replace('\n', ' ').strip()
        
        # 특수문자 정리
        title = re.sub(r'\s+', ' ', title)
        
        return title

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_messages(request, session_id):
    """특정 세션의 메시지 조회"""
    try:
        # 사용자 검증 로깅
        logger.info(f"Session {session_id} messages requested by user: {request.user.id}")
        
        # 세션 확인 - 반드시 현재 사용자 확인
        session = ChatSession.objects.get(
            id=session_id,
            user__id=request.user.id  # 명시적 ID 매칭
        )
        
        # 메시지 조회 - 이중 보안 확인
        messages = ChatMessage.objects.filter(
            session=session,
            user=request.user  # 메시지도 사용자 필터링
        ).order_by('created_at')
        
        # 메시지 데이터 구성
        message_list = []
        for msg in messages:
            message_data = {
                'id': msg.id,
                'sender': msg.sender,
                'message': msg.message,
                'created_at': msg.created_at.isoformat(),
                'context': msg.context
            }
            message_list.append(message_data)
        
        return Response({
            'session_id': session_id,
            'messages': message_list,
            'total': len(message_list)
        })
        
    except ChatSession.DoesNotExist:
        return Response({
            'error': '세션을 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"세션 메시지 조회 오류: {str(e)}")
        return Response({
            'error': '메시지를 불러올 수 없습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_session(request):
    """현재 활성 세션 조회 또는 생성"""
    try:
        # 활성 세션 찾기
        session = ChatSession.objects.filter(
            user=request.user,
            is_active=True
        ).first()
        
        # 없으면 새로 생성
        if not session:
            session = ChatSession.objects.create(
                user=request.user,
                is_active=True
            )
        
        # 세션의 메시지 수 확인
        message_count = session.messages.count()
        
        return Response({
            'session_id': session.id,
            'message_count': message_count,
            'started_at': session.started_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"활성 세션 조회 오류: {str(e)}")
        return Response({
            'error': '세션을 불러올 수 없습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
