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
    """사용자 프로필 조회 및 수정 (단순화)"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 간단한 게스트 체크
    is_guest = request.headers.get('X-Is-Guest') == 'true'
    if is_guest:
        return Response({
            'error': '게스트 사용자는 프로필에 접근할 수 없습니다.',
            'is_guest': True
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 하드코딩된 사용자 (포트폴리오용)
    try:
        user = User.objects.get(id=1)  # 테스트 사용자
    except User.DoesNotExist:
        return Response({
            'error': '사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    
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
            
            return Response({
                'success': True,
                'message': '프로필이 업데이트되었습니다.'
            })
        except UserProfile.DoesNotExist:
            return Response({
                'error': '프로필을 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'프로필 업데이트 오류: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
