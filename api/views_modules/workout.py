# 운동 관련 뷰 모듈 - 모듈화된 버전
"""
운동 관련 모든 엔드포인트를 모듈별로 정리
- workout_core: 기본 운동 기능 (exercise_list, workout_routines, workout_videos)
- workout_logs: 운동 로그 관련 (workout_logs, guest_workout_logs, workout_logs_create)
- workout_ai: AI 운동 관련 (ai_workout_recommendation, ai_workout)
- workout_constants: 상수 정의
- workout_utils: 유틸리티 함수
"""

# 기본 운동 기능
from .workout_core import (
    exercise_list,
    workout_routines,
    workout_videos,
    workout_videos_list
)

# 운동 로그 기능
from .workout_logs import (
    workout_logs,
    guest_workout_logs,
    workout_logs_create
)

# AI 운동 기능
from .workout_ai import (
    ai_workout_recommendation,
    ai_workout
)

# 모든 뷰 함수를 명시적으로 export
__all__ = [
    # Core
    'exercise_list',
    'workout_routines',
    'workout_videos',
    'workout_videos_list',
    
    # Logs
    'workout_logs',
    'guest_workout_logs',
    'workout_logs_create',
    
    # AI
    'ai_workout_recommendation',
    'ai_workout',
]
