from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..models import UserProfile
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def auth_csrf(request):
    """CSRF 토큰 가져오기"""
    return Response({'csrfToken': get_token(request)})

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def csrf_failure(request):
    """CSRF 실패 처리"""
    return Response({
        'error': 'CSRF token missing or incorrect',
        'message': 'Please refresh the page and try again'
    }, status=status.HTTP_403_FORBIDDEN)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def auth_login(request):
    """로그인 API - 디버깅 강화"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 요청 데이터 로깅
        username = request.data.get('username')
        password = request.data.get('password')
        
        logger.info(f"Login attempt - username: {username}")
        logger.info(f"Request data keys: {list(request.data.keys())}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        if not username or not password:
            logger.warning("Missing username or password")
            return Response({
                'success': False,
                'error': 'Username and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 이메일로도 로그인 시도
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username
                logger.info(f"Found user by email: {username}")
            except User.DoesNotExist:
                logger.warning(f"No user found with email: {username}")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # 세션 저장 강제
            request.session.save()
            request.session.set_expiry(86400 * 30)  # 30일
            
            # 프로필 확인 및 생성
            try:
                profile = UserProfile.objects.get(user=user)
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)
                logger.info(f"Created profile for user: {user.username}")
            
            response_data = {
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'profile_image': None
                },
                'access': 'authenticated',  # 프론트엔드가 토큰을 기대
                'refresh': 'authenticated',
                'session_key': request.session.session_key,
                'csrf_token': get_token(request)
            }
            
            logger.info(f"Login successful for user: {user.username} (ID: {user.id})")
            logger.info(f"Session key: {request.session.session_key}")
            return Response(response_data)
        else:
            logger.warning(f"Authentication failed for username: {username}")
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def auth_logout(request):
    """로그아웃 API"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 게스트 사용자 확인
    is_guest = request.headers.get('X-Is-Guest') == 'true'
    
    if is_guest:
        # 게스트의 경우 그냥 성공 반환
        return Response({'success': True, 'message': 'Guest logout successful'})
    
    # 일반 사용자 로그아웃
    logout(request)
    return Response({'success': True})

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def auth_register(request):
    """회원가입 API - 디버깅 강화"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        logger.info(f"Register attempt - data: {request.data}")
        
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        # 추가 프로필 정보 (옵션)
        birth_date = request.data.get('birth_date')
        gender = request.data.get('gender')
        height = request.data.get('height')
        weight = request.data.get('weight')
        diseases = request.data.get('diseases', [])
        health_conditions = request.data.get('health_conditions', [])
        allergies = request.data.get('allergies', [])
        fitness_level = request.data.get('fitness_level', 'beginner')
        
        logger.info(f"Register attempt - username: {username}, email: {email}")
        
        if not username or not email or not password:
            logger.warning("Missing required fields")
            return Response({
                'success': False,
                'error': 'Username, email, and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            logger.warning(f"Username already exists: {username}")
            return Response({
                'success': False,
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
            logger.warning(f"Email already exists: {email}")
            return Response({
                'success': False,
                'error': 'Email already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 사용자 생성
        user = User.objects.create_user(username=username, email=email, password=password)
        logger.info(f"User created: {username} (ID: {user.id})")
        
        # 프로필 생성 또는 업데이트
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        profile.fitness_level = fitness_level
        profile.diseases = diseases if isinstance(diseases, list) else []
        profile.health_conditions = health_conditions if isinstance(health_conditions, list) else []
        profile.allergies = allergies if isinstance(allergies, list) else []
        
        if birth_date:
            profile.birth_date = birth_date
        if gender:
            profile.gender = gender
        if height:
            try:
                profile.height = float(height)
            except (ValueError, TypeError):
                logger.warning(f"Invalid height value: {height}")
        if weight:
            try:
                profile.weight = float(weight)
            except (ValueError, TypeError):
                logger.warning(f"Invalid weight value: {weight}")
            
        profile.save()
        logger.info(f"Profile {'created' if created else 'updated'} for user: {username}")
        
        # 자동 로그인
        login(request, user)
        request.session.save()
        request.session.set_expiry(86400 * 30)  # 30일
        
        logger.info(f"Auto login successful for new user: {username}")
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile_image': None
            },
            'access': 'authenticated',
            'refresh': 'authenticated'
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
