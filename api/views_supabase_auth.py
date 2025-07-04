"""
Supabase Authentication Views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db import transaction
from .jwt_auth import create_user_response
from .serializers import UserSerializer
from .supabase_auth import SupabaseClient
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_auth(request):
    """
    Supabase 토큰으로 Django 인증
    """
    try:
        supabase_token = request.data.get('supabase_token')
        supabase_user = request.data.get('supabase_user')
        
        if not supabase_token or not supabase_user:
            return Response({
                'error': 'Supabase 인증 정보가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Supabase 사용자 정보로 Django 사용자 생성/업데이트
        email = supabase_user.get('email')
        supabase_id = supabase_user.get('id')
        
        if not email or not supabase_id:
            return Response({
                'error': '유효하지 않은 Supabase 사용자 정보입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Django 사용자 가져오기 또는 생성
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': supabase_user.get('user_metadata', {}).get('first_name', ''),
                'last_name': supabase_user.get('user_metadata', {}).get('last_name', ''),
            }
        )
        
        # 프로필에 Supabase ID 저장
        from .models import UserProfile
        profile = user.profile
        profile.supabase_id = supabase_id
        profile.save()
        
        # JWT 토큰 생성하여 반환
        response_data = create_user_response(user)
        
        if created:
            logger.info(f"New user created from Supabase: {email}")
        else:
            logger.info(f"User authenticated from Supabase: {email}")
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Supabase auth error: {str(e)}")
        return Response({
            'error': 'Supabase 인증 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def supabase_register(request):
    """
    Supabase로 회원가입한 사용자를 Django에 등록
    """
    try:
        data = request.data
        supabase_id = data.get('supabase_id')
        email = data.get('email')
        username = data.get('username')
        
        if not all([supabase_id, email, username]):
            return Response({
                'error': '필수 정보가 누락되었습니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Django 사용자 생성
        with transaction.atomic():
            # 이메일로 기존 사용자 확인
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
            else:
                # 사용자명 중복 처리
                if User.objects.filter(username=username).exists():
                    username = f"{username}_{supabase_id[:8]}"
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=None  # Supabase로 인증하므로 Django 비밀번호 불필요
                )
            
            # 프로필 업데이트
            from .models import UserProfile
            profile = user.profile
            profile.supabase_id = supabase_id
            
            # 추가 프로필 정보가 있으면 업데이트
            profile_data = data.get('profile', {})
            for field in ['birth_date', 'gender', 'height', 'weight', 
                         'fitness_level', 'fitness_goals']:
                if field in profile_data:
                    setattr(profile, field, profile_data[field])
            
            profile.save()
        
        # JWT 토큰 생성하여 반환
        response_data = create_user_response(user)
        logger.info(f"User registered via Supabase: {username}")
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Supabase register error: {str(e)}")
        return Response({
            'error': '회원가입 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
