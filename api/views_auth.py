"""
인증 관련 뷰 - 로그인 문제 해결 버전 (username/email 자동 감지)
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from .jwt_auth import create_user_response, authenticate_user, get_tokens_for_user
from .serializers import UserSerializer
import logging
import re

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    사용자 회원가입
    """
    try:
        data = request.data
        logger.info(f"Registration attempt with data: {list(data.keys())}")
        
        # 필수 필드 검증
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            logger.warning("Registration failed: Missing required fields")
            return Response({
                'success': False,
                'error': '모든 필드를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 중복 검사
        if User.objects.filter(username=username).exists():
            logger.warning(f"Registration failed: Username {username} already exists")
            return Response({
                'success': False,
                'error': '이미 사용중인 사용자명입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            logger.warning(f"Registration failed: Email {email} already exists")
            return Response({
                'success': False,
                'error': '이미 사용중인 이메일입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 사용자 생성
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            logger.info(f"User created: {username}")
            
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
                logger.info(f"Profile updated for user: {username}")
        
        # 응답 생성
        response_data = create_user_response(user)
        response_data['success'] = True  # 중요: 프론트엔드가 기대하는 success 필드
        logger.info(f"User registered successfully: {username}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return Response({
            'success': False,
            'error': '회원가입 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def is_email(text):
    """이메일 형식인지 확인"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, text) is not None


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    사용자 로그인 - username/email 자동 감지 버전
    """
    try:
        data = request.data
        logger.info(f"Login attempt with data keys: {list(data.keys())}")
        
        # 로그인 정보 추출
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        logger.info(f"Login attempt - username: {username}, email: {email}")
        
        if not password:
            logger.warning("Login failed: No password provided")
            return Response({
                'success': False,
                'error': '비밀번호를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not (username or email):
            logger.warning("Login failed: No username or email provided")
            return Response({
                'success': False,
                'error': '사용자명 또는 이메일을 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # === 스마트 이메일/사용자명 감지 ===
        # username 필드에 이메일이 들어온 경우 자동으로 이메일로 처리
        if username and is_email(username) and not email:
            logger.info(f"Detected email in username field: {username}")
            email = username
            username = None
        
        # === 강화된 디버깅 섹션 ===
        logger.info(f"After auto-detection - username: {username}, email: {email}")
        logger.info(f"Password length: {len(password)}")
        logger.info(f"Password starts with: {password[:3]}..." if len(password) > 3 else f"Password: {password}")
        
        # 1. 사용자 존재 확인
        target_user = None
        if email:
            try:
                target_user = User.objects.get(email=email)
                logger.info(f"Found user by email: {target_user.username} (ID: {target_user.id})")
            except User.DoesNotExist:
                logger.warning(f"No user found with email: {email}")
                return Response({
                    'success': False,
                    'error': '잘못된 로그인 정보입니다.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        elif username:
            try:
                target_user = User.objects.get(username=username)
                logger.info(f"Found user by username: {target_user.username} (ID: {target_user.id})")
            except User.DoesNotExist:
                logger.warning(f"No user found with username: {username}")
                return Response({
                    'success': False,
                    'error': '잘못된 로그인 정보입니다.'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not target_user:
            logger.error("No target user found - this should not happen")
            return Response({
                'success': False,
                'error': '잘못된 로그인 정보입니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 2. 사용자 상태 확인
        logger.info(f"User active status: {target_user.is_active}")
        logger.info(f"User password hash preview: {target_user.password[:50]}...")
        
        # 3. 직접 비밀번호 검증
        password_valid = target_user.check_password(password)
        logger.info(f"Direct password check result: {password_valid}")
        
        # 4. Django authenticate 함수 테스트
        auth_user = authenticate(username=target_user.username, password=password)
        logger.info(f"Django authenticate result: {auth_user}")
        logger.info(f"Django authenticate success: {auth_user is not None}")
        
        # 실제 인증 결과 결정
        if password_valid and target_user.is_active:
            logger.info("Using direct password validation - SUCCESS")
            user = target_user
        else:
            logger.warning("Authentication failed - password or user inactive")
            return Response({
                'success': False,
                'error': '잘못된 로그인 정보입니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # 응답 생성
        response_data = create_user_response(user)
        response_data['success'] = True  # 중요: 프론트엔드가 기대하는 success 필드
        logger.info(f"User logged in successfully: {user.username}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(f"Login error type: {type(e)}")
        import traceback
        logger.error(f"Login error traceback: {traceback.format_exc()}")
        return Response({
            'success': False,
            'error': '로그인 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    사용자 로그아웃
    """
    try:
        logger.info(f"User logged out: {request.user.username}")
        return Response({
            'success': True,
            'message': '로그아웃되었습니다.'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'success': False,
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
            'success': True,
            'user': user_data,
            'isAuthenticated': True
        })
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return Response({
            'success': False,
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
                    'success': False,
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
            'success': True,
            'user': user_data,
            'message': '정보가 업데이트되었습니다.'
        })
        
    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return Response({
            'success': False,
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
                'success': False,
                'error': 'Refresh token이 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 새로운 토큰 생성
        token = RefreshToken(refresh)
        
        return Response({
            'success': True,
            'access': str(token.access_token),
            'refresh': str(token)
        })
        
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return Response({
            'success': False,
            'error': '토큰 갱신 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
