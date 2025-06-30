from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

@csrf_exempt
@require_http_methods(["GET"])
def guest_profile(request):
    """비회원용 기본 프로필 정보"""
    return JsonResponse({
        'user': {
            'id': 'guest',
            'username': '게스트',
            'email': 'guest@example.com',
            'is_guest': True,
            'profile': {
                'age': 0,
                'height': 0,
                'weight': 0,
                'gender': '',
                'exercise_experience': 'beginner',
                'diseases': [],
                'allergies': [],
                'profile_image': None
            }
        },
        'message': '비회원 모드로 이용 중입니다. 로그인하시면 더 많은 기능을 사용할 수 있습니다.'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_routines(request):
    """비회원용 빈 루틴 목록 반환"""
    return Response([], status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_fitness_profile(request):
    """비회원용 기본 피트니스 프로필 반환 - null로 반환"""
    # 게스트는 피트니스 프로필이 없음
    return Response(None, status=status.HTTP_200_OK)
