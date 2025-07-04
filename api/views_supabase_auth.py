"""
Supabase 인증 연동 뷰
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import transaction
from .jwt_auth import create_user_response, get_tokens_for_user
from .serializers import UserSerializer
from .supabase_auth import SupabaseAuthBackend
import requests
import logging
import uuid

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_auth(request):
    """
    Supabase 토큰으로 인증하고 Django 사용자 생성/연동
    """
    try:
        # Supabase 토큰 가져오기
        supabase_token = request.data.get('supabase_token')
        supabase_user = request.data.get('supabase_user')
        
        if not supabase_token or not supabase_user:
            return Response({
                'error': 'Supabase 인증 정보가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Supabase 사용자 정보 추출
        supabase_id = supabase_user.get('id')
        email = supabase_user.get('email')
        user_metadata = supabase_user.get('user_metadata', {})
        
        if not supabase_id or not email:
            return Response({
                'error': '유효하지 않은 Supabase 사용자 정보입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Django 사용자 찾기 또는 생성
        with transaction.atomic():
            try:
                # 이메일로 기존 사용자 찾기
                user = User.objects.get(email=email)
                
                # Supabase ID 연동
                profile = user.profile
                if not profile.supabase_id:
                    profile.supabase_id = supabase_id
                    profile.save()
                
            except User.DoesNotExist:
                # 새 사용자 생성
                username = email.split('@')[0]
                
                # 사용자명 중복 처리
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # 사용자 생성
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None  # Supabase 인증 사용
                )
                
                # 프로필 업데이트
                profile = user.profile
                profile.supabase_id = supabase_id
                
                # Supabase 메타데이터에서 추가 정보 가져오기
                if user_metadata:
                    if 'full_name' in user_metadata:
                        name_parts = user_metadata['full_name'].split(' ', 1)
                        user.first_name = name_parts[0]
                        if len(name_parts) > 1:
                            user.last_name = name_parts[1]
                        user.save()
                    
                    # 프로필 정보 업데이트
                    for field in ['birth_date', 'gender', 'height', 'weight', 
                                 'fitness_level', 'fitness_goals']:
                        if field in user_metadata:
                            setattr(profile, field, user_metadata[field])
                
                profile.save()
                logger.info(f"Created new user from Supabase: {email}")
        
        # Django JWT 토큰 생성
        tokens = get_tokens_for_user(user)
        
        # 응답 생성
        response_data = {
            'access': str(tokens['access']),
            'refresh': str(tokens['refresh']),
            'user': UserSerializer(user).data,
            'isAuthenticated': True,
            'isGuest': False
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Supabase auth error: {str(e)}")
        return Response({
            'error': '인증 처리 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_register(request):
    """
    Supabase에 회원가입하고 Django 사용자 생성
    """
    try:
        from healthwise.settings_supabase import SUPABASE_URL, SUPABASE_ANON_KEY
        
        data = request.data
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')
        profile_data = data.get('profile', {})
        
        if not all([email, password, username]):
            return Response({
                'error': '모든 필드를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Supabase에 회원가입 요청
        supabase_data = {
            'email': email,
            'password': password,
            'data': {
                'username': username,
                **profile_data
            }
        }
        
        headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/signup",
            json=supabase_data,
            headers=headers
        )
        
        if response.status_code != 200:
            error_data = response.json()
            return Response({
                'error': error_data.get('msg', '회원가입에 실패했습니다.')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Supabase 응답에서 사용자 정보 추출
        supabase_response = response.json()
        supabase_user = supabase_response.get('user')
        
        if not supabase_user:
            return Response({
                'error': '회원가입은 성공했으나 사용자 정보를 가져올 수 없습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Django 사용자 생성
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password  # Django에서도 비밀번호 저장
            )
            
            # 프로필 업데이트
            profile = user.profile
            profile.supabase_id = supabase_user['id']
            
            # 프로필 정보 업데이트
            for field in ['birth_date', 'gender', 'height', 'weight', 
                         'fitness_level', 'fitness_goals']:
                if field in profile_data:
                    setattr(profile, field, profile_data[field])
            
            profile.save()
        
        # 응답 생성
        response_data = create_user_response(user)
        
        return Response({
            **response_data,
            'message': '회원가입이 완료되었습니다. 이메일을 확인해주세요.'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Supabase register error: {str(e)}")
        return Response({
            'error': '회원가입 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_login(request):
    """
    Supabase로 로그인하고 Django 토큰 발급
    """
    try:
        from healthwise.settings_supabase import SUPABASE_URL, SUPABASE_ANON_KEY
        
        data = request.data
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return Response({
                'error': '이메일과 비밀번호를 입력해주세요.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Supabase 로그인 요청
        headers = {
            'apikey': SUPABASE_ANON_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            json={
                'email': email,
                'password': password
            },
            headers=headers
        )
        
        if response.status_code != 200:
            return Response({
                'error': '잘못된 로그인 정보입니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Supabase 응답 처리
        supabase_response = response.json()
        access_token = supabase_response.get('access_token')
        user_data = supabase_response.get('user')
        
        if not access_token or not user_data:
            return Response({
                'error': '로그인 처리 중 오류가 발생했습니다.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Django 사용자 찾기 또는 생성
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Supabase에는 있지만 Django에는 없는 경우
            return Response({
                'error': '사용자를 찾을 수 없습니다. 회원가입을 진행해주세요.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Django JWT 토큰 생성
        tokens = get_tokens_for_user(user)
        
        # 응답 생성
        response_data = {
            'access': str(tokens['access']),
            'refresh': str(tokens['refresh']),
            'supabase_token': access_token,
            'user': UserSerializer(user).data,
            'isAuthenticated': True,
            'isGuest': False
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Supabase login error: {str(e)}")
        return Response({
            'error': '로그인 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
