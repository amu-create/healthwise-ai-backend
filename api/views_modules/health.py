"""
Health related views
"""
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime
import logging

from ..services.data import HEALTH_OPTIONS
from ..ai_service import get_chatbot
from ..models import UserProfile

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """DB 연결 상태를 확인하는 헬스체크 엔드포인트"""
    import django.db
    from django.db import connection
    
    result = {
        'status': 'ok',
        'api': 'running',
        'timestamp': datetime.now().isoformat(),
    }
    
    # DB 연결 테스트
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        result['database'] = 'connected'
        
        # 사용자 수 확인
        user_count = User.objects.count()
        result['users'] = user_count
        
        # 세션 테스트
        result['session_key'] = request.session.session_key or 'no-session'
        
    except Exception as e:
        result['database'] = 'error'
        result['db_error'] = str(e)
        result['status'] = 'error'
    
    # Redis 연결 테스트
    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 10)
        if cache.get('health_check') == 'ok':
            result['redis'] = 'connected'
        else:
            result['redis'] = 'not working'
    except Exception as e:
        result['redis'] = 'error'
        result['redis_error'] = str(e)
    
    return Response(result)


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def health_options(request):
    """건강 선택지 API"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response(HEALTH_OPTIONS)


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def api_health(request):
    """간단한 헬스체크"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    return Response({
        'status': 'healthy',
        'service': 'api',
        'version': '1.0.0'
    })


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def health_consultation(request):
    """AI 건강 상담"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = request.data
        question = data.get('question', '')
        category = data.get('category', 'general')
        
        # 사용자 정보 수집
        user_data = {
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'username': request.user.username if request.user.is_authenticated else 'Guest',
        }
        
        # 프로필 정보 추가
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            user_data.update({
                'birth_date': profile.birth_date,
                'gender': profile.gender,
                'height': profile.height,
                'weight': profile.weight,
                'diseases': profile.diseases,
                'allergies': profile.allergies,
                'fitness_level': profile.fitness_level
            })
        
        # AI 챗봇 사용
        chatbot = get_chatbot()
        result = chatbot.get_health_consultation(user_data, question)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'error': f'Health consultation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot_status(request):
    """챗봇 상태"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 사용자 컨텍스트 수집
    user_context = {}
    has_profile = False
    
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            from datetime import date
            today = date.today()
            age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)) if profile.birth_date else 30
            
            user_context = {
                'age': age,
                'gender': profile.gender or 'unknown',
                'height': profile.height,
                'weight': profile.weight,
                'fitness_level': profile.fitness_level,
                'diseases': profile.diseases,
                'allergies': profile.allergies,
                'exercise_experience': profile.fitness_level
            }
            has_profile = True
        except UserProfile.DoesNotExist:
            pass
    
    return Response({
        'status': 'available',
        'user_context': user_context,
        'message_count': 0,
        'has_profile': has_profile
    })


@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot_sessions(request):
    """챗봇 세션"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    if request.method == 'POST':
        # 새 세션 생성
        session_id = f"session-{datetime.now().timestamp()}"
        return Response({
            'session_id': session_id,
            'created_at': datetime.now().isoformat()
        })
    
    # GET - 세션 목록 (프론트엔드가 기대하는 형식)
    sessions = []
    
    # 사용자가 인증된 경우 기본 세션 추가
    if request.user.is_authenticated:
        sessions.append({
            'id': f"session-{request.user.id}",
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'message_count': 0
        })
    
    return Response({
        'count': len(sessions),
        'results': sessions,
        'next': None,
        'previous': None,
        'active_session': {
            'id': 'guest-session' if not request.user.is_authenticated else f"session-{request.user.id}",
            'created_at': datetime.now().isoformat()
        }
    })


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot_sessions_active(request):
    """활성 챗봇 세션"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 항상 활성 세션 반환
    session_id = 'guest-session' if not request.user.is_authenticated else f"session-{request.user.id}"
    
    return Response({
        'session': {
            'id': session_id,
            'created_at': datetime.now().isoformat(),
            'messages': []  # 빈 메시지 배열
        },
        'session_id': session_id
    })


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def chatbot(request):
    """메인 챗봇 API"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        data = request.data
        message = data.get('message', '')
        language = data.get('language', 'ko')
        
        # 로깅 추가
        logger.info(f"Chatbot request - User authenticated: {request.user.is_authenticated}")
        logger.info(f"User: {request.user.username if request.user.is_authenticated else 'Anonymous'}")
        logger.info(f"Session key: {request.session.session_key}")
        
        # 사용자 정보 수집
        user_data = {
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'username': request.user.username if request.user.is_authenticated else 'Guest',
            'is_authenticated': request.user.is_authenticated
        }
        
        # 프로필 정보 추가
        if request.user.is_authenticated:
            try:
                profile = UserProfile.objects.get(user=request.user)
                user_data.update({
                    'birth_date': profile.birth_date,
                    'gender': profile.gender,
                    'height': profile.height,
                    'weight': profile.weight,
                    'diseases': profile.diseases,
                    'allergies': profile.allergies,
                    'fitness_level': profile.fitness_level
                })
                logger.info(f"Profile found for user {request.user.username}")
            except UserProfile.DoesNotExist:
                logger.warning(f"No profile found for user {request.user.username}")
        
        # AI 챗봇 사용
        chatbot = get_chatbot()
        result = chatbot.get_health_consultation(user_data, message)
        
        # 응답 형식 맞추기
        response_data = {
            'success': result.get('success', True),
            'response': result.get('response', ''),
            'raw_response': result.get('response', ''),
            'sources': [],
            'user_context': user_data,
            'session_id': f"session-{request.user.id}" if request.user.is_authenticated else 'guest-session',
            'is_authenticated': request.user.is_authenticated
        }
        
        logger.info(f"Chatbot response - Session ID: {response_data['session_id']}")
        
        return Response(response_data)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': f'Chatbot error: {str(e)}',
            'response': '죄송합니다. 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
