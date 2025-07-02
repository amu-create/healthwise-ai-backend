from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from ..models import UserProfile
from ..authentication import SimpleTokenAuthentication
from rest_framework.authentication import SessionAuthentication
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

@api_view(['GET', 'PUT', 'OPTIONS'])
@permission_classes([AllowAny])
@authentication_classes([SimpleTokenAuthentication, SessionAuthentication])
def user_profile(request):
    """사용자 프로필 조회 및 수정"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 인증 확인 - 더 유연하게 처리
    user = None
    
    # 1. Django 인증된 사용자
    if request.user and request.user.is_authenticated:
        user = request.user
        logger.info(f"Authenticated user from Django: {user.username}")
    
    # 2. 헤더에서 사용자 ID 확인 (프록시 환경)
    elif request.META.get('HTTP_X_USER_ID'):
        try:
            user_id = request.META.get('HTTP_X_USER_ID')
            user = User.objects.get(id=user_id)
            logger.info(f"User from X-User-ID header: {user.username}")
        except User.DoesNotExist:
            logger.error(f"User not found with ID: {user_id}")
            pass
    
    # 3. 토큰에서 사용자 확인
    elif hasattr(request, 'auth') and request.auth:
        # SimpleTokenAuthentication이 설정한 사용자
        if hasattr(request, 'user') and request.user:
            user = request.user
            logger.info(f"User from token auth: {user.username}")
    
    # 게스트 사용자 체크
    is_guest = request.headers.get('X-Is-Guest') == 'true'
    if is_guest:
        logger.info("Guest user detected")
        return Response({
            'error': '게스트 사용자는 프로필에 접근할 수 없습니다.',
            'is_guest': True
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 사용자를 찾을 수 없는 경우
    if not user:
        logger.error("No authenticated user found")
        return Response({
            'error': '인증이 필요합니다.',
            'is_guest': False,
            'debug_info': {
                'has_auth_header': bool(request.META.get('HTTP_AUTHORIZATION')),
                'has_user_id_header': bool(request.META.get('HTTP_X_USER_ID')),
                'is_authenticated': request.user.is_authenticated if hasattr(request, 'user') else False
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    if request.method == 'GET':
        try:
            profile = UserProfile.objects.get(user=user)
            today = date.today()
            age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)) if profile.birth_date else None
            
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile': {
                    'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                    'age': age,
                    'gender': profile.gender,
                    'height': profile.height,
                    'weight': profile.weight,
                    'diseases': profile.diseases,
                    'health_conditions': profile.health_conditions,
                    'allergies': profile.allergies,
                    'fitness_level': profile.fitness_level,
                    'fitness_goals': profile.fitness_goals,
                    'created_at': profile.created_at.isoformat(),
                    'updated_at': profile.updated_at.isoformat()
                }
            })
        except UserProfile.DoesNotExist:
            # 프로필이 없으면 기본값으로 생성
            profile = UserProfile.objects.create(user=user)
            return Response({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile': {
                    'birth_date': None,
                    'age': None,
                    'gender': None,
                    'height': None,
                    'weight': None,
                    'diseases': [],
                    'health_conditions': [],
                    'allergies': [],
                    'fitness_level': 'beginner',
                    'fitness_goals': [],
                    'created_at': profile.created_at.isoformat(),
                    'updated_at': profile.updated_at.isoformat()
                }
            })
    
    elif request.method == 'PUT':
        try:
            profile = UserProfile.objects.get(user=user)
            data = request.data.get('profile', {})
            
            # 업데이트 가능한 필드들
            if 'birth_date' in data:
                profile.birth_date = data['birth_date']
            if 'gender' in data:
                profile.gender = data['gender']
            if 'height' in data:
                profile.height = float(data['height'])
            if 'weight' in data:
                profile.weight = float(data['weight'])
            if 'diseases' in data:
                profile.diseases = data['diseases']
            if 'health_conditions' in data:
                profile.health_conditions = data['health_conditions']
            if 'allergies' in data:
                profile.allergies = data['allergies']
            if 'fitness_level' in data:
                profile.fitness_level = data['fitness_level']
            if 'fitness_goals' in data:
                profile.fitness_goals = data['fitness_goals']
            
            profile.save()
            
            # 나이 계산
            today = date.today()
            age = today.year - profile.birth_date.year - ((today.month, today.day) < (profile.birth_date.month, profile.birth_date.day)) if profile.birth_date else None
            
            return Response({
                'success': True,
                'message': '프로필이 업데이트되었습니다.',
                'profile': {
                    'birth_date': profile.birth_date.isoformat() if profile.birth_date else None,
                    'age': age,
                    'gender': profile.gender,
                    'height': profile.height,
                    'weight': profile.weight,
                    'diseases': profile.diseases,
                    'health_conditions': profile.health_conditions,
                    'allergies': profile.allergies,
                    'fitness_level': profile.fitness_level,
                    'fitness_goals': profile.fitness_goals,
                    'updated_at': profile.updated_at.isoformat()
                }
            })
        except UserProfile.DoesNotExist:
            return Response({
                'error': '프로필을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f'Profile update error: {str(e)}')
            return Response({
                'error': f'프로필 업데이트 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
