"""
디버깅용 뷰 - 개발 환경에서만 사용
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def debug_create_user(request):
    """
    디버깅용 사용자 생성 - 올바른 비밀번호 해시 사용
    """
    try:
        username = request.data.get('username', 'testuser')
        email = request.data.get('email', 'test@test.com')
        password = request.data.get('password', 'test123')
        
        # 기존 사용자 삭제
        User.objects.filter(email=email).delete()
        User.objects.filter(username=username).delete()
        
        # 새 사용자 생성
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),  # 올바른 해시 생성
            is_active=True
        )
        
        logger.info(f"Created debug user: {username} with email: {email}")
        
        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            },
            'password_hash': user.password[:50] + '...',  # 해시 일부만 표시
            'message': f'User {username} created successfully'
        })
        
    except Exception as e:
        logger.error(f"Debug user creation error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def debug_test_auth(request):
    """
    인증 테스트 - 사용자 존재 여부와 비밀번호 확인
    """
    try:
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        # 사용자 검색
        user = None
        if email:
            try:
                user = User.objects.get(email=email)
                logger.info(f"Found user by email: {user.username}")
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'No user found with email: {email}'
                })
        elif username:
            try:
                user = User.objects.get(username=username)
                logger.info(f"Found user by username: {user.username}")
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'No user found with username: {username}'
                })
        
        if not user:
            return Response({
                'success': False,
                'error': 'No username or email provided'
            })
        
        # 비밀번호 확인
        password_valid = user.check_password(password)
        
        # Django authenticate 함수 테스트
        auth_user = authenticate(username=user.username, password=password)
        
        return Response({
            'success': True,
            'user_found': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_active': user.is_active,
            'password_valid': password_valid,
            'auth_successful': auth_user is not None,
            'password_hash_preview': user.password[:50] + '...'
        })
        
    except Exception as e:
        logger.error(f"Debug auth test error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def debug_reset_password(request):
    """
    사용자 비밀번호 재설정
    """
    try:
        email = request.data.get('email')
        new_password = request.data.get('password', 'test123')
        
        if not email:
            return Response({
                'success': False,
                'error': 'Email required'
            })
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': f'No user found with email: {email}'
            })
        
        # 비밀번호 업데이트
        user.set_password(new_password)
        user.save()
        
        logger.info(f"Password updated for user: {user.username}")
        
        # 비밀번호 확인 테스트
        test_check = user.check_password(new_password)
        
        return Response({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'new_password': new_password,
            'password_test': test_check,
            'message': 'Password updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Debug password reset error: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
