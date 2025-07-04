"""
Supabase Authentication Backend for Django
"""

import jwt
import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.conf import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class SupabaseAuthBackend(BaseBackend):
    """
    Django authentication backend that validates Supabase JWT tokens
    """
    
    def __init__(self):
        # Supabase 설정 가져오기
        try:
            from healthwise.settings_supabase import (
                SUPABASE_URL, 
                SUPABASE_ANON_KEY, 
                SUPABASE_JWT_SECRET
            )
            self.supabase_url = SUPABASE_URL
            self.supabase_anon_key = SUPABASE_ANON_KEY
            self.jwt_secret = SUPABASE_JWT_SECRET
        except ImportError:
            logger.warning("Supabase settings not found")
            self.supabase_url = None
            self.supabase_anon_key = None
            self.jwt_secret = None
    
    def authenticate(self, request, token=None, **kwargs):
        """
        Authenticate user using Supabase JWT token
        """
        if not token or not self.jwt_secret:
            return None
        
        try:
            # JWT 토큰 검증
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=['HS256'],
                audience='authenticated'
            )
            
            # Supabase user ID 가져오기
            sub = payload.get('sub')
            if not sub:
                logger.error("No 'sub' in JWT payload")
                return None
            
            # Supabase에서 사용자 정보 가져오기
            user_data = self._get_supabase_user(sub, token)
            if not user_data:
                return None
            
            # Django User 생성 또는 업데이트
            user = self._get_or_create_user(sub, user_data)
            
            return user
            
        except jwt.ExpiredSignatureError:
            logger.error("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    def _get_supabase_user(self, user_id: str, token: str) -> Optional[dict]:
        """
        Get user data from Supabase
        """
        if not self.supabase_url:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {token}',
                'apikey': self.supabase_anon_key
            }
            
            # Supabase Auth Admin API 호출
            response = requests.get(
                f"{self.supabase_url}/auth/v1/user",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get user from Supabase: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching Supabase user: {e}")
            return None
    
    def _get_or_create_user(self, supabase_id: str, user_data: dict) -> User:
        """
        Get or create Django user from Supabase user data
        """
        email = user_data.get('email', '')
        user_metadata = user_data.get('user_metadata', {})
        
        # username 생성 (email의 @ 앞부분 사용)
        username = email.split('@')[0] if email else f'user_{supabase_id[:8]}'
        
        # Django User 찾기 또는 생성
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'first_name': user_metadata.get('first_name', ''),
                'last_name': user_metadata.get('last_name', ''),
                'is_active': True,
            }
        )
        
        # Supabase ID 저장 (profile에)
        if hasattr(user, 'profile'):
            profile = user.profile
            if not hasattr(profile, 'supabase_id'):
                # profile 모델에 supabase_id 필드 추가 필요
                pass
        else:
            # Profile 생성
            from api.models import UserProfile
            UserProfile.objects.get_or_create(user=user)
        
        if created:
            logger.info(f"Created new user from Supabase: {email}")
        
        return user
    
    def get_user(self, user_id):
        """
        Required method for Django auth backend
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SupabaseJWTAuthentication:
    """
    DRF Authentication class for Supabase JWT
    """
    
    def __init__(self):
        self.backend = SupabaseAuthBackend()
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        user = self.backend.authenticate(request, token=token)
        
        if user:
            return (user, token)
        
        return None
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer'
