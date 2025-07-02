from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from ..models import UserProfile
import logging
import uuid

logger = logging.getLogger(__name__)

@api_view(['GET'])
def guest_profile(request):
    return Response({
        'id': 'guest-123',
        'username': 'guest',
        'email': 'guest@example.com',
        'is_guest': True,
    })

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def guest_login(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 게스트 세션 생성
    guest_id = str(uuid.uuid4())
    
    return Response({
        'success': True,
        'guest_id': guest_id,
        'message': '게스트 모드로 접속했습니다.'
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def auth_csrf(request):
    return Response({'csrfToken': get_token(request)})

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def auth_login(request):
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # request.data를 사용하여 JSON 파싱
        username = request.data.get('username')
        password = request.data.get('password')
        
        # 디버깅을 위한 로그
        print(f"Login attempt - username: {username}")
        
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
            return Response({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'profile_image': None  # 프론트엔드가 기대하는 필드
                },
                'access': 'dummy-token',  # 프론트엔드가 토큰을 기대할 수 있음
                'refresh': 'dummy-refresh-token'
            })
        else:
            return Response({
                'success': False,
                'error': 'Invalid credentials'
            }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print(f"Login error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])  # 게스트도 로그아웃 가능하도록 변경
def auth_logout(request):
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
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # request.data 사용 (DRF 표준)
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
        
        print(f"Register attempt - username: {username}, email: {email}")
        
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
        
        # 사용자 생성 (신호에서 UserProfile 자동 생성됨)
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # 프로필 업데이트 (이미 생성된 프로필을 가져와서 업데이트)
        profile = user.profile  # 신호에서 자동 생성된 프로필
        
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
        
        # 자동 로그인
        login(request, user)
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'profile_image': None
            },
            'access': 'dummy-token',
            'refresh': 'dummy-refresh-token'
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
