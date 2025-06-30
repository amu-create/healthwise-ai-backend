# 이 파일은 더 이상 사용되지 않습니다.
# 모든 모델은 core.models로 통합되었습니다.
# api/map/views.py와 serializers.py에서 core.models를 import하여 사용하세요.

from apps.core.models import (
    UserProfile as FitnessProfile,  # 호환성을 위한 별칭
    WorkoutLog as WorkoutRecord,     # 호환성을 위한 별칭
    MusicPreference,
    WorkoutMusic,
)
