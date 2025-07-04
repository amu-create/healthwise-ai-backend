"""
인증 관련 뷰
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import transaction
from .jwt_auth import create_user_response, authenticate_user, get_tokens_for_user
from .serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    사용자 회원가입
    """
    try:
        data = request.data
        
        # 필수 필드 검증
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return Response({
                'error': '모든 필드를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 중복 검사
        if User.objects.filter(username=username).exists():
            return Response({
                'error': '이미 사용중인 사용자명입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            return Response({
                'error': '이미 사용중인 이메일입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 사용자 생성
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # 프로필 정보가 있으면 업데이트
            profile_data = data.get('profile', {})
            if profile_data:
                from .models import UserProfile
                profile = user.profile
                
                # 프로필 필드 업데이트
                for field in ['birth_date', 'gender', 'height', 'weight', 
                             'fitness_level', 'fitness_goals']:
                    if field in profile_data:
                        setattr(profile, field, profile_data[field])
                
                profile.save()
        
        # 응답 생성
        response_data = create_user_response(user)
        logger.info(f"User registered successfully: {username}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            'error': '회원가입 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    사용자 로그인
    """
    try:
        data = request.data
        
        # 로그인 정보 추출
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not password:
            return Response({
                'error': '비밀번호를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not (username or email):
            return Response({
                'error': '사용자명 또는 이메일을 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 인증 시도
        user = authenticate_user(username=username, email=email, password=password)
        
        if not user:
            return Response({
                'error': '잘못된 로그인 정보입니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 응답 생성
        response_data = create_user_response(user)
        logger.info(f"User logged in successfully: {user.username}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return Response({
            'error': '로그인 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    사용자 로그아웃
    """
    try:
        # 현재는 클라이언트에서 토큰을 삭제하는 방식
        # 추후 토큰 블랙리스트 기능 추가 가능
        
        logger.info(f"User logged out: {request.user.username}")
        return Response({
            'message': '로그아웃되었습니다.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'error': '로그아웃 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user(request):
    """
    현재 사용자 정보 조회
    """
    try:
        user_data = UserSerializer(request.user).data
        return Response({
            'user': user_data,
            'isAuthenticated': True
        })
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return Response({
            'error': '사용자 정보 조회 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_user(request):
    """
    사용자 정보 업데이트
    """
    try:
        user = request.user
        data = request.data
        
        # 사용자 기본 정보 업데이트
        if 'email' in data:
            # 이메일 중복 검사
            if User.objects.filter(email=data['email']).exclude(id=user.id).exists():
                return Response({
                    'error': '이미 사용중인 이메일입니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.email = data['email']
        
        if 'first_name' in data:
            user.first_name = data['first_name']
        
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        user.save()
        
        # 프로필 정보 업데이트
        profile = user.profile
        profile_data = data.get('profile', {})
        
        for field in ['birth_date', 'gender', 'height', 'weight', 
                     'fitness_level', 'fitness_goals', 'diseases', 
                     'allergies', 'preferred_exercises', 'preferred_foods',
                     'workout_days_per_week', 'weekly_workout_goal', 
                     'daily_steps_goal']:
            if field in profile_data:
                setattr(profile, field, profile_data[field])
        
        profile.save()
        
        # 업데이트된 정보 반환
        user_data = UserSerializer(user).data
        
        return Response({
            'user': user_data,
            'message': '정보가 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return Response({
            'error': '사용자 정보 업데이트 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    JWT 토큰 갱신
    """
    try:
        from rest_framework_simplejwt.tokens import RefreshToken
        
        refresh = request.data.get('refresh')
        if not refresh:
            return Response({
                'error': 'Refresh token이 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 새로운 토큰 생성
        token = RefreshToken(refresh)
        
        return Response({
            'access': str(token.access_token),
            'refresh': str(token)
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return Response({
            'error': '토큰 갱신 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Guest login removed - authentication required for all features
