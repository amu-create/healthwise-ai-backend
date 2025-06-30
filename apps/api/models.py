from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# 운동 관련 모델
class Exercise(models.Model):
    EXERCISE_TYPES = [
        ('strength', '근력'),
        ('cardio', '유산소'),
        ('flexibility', '유연성'),
        ('core', '코어'),
    ]

    name = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, blank=True, null=True, help_text='영어 이름')
    name_es = models.CharField(max_length=100, blank=True, null=True, help_text='스페인어 이름')
    muscle_group = models.CharField(max_length=50, blank=True, null=True)
    muscle_group_en = models.CharField(max_length=50, blank=True, null=True, help_text='영어 근육군')
    muscle_group_es = models.CharField(max_length=50, blank=True, null=True, help_text='스페인어 근육군')
    gif_url = models.URLField(default='https://example.com/default.gif')
    default_sets = models.IntegerField(default=3)
    default_reps = models.IntegerField(default=10)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES, default='strength')
    description = models.TextField(blank=True, null=True)
    description_en = models.TextField(blank=True, null=True, help_text='영어 설명')
    description_es = models.TextField(blank=True, null=True, help_text='스페인어 설명')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_name(self, language='ko'):
        """언어별 이름 반환"""
        if language == 'en' and self.name_en:
            return self.name_en
        elif language == 'es' and self.name_es:
            return self.name_es
        return self.name
    
    def get_muscle_group(self, language='ko'):
        """언어별 근육군 반환"""
        if language == 'en' and self.muscle_group_en:
            return self.muscle_group_en
        elif language == 'es' and self.muscle_group_es:
            return self.muscle_group_es
        return self.muscle_group
    
    def get_description(self, language='ko'):
        """언어별 설명 반환"""
        if language == 'en' and self.description_en:
            return self.description_en
        elif language == 'es' and self.description_es:
            return self.description_es
        return self.description
    
    def __str__(self):
        return f"{self.name} ({self.get_exercise_type_display()})"

    class Meta:
        verbose_name = "운동"
        verbose_name_plural = "운동 목록"


class Routine(models.Model):
    name = models.CharField(max_length=100)
    exercises = models.ManyToManyField('Exercise', through='RoutineExercise')
    level = models.CharField(max_length=10)  # 초급 / 중급 / 상급
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='routines', null=True, blank=True)
    is_ai_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.level})"

    class Meta:
        verbose_name = "운동 루틴"
        verbose_name_plural = "운동 루틴 목록"


class RoutineExercise(models.Model):
    routine = models.ForeignKey(Routine, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    sets = models.IntegerField()
    reps = models.IntegerField()
    recommended_weight = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['order']
        unique_together = [['routine', 'exercise', 'order']]


# 사용자 피트니스 프로필
class FitnessProfile(models.Model):
    EXPERIENCE_CHOICES = [
        ('beginner', '초급'),
        ('intermediate', '중급'),
        ('advanced', '상급'),
    ]
    
    GOAL_CHOICES = [
        ('muscle_gain', '근육 증가'),
        ('weight_loss', '체중 감량'),
        ('endurance', '지구력 향상'),
        ('strength', '근력 향상'),
        ('general_fitness', '전반적 건강'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='fitness_profile')
    experience = models.CharField(max_length=20, choices=EXPERIENCE_CHOICES, default='beginner')
    goal = models.CharField(max_length=50, choices=GOAL_CHOICES, default='general_fitness')
    goal_text = models.CharField(max_length=100, blank=True, null=True)
    frequency = models.IntegerField(help_text="주당 운동 횟수", default=3)
    weight = models.FloatField(help_text="체중 (kg)", default=70)
    height = models.FloatField(help_text="신장 (cm)", default=170)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('male', '남성'), ('female', '여성'), ('other', '기타')], default='other')
    preferred_exercises = models.JSONField(default=list, blank=True)
    gym_access = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.goal}"

    class Meta:
        verbose_name = "피트니스 프로필"
        verbose_name_plural = "피트니스 프로필 목록"


# 운동 루틴 기록
class WorkoutRoutineLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_routine_logs')
    routine = models.ForeignKey(Routine, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    duration = models.IntegerField(help_text="운동 시간 (분)")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "운동 루틴 기록"
        verbose_name_plural = "운동 루틴 기록 목록"
        ordering = ['-date']


# 운동 기록 시스템 모델
class WorkoutAchievement(models.Model):
    CATEGORY_CHOICES = [
        ('workout', '운동'),
        ('nutrition', '영양'),
        ('streak', '연속'),
        ('milestone', '마일스톤'),
        ('challenge', '챌린지'),
    ]
    
    BADGE_CHOICES = [
        ('bronze', '브론즈'),
        ('silver', '실버'),
        ('gold', '골드'),
        ('platinum', '플래티넘'),
        ('diamond', '다이아몬드'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    name_en = models.CharField(max_length=100, blank=True, null=True)
    name_es = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    description_en = models.TextField(blank=True, null=True)
    description_es = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    badge_level = models.CharField(max_length=20, choices=BADGE_CHOICES, default='bronze')
    icon_name = models.CharField(max_length=50, help_text="Badge icon identifier")
    target_value = models.IntegerField(help_text="목표 달성 값")
    points = models.IntegerField(default=10, help_text="획득 포인트")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_name(self, language='ko'):
        if language == 'en' and self.name_en:
            return self.name_en
        elif language == 'es' and self.name_es:
            return self.name_es
        return self.name
    
    def get_description(self, language='ko'):
        if language == 'en' and self.description_en:
            return self.description_en
        elif language == 'es' and self.description_es:
            return self.description_es
        return self.description
    
    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    
    class Meta:
        verbose_name = "운동 기록 업적"
        verbose_name_plural = "운동 기록 업적 목록"
        ordering = ['category', 'target_value']


class UserWorkoutAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_achievements')
    achievement = models.ForeignKey(WorkoutAchievement, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0, help_text="현재 진행 상황")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def progress_percentage(self):
        if self.achievement.target_value > 0:
            return min(100, int((self.progress / self.achievement.target_value) * 100))
        return 0
    
    class Meta:
        verbose_name = "사용자 운동 기록"
        verbose_name_plural = "사용자 운동 기록 목록"
        unique_together = [['user', 'achievement']]
        ordering = ['-completed', '-progress']


# 사용자 레벨 시스템
# 소셜 기능 모델
class UserProfile(models.Model):
    """확장된 사용자 프로필 (소셜 기능 포함)"""
    PRIVACY_CHOICES = [
        ('public', '공개'),
        ('friends', '친구만'),
        ('private', '비공개'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_profile')
    bio = models.TextField(max_length=500, blank=True, help_text="자기소개")
    profile_picture_url = models.URLField(blank=True, null=True)
    privacy_setting = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')
    allow_friend_requests = models.BooleanField(default=True)
    show_achievement_badges = models.BooleanField(default=True)
    show_workout_stats = models.BooleanField(default=True)
    show_nutrition_stats = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Social Profile"
    
    class Meta:
        verbose_name = "소셜 프로필"
        verbose_name_plural = "소셜 프로필 목록"


class Follow(models.Model):
    """팔로우/팔로워 관계"""
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['follower', 'following']]
        verbose_name = "팔로우"
        verbose_name_plural = "팔로우 목록"
        
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class FriendRequest(models.Model):
    """친구 요청"""
    STATUS_CHOICES = [
        ('pending', '대기중'),
        ('accepted', '수락됨'),
        ('rejected', '거절됨'),
    ]
    
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_received')
    message = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['from_user', 'to_user']]
        verbose_name = "친구 요청"
        verbose_name_plural = "친구 요청 목록"


class WorkoutPost(models.Model):
    """운동 기록 공유 게시물"""
    VISIBILITY_CHOICES = [
        ('public', '전체 공개'),
        ('followers', '팔로워만'),
        ('private', '비공개'),
    ]
    
    MEDIA_TYPE_CHOICES = [
        ('image', '이미지'),
        ('video', '동영상'),
        ('gif', 'GIF'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_posts')
    workout_log = models.ForeignKey('WorkoutRoutineLog', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField(help_text="게시물 내용")
    
    # 미디어 필드
    image_url = models.URLField(blank=True, null=True)
    media_file = models.FileField(upload_to='social/posts/%Y/%m/', blank=True, null=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES, blank=True, null=True)
    media_url = models.URLField(blank=True, null=True, help_text="업로드된 미디어 URL")
    
    visibility = models.CharField(max_length=10, choices=VISIBILITY_CHOICES, default='public')
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # 미디어 타입 자동 설정
        if self.media_file:
            file_name = self.media_file.name.lower()
            if file_name.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                self.media_type = 'image'
            elif file_name.endswith(('.mp4', '.webm', '.mov')):
                self.media_type = 'video'
            elif file_name.endswith('.gif'):
                self.media_type = 'gif'
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "운동 게시물"
        verbose_name_plural = "운동 게시물 목록"
        ordering = ['-created_at']


class PostLike(models.Model):
    """게시물 좋아요"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(WorkoutPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['user', 'post']]
        verbose_name = "좋아요"
        verbose_name_plural = "좋아요 목록"


class PostComment(models.Model):
    """게시물 댓글"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(WorkoutPost, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "댓글"
        verbose_name_plural = "댓글 목록"
        ordering = ['created_at']


class UserWorkoutLevel(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='workout_level_info')
    level = models.IntegerField(default=1, help_text="현재 레벨 (1-100)")
    experience_points = models.IntegerField(default=0, help_text="총 경험치")
    total_achievement_points = models.IntegerField(default=0, help_text="총 업적 포인트")
    main_achievements = models.ManyToManyField(UserWorkoutAchievement, related_name='featured_by', blank=True, help_text="대표 업적 (최대 3개)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def required_exp_for_next_level(self):
        """다음 레벨까지 필요한 경험치 계산"""
        # 레벨당 필요 경험치 공식: level * 100
        return self.level * 100
    
    @property
    def current_level_progress(self):
        """현재 레벨에서의 진행도 (%)"""
        current_level_exp = sum((i * 100) for i in range(1, self.level))
        progress_in_level = self.experience_points - current_level_exp
        return min(100, int((progress_in_level / self.required_exp_for_next_level) * 100))
    
    def add_experience(self, points):
        """경험치 추가 및 레벨업 체크"""
        self.experience_points += points
        
        # 레벨업 체크
        while self.experience_points >= sum((i * 100) for i in range(1, self.level + 1)):
            if self.level < 100:  # 최대 레벨 100
                self.level += 1
                # 레벨업 시 알림 생성 로직 추가 가능
        
        self.save()
        return self.level
    
    def set_main_achievements(self, achievement_ids):
        """대표 업적 설정 (최대 3개)"""
        if len(achievement_ids) > 3:
            achievement_ids = achievement_ids[:3]
        
        user_achievements = UserWorkoutAchievement.objects.filter(
            user=self.user,
            id__in=achievement_ids,
            completed=True
        )
        self.main_achievements.set(user_achievements)
    
    def __str__(self):
        return f"{self.user.username} - Level {self.level}"
    
    class Meta:
        verbose_name = "사용자 운동 레벨"
        verbose_name_plural = "사용자 운동 레벨 목록"


class UserGoal(models.Model):
    GOAL_TYPE_CHOICES = [
        ('daily_calories', '일일 칼로리 목표'),
        ('weekly_workouts', '주간 운동 횟수'),
        ('monthly_workouts', '월간 운동 횟수'),
        ('weight_target', '목표 체중'),
        ('daily_steps', '일일 걸음수'),
        ('daily_water', '일일 수분 섭취'),
        ('sleep_hours', '수면 시간'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    goal_type = models.CharField(max_length=30, choices=GOAL_TYPE_CHOICES)
    target_value = models.FloatField()
    current_value = models.FloatField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def progress_percentage(self):
        if self.target_value > 0:
            return min(100, int((self.current_value / self.target_value) * 100))
        return 0
    
    @property
    def is_completed(self):
        return self.current_value >= self.target_value
    
    class Meta:
        verbose_name = "사용자 목표"
        verbose_name_plural = "사용자 목표 목록"
        unique_together = [['user', 'goal_type']]
        ordering = ['goal_type']


# 알림 시스템
class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('achievement', '업적'),
        ('social', '소셜'),
        ('workout', '운동'),
        ('nutrition', '영양'),
        ('system', '시스템'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    title_en = models.CharField(max_length=200, blank=True, null=True)
    title_es = models.CharField(max_length=200, blank=True, null=True)
    message = models.TextField()
    message_en = models.TextField(blank=True, null=True)
    message_es = models.TextField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    action_url = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_title(self, language='ko'):
        if language == 'en' and self.title_en:
            return self.title_en
        elif language == 'es' and self.title_es:
            return self.title_es
        return self.title
    
    def get_message(self, language='ko'):
        if language == 'en' and self.message_en:
            return self.message_en
        elif language == 'es' and self.message_es:
            return self.message_es
        return self.message
    
    class Meta:
        verbose_name = "알림"
        verbose_name_plural = "알림 목록"
        ordering = ['-created_at']


# 영양 분석 관련 모델
class FoodAnalysis(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_analyses')
    food_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    image_base64 = models.TextField(blank=True, null=True)
    calories = models.IntegerField()
    protein = models.FloatField(help_text="단백질 (g)")
    carbohydrates = models.FloatField(help_text="탄수화물 (g)")
    fat = models.FloatField(help_text="지방 (g)")
    fiber = models.FloatField(null=True, blank=True, help_text="식이섬유 (g)")
    sugar = models.FloatField(null=True, blank=True, help_text="당류 (g)")
    sodium = models.FloatField(null=True, blank=True, help_text="나트륨 (mg)")
    analysis_summary = models.TextField()
    recommendations = models.TextField()
    analyzed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "음식 분석"
        verbose_name_plural = "음식 분석 목록"
        ordering = ['-analyzed_at']


# 일일 영양 기록
class DailyNutrition(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_nutrition')
    date = models.DateField()
    total_calories = models.IntegerField(default=0)
    total_protein = models.FloatField(default=0)
    total_carbohydrates = models.FloatField(default=0)
    total_fat = models.FloatField(default=0)
    food_analyses = models.ManyToManyField(FoodAnalysis)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "일일 영양 기록"
        verbose_name_plural = "일일 영양 기록 목록"
        unique_together = [['user', 'date']]
        ordering = ['-date']
