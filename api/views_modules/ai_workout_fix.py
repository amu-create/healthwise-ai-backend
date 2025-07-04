# AI 운동 루틴 DB 저장 로직 추가

from ..models import WorkoutRoutine, Exercise, RoutineExercise
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

def save_ai_routine_to_db(user, routine_data, level, muscle_group):
    """AI로 생성된 루틴을 DB에 저장"""
    try:
        with transaction.atomic():
            # WorkoutRoutine 생성
            workout_routine = WorkoutRoutine.objects.create(
                user=user,
                name=routine_data.get('routine_name', f'{muscle_group} {level} 루틴'),
                description=f"AI가 생성한 {muscle_group} 운동 루틴 ({level})",
                total_duration=routine_data.get('total_duration', 30),
                difficulty=level,
                is_public=False
            )
            
            # 각 운동을 RoutineExercise로 저장
            for idx, exercise_data in enumerate(routine_data.get('exercises', [])):
                exercise_name = exercise_data.get('name', '')
                
                # Exercise 찾기 또는 생성
                exercise, created = Exercise.objects.get_or_create(
                    name=exercise_name,
                    defaults={
                        'category': muscle_group,
                        'description': exercise_data.get('notes', ''),
                        'instructions': exercise_data.get('notes', ''),
                        'duration': 5,  # 기본값
                        'calories_per_minute': 8.0,
                        'difficulty': level.lower() if level in ['초급', '중급', '상급'] else 'medium',
                        'muscle_groups': [muscle_group]
                    }
                )
                
                # RoutineExercise 생성
                RoutineExercise.objects.create(
                    routine=workout_routine,
                    exercise=exercise,
                    sets=exercise_data.get('sets', 3),
                    reps=exercise_data.get('reps', 12),
                    rest_time=exercise_data.get('rest_seconds', 60),
                    order=idx
                )
            
            logger.info(f"AI 루틴 저장 완료: {workout_routine.id}")
            return workout_routine
            
    except Exception as e:
        logger.error(f"AI 루틴 저장 실패: {str(e)}")
        return None


# ai_workout 함수의 수정 부분:
# 기존 코드의 response 부분을 다음과 같이 수정

"""
# 기존 코드:
routine = {
    'id': random.randint(1000, 9999),
    'name': routine_data.get('routine_name', f'{muscle_group} 루틴'),
    'exercises': routine_exercises,
    'total_duration': routine_data.get('total_duration', duration),
    'difficulty': level,
    'created_at': datetime.now().isoformat()
}

# 수정된 코드:
# DB에 저장
saved_routine = None
if request.user.is_authenticated:
    saved_routine = save_ai_routine_to_db(
        request.user, 
        routine_data, 
        level, 
        muscle_group
    )

# 응답 데이터 구성
if saved_routine:
    # DB에 저장된 경우 실제 ID 사용
    routine = {
        'id': saved_routine.id,
        'name': saved_routine.name,
        'exercises': routine_exercises,
        'total_duration': saved_routine.total_duration,
        'difficulty': saved_routine.difficulty,
        'created_at': saved_routine.created_at.isoformat()
    }
else:
    # 게스트이거나 저장 실패시 임시 ID 사용
    routine = {
        'id': f'temp_{random.randint(1000, 9999)}',
        'name': routine_data.get('routine_name', f'{muscle_group} 루틴'),
        'exercises': routine_exercises,
        'total_duration': routine_data.get('total_duration', duration),
        'difficulty': level,
        'created_at': datetime.now().isoformat(),
        'is_temporary': True
    }
"""
