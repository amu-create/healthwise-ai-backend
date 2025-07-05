# 운동 관련 유틸리티 함수들
import re
import logging

logger = logging.getLogger(__name__)

def safe_duration_convert(duration_value, default=30):
    """안전한 duration 값 변환"""
    try:
        logger.info(f"Received duration value: {duration_value} (type: {type(duration_value)})")
        
        # None, 빈 문자열, undefined 등 처리
        if duration_value is None or duration_value == '' or duration_value == 'undefined' or duration_value == 'null':
            duration = default
            logger.info(f"Duration is None/empty, using default {default}")
        elif isinstance(duration_value, str):
            # 문자열인 경우 숫자만 추출하여 변환
            numeric_str = re.sub(r'[^\d.]', '', str(duration_value))
            if numeric_str:
                try:
                    duration = int(float(numeric_str))
                except (ValueError, OverflowError):
                    duration = default
            else:
                duration = default
            logger.info(f"Converted string duration: {duration_value} -> {duration}")
        else:
            # 숫자인 경우 NaN 체크 후 변환
            try:
                # NaN 체크 (NaN != NaN은 True)
                if duration_value != duration_value:  # NaN 체크
                    duration = default
                    logger.info(f"Duration is NaN, using default {default}")
                else:
                    duration = int(float(duration_value))
                    logger.info(f"Converted numeric duration: {duration_value} -> {duration}")
            except (ValueError, TypeError, OverflowError):
                duration = default
                logger.info(f"Failed to convert numeric duration: {duration_value}, using default {default}")
        
        # 유효 범위 검증 (1분~300분)
        if duration < 1 or duration > 300:
            logger.warning(f"Duration {duration} out of range, using default {default}")
            duration = default
            
    except Exception as e:
        logger.warning(f"Exception in duration conversion: {duration_value}, using default {default}. Error: {str(e)}")
        duration = default
    
    return duration

def convert_routine_to_frontend_format(routine):
    """DB 루틴을 프론트엔드 형식으로 변환"""
    routine_exercises = []
    
    # RoutineExercise를 통해 운동 정보 가져오기
    for re in routine.routineexercise_set.all().order_by('order'):
        exercise = re.exercise
        routine_exercises.append({
            'id': exercise.id,
            'name': exercise.name,
            'sets': re.sets,
            'reps': re.reps,
            'duration': re.duration,
            'rest_time': re.rest_time,
            'category': exercise.category,
            'difficulty': exercise.difficulty,
            'description': exercise.description,
            'gif_url': f'/static/images/exercises/{exercise.name.lower().replace(" ", "_")}.gif',
            'order': re.order
        })
    
    # 루틴 객체 생성
    return {
        'id': routine.id,
        'name': routine.name,
        'description': routine.description,
        'level': routine.difficulty,
        'total_duration': routine.total_duration,
        'exercises': routine_exercises,
        'created_at': routine.created_at.isoformat(),
        'updated_at': routine.updated_at.isoformat(),
        'is_ai_generated': True,
        'is_custom': True
    }
