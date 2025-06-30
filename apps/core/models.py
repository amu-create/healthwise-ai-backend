from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import json
from django.utils import timezone

# 알림 모델 import
from .models_notification import NotificationSettings, NotificationLog

class User(AbstractUser):
    """커스텀 사용자 모델"""
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'

class UserProfile(models.Model):
    """사용자 프로필 정보"""
    GENDER_CHOICES = [
        ('M', '남성'),
        ('F', '여성'),
        ('O', '기타'),
    ]
    
    EXPERIENCE_CHOICES = [
        ('beginner', '초급자 (1년 미만)'),
        ('intermediate', '중급자 (1-3년)'),
        ('advanced', '상급자 (3-5년)'),
        ('expert', '전문가 (5년 이상)'),
    ]
    
    GOAL_CHOICES = [
        ('weight_loss', '체중 감량'),
        ('muscle_gain', '근육 증가'),
        ('health_improvement', '건강 개선'),
        ('endurance', '지구력 향상'),
        ('flexibility', '유연성 향상'),
        ('stress_relief', '스트레스 해소'),
        ('custom', '사용자 정의'),
    ]
    
    UNIT_CHOICES = [
        ('kg', 'kg'),
        ('lbs', 'lbs'),
    ]
    
    DISTANCE_UNIT_CHOICES = [
        ('km', 'km'),
        ('miles', 'miles'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # 신체 정보
    age = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(120)])
    height = models.FloatField(help_text='cm 단위', validators=[MinValueValidator(50), MaxValueValidator(300)])
    weight = models.FloatField(help_text='kg 단위', validators=[MinValueValidator(20), MaxValueValidator(500)])
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')
    
    # 운동 정보
    exercise_experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='beginner')
    
    # 프로필 이미지
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    
    # 건강 정보 (JSON으로 저장)
    diseases = models.JSONField(default=list, help_text='질병 목록')
    allergies = models.JSONField(default=list, help_text='알레르기 목록')
    
    # 선호도 정보 (대화에서 자동 학습)
    preferred_exercises = models.JSONField(default=list, help_text='선호하는 운동 목록')
    preferred_foods = models.JSONField(default=list, help_text='선호하는 음식 목록')
    disliked_exercises = models.JSONField(default=list, help_text='싫어하는 운동 목록')
    disliked_foods = models.JSONField(default=list, help_text='싫어하는 음식 목록')
    
    # 운동 목표 정보
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='health_improvement')
    custom_goal = models.TextField(blank=True, help_text='사용자 정의 목표')
    workout_days_per_week = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(7)])
    
    # 단위 설정
    weight_unit = models.CharField(max_length=5, choices=UNIT_CHOICES, default='kg')
    distance_unit = models.CharField(max_length=5, choices=DISTANCE_UNIT_CHOICES, default='km')
    
    # 운동 목표 설정
    weekly_workout_goal = models.IntegerField(default=3, help_text='주간 운동 목표 횟수')
    monthly_distance_goal = models.FloatField(default=50.0, help_text='월간 목표 거리 (km 또는 miles)')
    monthly_calories_goal = models.IntegerField(default=8000, help_text='월간 목표 칼로리 소모량')
    daily_steps_goal = models.IntegerField(default=10000, help_text='일일 목표 걸음 수')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필들'
    
    def __str__(self):
        return f"{self.user.email}의 프로필"

class WorkoutCategory(models.Model):
    """운동 카테고리"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text='아이콘 클래스명')
    
    class Meta:
        db_table = 'workout_categories'
        verbose_name = '운동 카테고리'
        verbose_name_plural = '운동 카테고리들'
    
    def __str__(self):
        return self.name

class WorkoutVideo(models.Model):
    """운동 영상 정보"""
    DIFFICULTY_CHOICES = [
        ('beginner', '초급'),
        ('intermediate', '중급'),
        ('advanced', '상급'),
    ]
    
    youtube_id = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    thumbnail_url = models.URLField()
    duration = models.IntegerField(help_text='초 단위')
    
    category = models.ForeignKey(WorkoutCategory, on_delete=models.CASCADE, related_name='videos')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    target_muscles = models.JSONField(default=list, help_text='타겟 근육 목록')
    
    view_count = models.IntegerField(default=0)
    like_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workout_videos'
        verbose_name = '운동 영상'
        verbose_name_plural = '운동 영상들'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title

class WorkoutLog(models.Model):
    """운동 기록"""
    WORKOUT_TYPE_CHOICES = [
        ('running', '러닝'),
        ('cycling', '자전거'),
        ('swimming', '수영'),
        ('gym', '헬스장'),
        ('yoga', '요가'),
        ('pilates', '필라테스'),
        ('hiking', '등산'),
        ('sports', '스포츠'),
        ('home', '홈트레이닝'),
        ('other', '기타'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_logs')
    video = models.ForeignKey(WorkoutVideo, on_delete=models.SET_NULL, null=True, blank=True)
    
    date = models.DateField()
    duration = models.IntegerField(help_text='분 단위')
    calories_burned = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # 운동 세부 정보
    workout_name = models.CharField(max_length=100)
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPE_CHOICES, default='other')
    sets = models.IntegerField(null=True, blank=True)
    reps = models.IntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True, help_text='kg 단위')
    
    # 지도 관련 정보
    start_latitude = models.FloatField(null=True, blank=True)
    start_longitude = models.FloatField(null=True, blank=True)
    end_latitude = models.FloatField(null=True, blank=True)
    end_longitude = models.FloatField(null=True, blank=True)
    route_coordinates = models.JSONField(default=list, help_text='경로 좌표 목록')
    distance = models.FloatField(null=True, blank=True, help_text='이동 거리 (km)')
    
    # 운동 중 측정값
    avg_heart_rate = models.IntegerField(null=True, blank=True, help_text='평균 심박수')
    max_heart_rate = models.IntegerField(null=True, blank=True, help_text='최대 심박수')
    steps = models.IntegerField(null=True, blank=True, help_text='걸음 수')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'workout_logs'
        verbose_name = '운동 기록'
        verbose_name_plural = '운동 기록들'
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.workout_name}"

class DietLog(models.Model):
    """식단 기록"""
    MEAL_TYPE_CHOICES = [
        ('breakfast', '아침'),
        ('lunch', '점심'),
        ('dinner', '저녁'),
        ('snack', '간식'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='diet_logs')
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES)
    
    food_items = models.JSONField(default=list, help_text='음식 항목 목록')
    total_calories = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    # 영양 정보
    protein = models.FloatField(null=True, blank=True, help_text='단백질(g)')
    carbohydrates = models.FloatField(null=True, blank=True, help_text='탄수화물(g)')
    fat = models.FloatField(null=True, blank=True, help_text='지방(g)')
    fiber = models.FloatField(null=True, blank=True, help_text='식이섬유(g)')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'diet_logs'
        verbose_name = '식단 기록'
        verbose_name_plural = '식단 기록들'
        ordering = ['-date', '-created_at']
        unique_together = ['user', 'date', 'meal_type']
    
    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.get_meal_type_display()}"

class ChatSession(models.Model):
    """챗봇 대화 세션"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    user_session_number = models.IntegerField(default=1, help_text='사용자별 세션 번호')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # 세션 요약 정보
    summary = models.TextField(blank=True, help_text='세션 대화 요약')
    extracted_preferences = models.JSONField(default=dict, help_text='추출된 선호도 정보')
    
    class Meta:
        db_table = 'chat_sessions'
        verbose_name = '챗봇 세션'
        verbose_name_plural = '챗봇 세션들'
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.email} - 세션 #{self.user_session_number} ({self.started_at})"    
    
    def end_session(self):
        """세션 종료"""
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()
    
    def save(self, *args, **kwargs):
        """저장 시 사용자별 세션 번호 자동 부여"""
        if not self.pk and not self.user_session_number:
            # 새 세션 생성 시 사용자의 마지막 세션 번호 + 1 부여
            last_session = ChatSession.objects.filter(user=self.user).order_by('-user_session_number').first()
            if last_session:
                self.user_session_number = last_session.user_session_number + 1
            else:
                self.user_session_number = 1
        super().save(*args, **kwargs)


class ChatMessage(models.Model):
    """챗봇 대화 메시지"""
    SENDER_CHOICES = [
        ('user', '사용자'),
        ('bot', '챗봇'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    
    # 메타데이터
    context = models.JSONField(null=True, blank=True, help_text='대화 컨텍스트')
    embedding = models.JSONField(null=True, blank=True, help_text='메시지 임베딩')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'chat_messages'
        verbose_name = '챗봇 메시지'
        verbose_name_plural = '챗봇 메시지들'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.sender} - {self.created_at}"


class VectorizedChatHistory(models.Model):
    """벡터화된 챗봇 대화 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vectorized_chats')
    sessions = models.JSONField(default=list, help_text='벡터화된 세션 ID 목록')
    
    # 벡터 저장
    embedding = models.JSONField(help_text='대화 내용의 통합 임베딩')
    summary = models.TextField(help_text='대화 내용 요약')
    
    # 메타데이터
    message_count = models.IntegerField(help_text='벡터화된 메시지 수')
    date_range_start = models.DateTimeField(help_text='가장 오래된 메시지 시간')
    date_range_end = models.DateTimeField(help_text='가장 최근 메시지 시간')
    
    # 추출된 정보
    topics = models.JSONField(default=list, help_text='대화 주제들')
    preferences = models.JSONField(default=dict, help_text='추출된 선호도 정보')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'vectorized_chat_history'
        verbose_name = '벡터화된 대화 기록'
        verbose_name_plural = '벡터화된 대화 기록들'
        ordering = ['-date_range_end']
    
    def __str__(self):
        return f"{self.user.email} - 벡터화 기록 ({self.date_range_start} ~ {self.date_range_end})"


class DailyRecommendation(models.Model):
    """일일 추천"""
    RECOMMENDATION_TYPE_CHOICES = [
        ('workout', '운동'),
        ('diet', '식단'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_recommendations')
    date = models.DateField(default=timezone.now)
    type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE_CHOICES)
    
    # 추천 내용
    title = models.CharField(max_length=200)
    description = models.TextField()
    details = models.JSONField(help_text='추천 상세 정보')
    
    # 추천 근거
    reasoning = models.TextField(help_text='추천 이유')
    based_on = models.JSONField(default=dict, help_text='추천 근거 데이터')
    
    # 사용자 피드백
    is_accepted = models.BooleanField(null=True, blank=True)
    user_feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_recommendations'
        verbose_name = '일일 추천'
        verbose_name_plural = '일일 추천들'
        ordering = ['-date', '-created_at']
        unique_together = ['user', 'date', 'type']
    
    def __str__(self):
        return f"{self.user.email} - {self.date} - {self.get_type_display()}: {self.title}"

class ExerciseLocation(models.Model):
    """운동 장소"""
    LOCATION_TYPE_CHOICES = [
        ('gym', '헬스장'),
        ('yoga', '요가원'),
        ('pilates', '필라테스'),
        ('crossfit', '크로스핏'),
        ('swimming', '수영장'),
        ('martial_arts', '무술도장'),
        ('dance', '댄스학원'),
        ('other', '기타'),
    ]
    
    name = models.CharField(max_length=100)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPE_CHOICES)
    address = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    operating_hours = models.JSONField(default=dict, help_text='운영 시간')
    
    rating = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(5)])
    review_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'exercise_locations'
        verbose_name = '운동 장소'
        verbose_name_plural = '운동 장소들'
    
    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"

class MusicRecommendation(models.Model):
    """음악 추천"""
    WORKOUT_TYPE_CHOICES = [
        ('cardio', '유산소'),
        ('strength', '근력운동'),
        ('yoga', '요가'),
        ('stretching', '스트레칭'),
        ('hiit', 'HIIT'),
        ('running', '러닝'),
    ]
    
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=100)
    album = models.CharField(max_length=200, blank=True)
    
    spotify_id = models.CharField(max_length=50, blank=True)
    preview_url = models.URLField(blank=True)
    
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPE_CHOICES)
    bpm = models.IntegerField(null=True, blank=True, help_text='Beats per minute')
    energy_level = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'music_recommendations'
        verbose_name = '음악 추천'
        verbose_name_plural = '음악 추천들'
    
    def __str__(self):
        return f"{self.title} - {self.artist} ({self.get_workout_type_display()})"


class MusicPreference(models.Model):
    """사용자 음악 선호도"""
    MOOD_CHOICES = [
        ('energetic', '활기찬'),
        ('calm', '차분한'),
        ('intense', '강렬한'),
        ('happy', '경쾌한'),
        ('focused', '집중하는'),
        ('relaxed', '편안한'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='music_preferences')
    
    # 음악 선호도
    preferred_genres = models.JSONField(default=list, help_text='선호 장르 목록')
    preferred_artists = models.JSONField(default=list, help_text='선호 아티스트 목록')
    disliked_genres = models.JSONField(default=list, help_text='비선호 장르 목록')
    
    # 운동별 선호도
    workout_music_preferences = models.JSONField(default=dict, help_text='운동 종류별 음악 선호도')
    
    # BPM 선호도
    preferred_bpm_min = models.IntegerField(default=100, help_text='선호 BPM 최소값')
    preferred_bpm_max = models.IntegerField(default=180, help_text='선호 BPM 최대값')
    
    # 기분별 선호도
    mood_preferences = models.JSONField(default=dict, help_text='기분별 음악 선호도')
    
    # 학습 데이터
    feedback_history = models.JSONField(default=list, help_text='피드백 기록')
    recommendation_accuracy = models.FloatField(default=0.0, help_text='추천 정확도')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'music_preferences'
        verbose_name = '음악 선호도'
        verbose_name_plural = '음악 선호도들'
    
    def __str__(self):
        return f"{self.user.email}의 음악 선호도"


class WorkoutMusic(models.Model):
    """운동 중 재생된 음악"""
    FEEDBACK_CHOICES = [
        ('liked', '좋음'),
        ('disliked', '싫음'),
        ('neutral', '보통'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_music')
    workout_log = models.ForeignKey(WorkoutLog, on_delete=models.CASCADE, related_name='played_music')
    
    # 음악 정보
    title = models.CharField(max_length=200)
    artist = models.CharField(max_length=100)
    youtube_id = models.CharField(max_length=50, blank=True)
    spotify_id = models.CharField(max_length=50, blank=True)
    
    # 재생 정보
    played_at = models.DateTimeField(auto_now_add=True)
    play_duration = models.IntegerField(help_text='재생 시간 (초)')
    skip_count = models.IntegerField(default=0, help_text='건너뛰기 횟수')
    
    # 피드백
    user_feedback = models.CharField(max_length=10, choices=FEEDBACK_CHOICES, null=True, blank=True)
    feedback_note = models.TextField(blank=True)
    
    # AI 추천 정보
    was_ai_recommended = models.BooleanField(default=False)
    recommendation_reason = models.TextField(blank=True)
    recommendation_keywords = models.JSONField(default=list, help_text='AI 추천 키워드')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'workout_music'
        verbose_name = '운동 중 재생 음악'
        verbose_name_plural = '운동 중 재생 음악들'
        ordering = ['-played_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title} ({self.workout_log.date})"

# 질병 및 알레르기 선택 옵션
DISEASE_CHOICES = [
    '고혈압', '당뇨병', '심장질환', '관절염', '천식',
    '갑상선 질환', '신장질환', '간질환', '위장질환', '빈혈',
    '골다공증', '우울증', '불안장애', '수면장애', '비만',
    '고지혈증', '통풍', '알레르기성 비염', '아토피', '건선'
]

ALLERGY_CHOICES = [
    '계란', '우유', '밀', '콩', '땅콩',
    '견과류', '생선', '조개류', '갑각류', '돼지고기',
    '소고기', '닭고기', '토마토', '딸기', '복숭아',
    '키위', '바나나', '아보카도', '메밀', '참깨'
]

# 운동 종류
EXERCISE_CHOICES = [
    '런닝', '조깅', '수영', '자전거', '등산',
    '요가', '필라테스', '웨이트 트레이닝', '크로스핏', '복싱',
    '댄스', '배드민턴', '테니스', '축구', '농구',
    '골프', '클라이밍', '스쿼시', '탁구', '볼링'
]

# 음식 카테고리
FOOD_CATEGORIES = [
    '한식', '중식', '일식', '양식', '분식',
    '샐러드', '과일', '채소', '육류', '해산물',
    '유제품', '빵', '면류', '죽', '스무디'
]
