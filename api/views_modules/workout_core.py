# 기본 운동 관련 엔드포인트
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import logging

from ..services.data import EXERCISE_DATA, ROUTINE_DATA
from ..services.youtube_service import get_workout_videos
from ..models import WorkoutRoutine
from .workout_utils import convert_routine_to_frontend_format

logger = logging.getLogger(__name__)

@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def exercise_list(request):
    """운동 목록 조회"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    category = request.GET.get('category', '')
    difficulty = request.GET.get('difficulty', '')
    
    exercises = EXERCISE_DATA.copy()
    
    if category:
        exercises = [e for e in exercises if e['category'] == category]
    if difficulty:
        exercises = [e for e in exercises if e['difficulty'] == difficulty]
        
    return Response({'count': len(exercises), 'results': exercises})


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_routines(request):
    """운동 루틴 목록 조회"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    # 기본 루틴 데이터
    routines = ROUTINE_DATA.copy()
    
    # 로그인 사용자의 경우 DB에서 저장된 루틴도 가져오기
    if request.user.is_authenticated:
        try:
            # 사용자의 루틴 가져오기
            user_routines = WorkoutRoutine.objects.filter(
                user=request.user
            ).prefetch_related('exercises', 'routineexercise_set').order_by('-created_at')
            
            # DB 루틴을 프론트엔드 형식으로 변환
            for routine in user_routines:
                routine_data = convert_routine_to_frontend_format(routine)
                # 사용자 루틴을 목록 앞에 추가
                routines.insert(0, routine_data)
                
            logger.info(f"Found {len(user_routines)} saved routines for user {request.user.id}")
            
        except Exception as e:
            logger.error(f"Error loading user routines: {str(e)}")
    
    # 프론트엔드가 배열을 기대하므로 배열로 반환
    return Response(routines)


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_videos(request):
    """운동 비디오 조회"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    exercise_type = request.GET.get('type', 'general')
    difficulty = request.GET.get('difficulty', 'beginner')
    result = get_workout_videos(exercise_type, difficulty)
    
    if 'error' in result:
        return Response(result, status=status.HTTP_502_BAD_GATEWAY)
    return Response(result)


@api_view(['GET', 'OPTIONS'])
@permission_classes([AllowAny])
def workout_videos_list(request):
    """운동 비디오 목록 조회"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    search = request.GET.get('search', '')
    category = request.GET.get('category', 'all')
    
    # 유튜브 운동 비디오 검색
    if search:
        result = get_workout_videos(search, category)
    else:
        # 기본 운동 비디오 목록
        result = get_workout_videos('workout', category)
    
    if 'error' in result:
        return Response(result, status=status.HTTP_502_BAD_GATEWAY)
    
    return Response(result)
