"""
Supabase Authentication Backend for Django
"""
import logging
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import jwt
from supabase import create_client, Client

User = get_user_model()
logger = logging.getLogger(__name__)


class SupabaseClient:
    """Singleton Supabase Client"""
    _instance = None

    @classmethod
    def get_client(cls) -> Client:
        if cls._instance is None:
            cls._instance = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
        return cls._instance


class SupabaseAuthBackend(BaseBackend):
    """
    Django authentication backend for Supabase
    """
    
    def authenticate(self, request, supabase_token=None, supabase_user=None, **kwargs):
        """
        Authenticate user with Supabase token
        """
        if not supabase_token or not supabase_user:
            return None
            
        try:
            # Verify token with Supabase
            client = SupabaseClient.get_client()
            
            # Get or create Django user
            email = supabase_user.get('email')
            supabase_id = supabase_user.get('id')
            
            if not email or not supabase_id:
                return None
                
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': supabase_user.get('user_metadata', {}).get('first_name', ''),
                    'last_name': supabase_user.get('user_metadata', {}).get('last_name', ''),
                }
            )
            
            # Update user's Supabase ID
            if created or not hasattr(user, 'profile'):
                from api.models import Profile
                Profile.objects.get_or_create(
                    user=user,
                    defaults={'supabase_id': supabase_id}
                )
            
            return user
            
        except Exception as e:
            logger.error(f"Supabase authentication error: {e}")
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class SupabaseJWTAuthentication(BaseAuthentication):
    """
    JWT Authentication for Supabase tokens in DRF
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
            
        token = auth_header.split(' ')[1]
        
        try:
            # Decode JWT token
            payload = jwt.decode(
                token,
                settings.SUPABASE_ANON_KEY,
                algorithms=['HS256'],
                audience='authenticated',
                options={"verify_signature": False}  # Supabase uses different signing
            )
            
            # Get user from payload
            user_id = payload.get('sub')
            if not user_id:
                raise AuthenticationFailed('Invalid token')
                
            # Get or create user
            client = SupabaseClient.get_client()
            
            # Try to get user from database first
            try:
                from api.models import Profile
                profile = Profile.objects.get(supabase_id=user_id)
                return (profile.user, token)
            except Profile.DoesNotExist:
                # If not found, verify with Supabase and create
                response = client.auth.get_user(token)
                if response and response.user:
                    email = response.user.email
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={
                            'username': email.split('@')[0],
                        }
                    )
                    
                    Profile.objects.get_or_create(
                        user=user,
                        defaults={'supabase_id': user_id}
                    )
                    
                    return (user, token)
                    
            raise AuthenticationFailed('User not found')
            
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except Exception as e:
            logger.error(f"Supabase JWT authentication error: {e}")
            raise AuthenticationFailed('Authentication failed')
