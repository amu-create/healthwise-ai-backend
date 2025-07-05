# AI 운동 관련 엔드포인트
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime
import random
import json
import logging

from ..ai_service import get_chatbot
from ..models import WorkoutRoutine, Exercise, RoutineExercise
from .workout_constants import (
    VALID_EXERCISES_WITH_GIF, VALID_EXERCISES_BY_GROUP, 
    EXERCISES_BY_LEVEL
)

logger = logging.getLogger(__name__)


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def ai_workout_recommendation(request):
    """AI 운동 추천"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        # 사용자 정보 수집
        user_data = {
            'user_id': request.user.id if request.user.is_authenticated else 'guest',
            'username': request.user.username if request.user.is_authenticated else 'Guest',
        }
        
        # 요청 데이터
        data = request.data
        user_data.update({
            'goal': data.get('goal', '체중 감량'),
            'experience': data.get('experience', '초급'),
        })
        
        # 프로필 정보 추가
        if request.user.is_authenticated and hasattr(request.user, 'profile'):
            profile = request.user.profile
            user_data.update({
                'birth_date': profile.birth_date,
                'gender': profile.gender,
                'height': profile.height,
                'weight': profile.weight,
                'fitness_level': profile.fitness_level
            })
        
        # AI 챗봇 사용
        chatbot = get_chatbot()
        result = chatbot.generate_workout_recommendation(user_data)
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'error': f'Workout recommendation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def select_exercises_for_routine(muscle_group, level, duration, equipment_available, is_guest):
    """루틴을 위한 운동 선택"""
    # 유효한 운동 목록 가져오기
    if muscle_group == "전신":
        # 전신 운동인 경우 각 부위에서 골고루 선택
        if level == "초급":
            available_exercises = ["체스트프레스 머신", "랫풀다운", "레그프레스", "숄더프레스 머신", "덤벨 컬"]
        else:  # 중급
            available_exercises = ["덤벨 체스트 프레스", "바벨로우", "바벨스쿼트", "밀리터리 프레스", "해머컬"]
    elif muscle_group == "복근":
        # 복근은 GIF가 있는 운동이 없으므로 다른 부위 운동으로 대체
        available_exercises = ["런지", "레그익스텐션", "레그컬"]
    elif muscle_group in EXERCISES_BY_LEVEL.get(level, {}):
        available_exercises = EXERCISES_BY_LEVEL[level][muscle_group]
    elif muscle_group in VALID_EXERCISES_BY_GROUP:
        available_exercises = VALID_EXERCISES_BY_GROUP[muscle_group][:5] if is_guest else VALID_EXERCISES_BY_GROUP[muscle_group]
    else:
        # 기본값
        available_exercises = ["체스트프레스 머신", "랫풀다운", "레그프레스"]
    
    # 장비가 없는 경우 맨몸 운동만 선택
    if not equipment_available:
        bodyweight_exercises = ["인클라인 푸시업", "풀업", "런지", "삼두(맨몸)"]
        available_exercises = [ex for ex in available_exercises if ex in bodyweight_exercises]
        
        # 맨몸 운동이 부족한 경우 추가
        if len(available_exercises) < 3:
            available_exercises = ["인클라인 푸시업", "런지", "삼두(맨몸)"]
    
    # 운동 시간에 따른 운동 개수 결정
    if duration <= 30:
        num_exercises = 3
    else:
        num_exercises = min(4 if is_guest else 6, (duration // 15))
    
    # 운동 선택 (중복 제거)
    selected_exercises = []
    used_exercises = set()
    
    for exercise_name in available_exercises:
        if exercise_name not in used_exercises:
            selected_exercises.append(exercise_name)
            used_exercises.add(exercise_name)
            if len(selected_exercises) >= num_exercises:
                break
    
    # 운동이 부족한 경우 다른 운동 추가
    if len(selected_exercises) < num_exercises:
        # 같은 근육군의 다른 운동들 추가
        if muscle_group in VALID_EXERCISES_BY_GROUP:
            for ex in VALID_EXERCISES_BY_GROUP[muscle_group]:
                if ex not in used_exercises and len(selected_exercises) < num_exercises:
                    selected_exercises.append(ex)
                    used_exercises.add(ex)
        
        # 그래도 부족하면 전체 운동에서 추가
        if len(selected_exercises) < num_exercises:
            all_exercises = list(VALID_EXERCISES_WITH_GIF.keys())
            random.shuffle(all_exercises)
            for ex in all_exercises:
                if ex not in used_exercises and len(selected_exercises) < num_exercises:
                    selected_exercises.append(ex)
                    used_exercises.add(ex)
    
    return selected_exercises, num_exercises


def generate_routine_with_ai(selected_exercises, muscle_group, level, duration, equipment_available):
    """AI를 사용한 루틴 생성"""
    chatbot = get_chatbot()
    exercises_list = ", ".join(selected_exercises)
    
    prompt = f"""
    운동 루틴을 생성해주세요.
    - 운동 대상 부위: {muscle_group}
    - 운동 난이도: {level}
    - 운동 시간: {duration}분
    - 장비 사용 가능: {'예' if equipment_available else '아니오'}
    - 사용 가능한 운동: {exercises_list}
    
    각 운동마다 세트, 반복 횟수, 휴식 시간을 포함해서 알려주세요.
    난이도에 맞게 세트수와 반복수를 조절하세요:
    - 초급: 3세트, 10-12회
    - 중급: 3-4세트, 8-12회
    - 상급: 4-5세트, 6-10회
    
    JSON 형식으로 답변해주세요:
    {{
        "routine_name": "루틴 이름",
        "exercises": [
            {{
                "name": "운동 이름",
                "sets": 세트 수,
                "reps": 반복 횟수,
                "rest_seconds": 휴식 시간(초),
                "notes": "수행 팁"
            }}
        ],
        "total_duration": 예상 시간
    }}
    """
    
    try:
        # AI 응답 받기
        logger.info("Calling AI chatbot for workout generation...")
        response = chatbot.get_health_consultation(
            user_data={'user_id': 'ai_workout'},
            question=prompt
        )
        
        # 응답 성공 여부 확인
        if not response.get('success', False):
            logger.warning(f"AI response failed: {response.get('error', 'Unknown error')}")
            raise ValueError(f"AI response failed: {response.get('error', 'Unknown error')}")
        
        # JSON 파싱 시도
        content = response.get('response', '')
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()
        
        routine_data = json.loads(content)
        return routine_data
        
    except Exception as e:
        logger.info(f"Using fallback routine due to: {str(e)}")
        # AI 실패 시 기본 루틴 생성
        routine_data = {
            "routine_name": f"{muscle_group} {level} 루틴",
            "exercises": [],
            "total_duration": duration
        }
        
        # 기본 세트/반복수 설정
        if level == "초급":
            sets, reps = 3, 12
        else:  # 중급
            sets, reps = 3, 10
        
        for exercise_name in selected_exercises:
            routine_data["exercises"].append({
                "name": exercise_name,
                "sets": sets,
                "reps": reps,
                "rest_seconds": 60 if level == "초급" else 75,
                "notes": "정확한 자세로 천천히 수행하세요"
            })
        
        return routine_data


def save_routine_to_db(request, routine_data, muscle_group, level, duration):
    """루틴을 DB에 저장"""
    try:
        logger.info(f"Attempting to save routine for user: {request.user.id} ({request.user.username})")
        
        # difficulty 변환 (한글 -> 영어)
        difficulty_map = {
            '초급': 'beginner',
            '중급': 'intermediate', 
            '상급': 'advanced',
            'beginner': 'beginner',
            'intermediate': 'intermediate',
            'advanced': 'advanced'
        }
        difficulty_english = difficulty_map.get(level, 'intermediate')
        
        # WorkoutRoutine 생성
        saved_routine = WorkoutRoutine.objects.create(
            user=request.user,
            name=routine_data.get('routine_name', f'{muscle_group} {level} 루틴'),
            description=f"AI가 생성한 {muscle_group} 운동 루틴 ({level})",
            total_duration=safe_duration_convert(routine_data.get('total_duration', duration)),
            difficulty=difficulty_english,
            is_public=False
        )
        
        logger.info(f"Created WorkoutRoutine with ID: {saved_routine.id}")
        
        # 각 운동을 RoutineExercise로 저장
        for idx, exercise_data in enumerate(routine_data.get('exercises', [])):
            exercise_name = exercise_data.get('name', '')
            
            # 유효한 운동인지 확인
            if exercise_name in VALID_EXERCISES_WITH_GIF:
                # difficulty 변환
                if level == '초급':
                    difficulty = 'easy'
                elif level == '중급':
                    difficulty = 'medium'
                else:
                    difficulty = 'hard'
                
                # Exercise 찾기 또는 생성
                exercise, created = Exercise.objects.get_or_create(
                    name=exercise_name,
                    defaults={
                        'category': muscle_group,
                        'description': f'{muscle_group} 운동',
                        'instructions': exercise_data.get('notes', '정확한 자세로 천천히 수행하세요'),
                        'duration': 5,  # 기본값
                        'calories_per_minute': 8.0,
                        'difficulty': difficulty,
                        'muscle_groups': [muscle_group]
                    }
                )
                
                if created:
                    logger.info(f"Created new Exercise: {exercise_name}")
                
                # duration과 rest_time 안전하게 변환
                duration_value = safe_duration_convert(exercise_data.get('duration', 5))
                rest_time_value = safe_duration_convert(exercise_data.get('rest_seconds', 60))
                
                # RoutineExercise 생성
                routine_exercise = RoutineExercise.objects.create(
                    routine=saved_routine,
                    exercise=exercise,
                    sets=int(exercise_data.get('sets', 3)),
                    reps=int(exercise_data.get('reps', 12)),
                    duration=duration_value,
                    rest_time=rest_time_value,
                    order=idx
                )
                logger.info(f"Created RoutineExercise: {exercise_name} for routine {saved_routine.id}")
        
        logger.info(f"AI 루틴 DB 저장 완료: {saved_routine.id} with {saved_routine.exercises.count()} exercises")
        return saved_routine
        
    except Exception as e:
        logger.error(f"AI 루틴 DB 저장 실패: {str(e)}", exc_info=True)
        return None


@api_view(['POST', 'OPTIONS'])
@permission_classes([AllowAny])
def ai_workout(request):
    """AI 운동 루틴 생성"""
    if request.method == 'OPTIONS':
        return Response(status=status.HTTP_200_OK)
    
    try:
        logger.info(f"AI workout request received: {request.data}")
        
        data = request.data
        muscle_group = data.get('muscle_group', '전신')
        level = data.get('level', '초급')
        duration = data.get('duration', 30)
        equipment_available = data.get('equipment_available', True)
        specific_goals = data.get('specific_goals', '')
        
        # 게스트 사용자인지 확인
        is_guest = not request.user.is_authenticated
        
        # 게스트는 초급, 중급만 이용 가능
        if is_guest and level == "상급":
            level = "중급"
        
        # 운동 선택
        selected_exercises, num_exercises = select_exercises_for_routine(
            muscle_group, level, duration, equipment_available, is_guest
        )
        
        # AI를 사용한 루틴 생성
        routine_data = generate_routine_with_ai(
            selected_exercises[:num_exercises], muscle_group, level, duration, equipment_available
        )
        
        # 루틴 데이터 준비
        exercises_with_details = []
        added_exercises = set()
        
        for exercise_data in routine_data['exercises']:
            exercise_name = exercise_data['name']
            
            # 유효한 운동인지 확인 및 중복 체크
            if exercise_name not in VALID_EXERCISES_WITH_GIF or exercise_name in added_exercises:
                continue
            
            exercise_info = VALID_EXERCISES_WITH_GIF[exercise_name]
            added_exercises.add(exercise_name)
            
            exercises_with_details.append({
                'id': len(exercises_with_details) + 1,
                'exercise': {
                    'id': len(exercises_with_details) + 1,
                    'name': exercise_name,
                    'muscle_group': exercise_info['muscle_group'],
                    'gif_url': exercise_info['gif_url'],
                    'default_sets': exercise_data['sets'],
                    'default_reps': exercise_data['reps'],
                    'exercise_type': 'strength',
                    'description': f'{exercise_name} 운동'
                },
                'order': len(exercises_with_details) + 1,
                'sets': exercise_data['sets'],
                'reps': exercise_data['reps'],
                'recommended_weight': None,
                'notes': exercise_data.get('notes', '정확한 자세로 천천히 수행하세요')
            })
        
        # DB에 루틴 저장 (로그인 사용자만)
        saved_routine = None
        if request.user.is_authenticated:
            saved_routine = save_routine_to_db(request, routine_data, muscle_group, level, duration)
        
        # AI 생성 루틴 객체
        if saved_routine:
            # DB에 저장된 경우 실제 ID 사용
            routine = {
                'id': saved_routine.id,
                'name': saved_routine.name,
                'exercises': exercises_with_details,
                'level': level,
                'total_duration': saved_routine.total_duration,
                'is_ai_generated': True,
                'created_at': saved_routine.created_at.isoformat(),
                'updated_at': saved_routine.updated_at.isoformat(),
                'is_guest': False,
                'is_saved': True
            }
        else:
            # 게스트이거나 저장 실패시 임시 ID 사용
            routine = {
                'id': f'temp_{random.randint(1000, 9999)}',
                'name': routine_data['routine_name'],
                'exercises': exercises_with_details,
                'level': level,
                'total_duration': routine_data.get('total_duration', duration),
                'is_ai_generated': True,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'is_guest': is_guest,
                'is_saved': False
            }
        
        response_data = {
            'success': True,
            'routine': routine,
            'estimated_duration': routine_data.get('total_duration', duration)
        }
        
        if is_guest:
            response_data['guest_info'] = {
                'message': '더 많은 기능을 원하시면 회원가입을 해주세요.',
                'limited_features': ['초급, 중급 운동만 이용 가능', '최대 4개 운동까지 추천']
            }
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f'AI workout error: {str(e)}', exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
            'message': 'AI 운동 루틴 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
