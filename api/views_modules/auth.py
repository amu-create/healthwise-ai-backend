from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from api.models import UserProfile
import logging

logger = logging.getLogger(__name__)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def auth_login(request):
    """로그인 API - 개선된 버전"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        username = request.data.get('username')
        password = request.data.get('password')
        
        logger.info(f"Login attempt - username: {username}")
        
        # 이메일로도 로그인 시도
        if '@' in username:
            try:
                user_obj = User.objects.get(email=username)
                username = user_obj.username
            except User.DoesNotExist:
                pass
        
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
            return Response(response_data)
        else:
            logger.warning(f"Login failed for username: {username}")
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
def auth_register(request):
    """회원가입 API - 개선된 버전"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        # 추가 프로필 정보
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
            return Response({
                'success': False,
                'error': 'Username, email, and password are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'error': 'Username already exists'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(email=email).exists():
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
        profile.diseases = diseases
        profile.health_conditions = health_conditions
        profile.allergies = allergies
        
        if birth_date:
            profile.birth_date = birth_date
        if gender:
            profile.gender = gender
        if height:
            profile.height = float(height)
        if weight:
            profile.weight = float(weight)
            
        profile.save()
        logger.info(f"Profile {'created' if created else 'updated'} for user: {username}")
        
        # 자동 로그인
        login(request, user)
        request.session.save()
        request.session.set_expiry(86400 * 30)  # 30일
        
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
