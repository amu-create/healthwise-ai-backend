from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from ..models import UserProfile
from datetime import date
import logging

logger = logging.getLogger(__name__)

@api_view(['GET', 'PUT', 'OPTIONS'])
@permission_classes([AllowAny])
def user_profile(request):
    """사용자 프로필 조회 및 수정"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 인증된 사용자 확인
    if not request.user.is_authenticated:
        return Response({
            'error': '로그인이 필요합니다.',
            'is_guest': True
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    user = request.user
    
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
                    'diseases': profile.diseases or [],
                    'health_conditions': profile.health_conditions or [],
                    'allergies': profile.allergies or [],
                    'fitness_level': profile.fitness_level or 'beginner',
                    'fitness_goals': profile.fitness_goals or [],
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
                # 빈 문자열이나 None인 경우 처리
                birth_date_value = data['birth_date']
                if birth_date_value and birth_date_value.strip():
                    profile.birth_date = birth_date_value
                else:
                    profile.birth_date = None
                    
            if 'gender' in data:
                profile.gender = data['gender']
            if 'height' in data and data['height']:
                profile.height = float(data['height'])
            if 'weight' in data and data['weight']:
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
            
            logger.info(f"Profile updated for user {user.username}")
            
            return Response({
                'success': True,
                'message': '프로필이 업데이트되었습니다.'
            })
        except UserProfile.DoesNotExist:
            return Response({
                'error': '프로필을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({
                'error': f'입력값 오류: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Profile update error for user {user.username}: {str(e)}")
            return Response({
                'error': f'프로필 업데이트 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
