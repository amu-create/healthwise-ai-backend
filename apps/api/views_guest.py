from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.sessions.models import Session
from django.utils import timezone
import uuid


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_token(request):
    """
    비회원을 위한 게스트 토큰 발급
    세션 기반으로 임시 사용자 식별
    """
    # 세션에 게스트 ID가 있는지 확인
    guest_id = request.session.get('guest_id')
    
    if not guest_id:
        # 새로운 게스트 ID 생성
        guest_id = str(uuid.uuid4())
        request.session['guest_id'] = guest_id
        request.session['is_guest'] = True
        request.session['created_at'] = timezone.now().isoformat()
        
        # 세션 만료 시간 설정 (7일)
        request.session.set_expiry(60 * 60 * 24 * 7)
    
    return Response({
        'guest_id': guest_id,
        'is_guest': True,
        'features': {
            'exercise_list': True,
            'workout_videos': True,
            'basic_recommendations': True,
            'chat': False,  # 채팅은 회원만
            'profile': False,  # 프로필은 회원만
            'workout_log': False,  # 운동 기록은 회원만
            'nutrition_analysis': False,  # 영양 분석은 회원만
        },
        'message': '게스트로 이용 중입니다. 더 많은 기능을 이용하려면 회원가입을 해주세요.'
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def check_auth_status(request):
    """
    현재 사용자의 인증 상태 확인
    """
    if request.user.is_authenticated:
        return Response({
            'is_authenticated': True,
            'is_guest': False,
            'user': {
                'id': request.user.id,
                'email': request.user.email,
                'username': request.user.username,
            },
            'features': {
                'exercise_list': True,
                'workout_videos': True,
                'basic_recommendations': True,
                'chat': True,
                'profile': True,
                'workout_log': True,
                'nutrition_analysis': True,
            }
        })
    else:
        guest_id = request.session.get('guest_id')
        return Response({
            'is_authenticated': False,
            'is_guest': bool(guest_id),
            'guest_id': guest_id,
            'features': {
                'exercise_list': True,
                'workout_videos': True,
                'basic_recommendations': True,
                'chat': False,
                'profile': False,
                'workout_log': False,
                'nutrition_analysis': False,
            },
            'message': '로그인하면 모든 기능을 이용할 수 있습니다.'
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def guest_recommendations(request):
    """
    비회원을 위한 기본 추천
    """
    # 기본 운동 추천
    basic_recommendations = {
        'workout': {
            'title': '초보자를 위한 전신 운동',
            'description': '운동을 시작하는 분들을 위한 기본 전신 운동 루틴입니다.',
            'details': {
                'duration': '20분',
                'intensity': '낮음',
                'exercises': [
                    '워밍업 스트레칭 (5분)',
                    '스쿼트 10회 x 3세트',
                    '팔굽혀펴기 10회 x 3세트',
                    '플랭크 30초 x 3세트',
                    '쿨다운 스트레칭 (5분)'
                ]
            },
            'reasoning': '운동 초보자에게 적합한 기본 운동으로 구성했습니다.'
        },
        'diet': {
            'title': '균형잡힌 하루 식단',
            'description': '건강한 하루를 위한 균형잡힌 식단 구성입니다.',
            'details': {
                'breakfast': ['통곡물 시리얼', '우유', '과일'],
                'lunch': ['현미밥', '구운 닭가슴살', '샐러드'],
                'dinner': ['잡곡밥', '생선구이', '나물반찬'],
                'snack': ['견과류', '요거트']
            },
            'reasoning': '탄수화물, 단백질, 지방의 균형을 맞춘 건강한 식단입니다.'
        },
        'is_guest': True,
        'upgrade_message': '회원가입하시면 맞춤형 추천을 받을 수 있습니다!'
    }
    
    return Response(basic_recommendations)


@api_view(['POST'])
@permission_classes([AllowAny])
def convert_guest_to_member(request):
    """
    게스트 데이터를 회원 계정으로 전환
    """
    if not request.user.is_authenticated:
        return Response({
            'error': '로그인이 필요합니다.'
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    guest_id = request.session.get('guest_id')
    if not guest_id:
        return Response({
            'message': '전환할 게스트 데이터가 없습니다.'
        })
    
    # TODO: 게스트 데이터가 있다면 회원 계정으로 마이그레이션
    # 예: 임시 저장된 운동 기록, 선호도 등
    
    # 게스트 세션 정보 삭제
    request.session.pop('guest_id', None)
    request.session.pop('is_guest', None)
    request.session.pop('created_at', None)
    
    return Response({
        'message': '게스트 데이터가 회원 계정으로 전환되었습니다.',
        'user_id': request.user.id
    })
