from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Achievement(models.Model):
    """업적 정의"""
    CATEGORIES = (
        ('exercise', '운동'),
        ('nutrition', '영양'),
        ('social', '소셜'),
        ('streak', '연속'),
        ('milestone', '이정표'),
        ('general', '일반'),
    )
    
    code = models.CharField(max_length=50, unique=True, help_text='업적 고유 코드')
    title = models.CharField(max_length=100, verbose_name='업적명')
    description = models.TextField(verbose_name='설명')
    points = models.IntegerField(default=10, verbose_name='포인트')
    category = models.CharField(max_length=20, choices=CATEGORIES, default='general')
    icon = models.CharField(max_length=10, default='🏆', help_text='이모지 아이콘')
    
    # 조건
    condition_type = models.CharField(max_length=50, blank=True, help_text='조건 타입')
    condition_value = models.JSONField(default=dict, blank=True, help_text='조건 값')
    
    # 상태
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'achievements'
        ordering = ['category', 'points']
        verbose_name = '업적'
        verbose_name_plural = '업적'
    
    def __str__(self):
        return f"{self.title} ({self.points}p)"


class UserAchievement(models.Model):
    """사용자별 업적 달성 기록"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    
    is_unlocked = models.BooleanField(default=False, verbose_name='달성 여부')
    unlocked_at = models.DateTimeField(null=True, blank=True, verbose_name='달성 시간')
    progress = models.FloatField(default=0, verbose_name='진행률 (0-100)')
    
    # 추가 데이터
    metadata = models.JSONField(default=dict, blank=True, help_text='추가 메타데이터')
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_achievements'
        unique_together = [['user', 'achievement']]
        ordering = ['-unlocked_at', 'achievement__category']
        verbose_name = '사용자 업적'
        verbose_name_plural = '사용자 업적'
    
    def __str__(self):
        status = "달성" if self.is_unlocked else f"진행중 ({self.progress}%)"
        return f"{self.user.username} - {self.achievement.title} [{status}]"
    
    def save(self, *args, **kwargs):
        # 달성 시 시간 기록
        if self.is_unlocked and not self.unlocked_at:
            self.unlocked_at = timezone.now()
        super().save(*args, **kwargs)


class Level(models.Model):
    """레벨 정의"""
    level = models.IntegerField(unique=True, verbose_name='레벨')
    title = models.CharField(max_length=50, verbose_name='칭호')
    required_points = models.IntegerField(verbose_name='필요 포인트')
    icon = models.CharField(max_length=10, default='⭐', help_text='레벨 아이콘')
    color = models.CharField(max_length=7, default='#FFD700', help_text='레벨 색상 (HEX)')
    
    class Meta:
        db_table = 'levels'
        ordering = ['level']
        verbose_name = '레벨'
        verbose_name_plural = '레벨'
    
    def __str__(self):
        return f"Lv.{self.level} {self.title} ({self.required_points}p)"


class UserLevel(models.Model):
    """사용자 레벨 정보"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='level_info')
    current_level = models.ForeignKey(Level, on_delete=models.PROTECT)
    total_points = models.IntegerField(default=0, verbose_name='총 포인트')
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_levels'
        verbose_name = '사용자 레벨'
        verbose_name_plural = '사용자 레벨'
    
    def __str__(self):
        return f"{self.user.username} - {self.current_level}"
    
    def add_points(self, points):
        """포인트 추가 및 레벨 업 체크"""
        self.total_points += points
        
        # 다음 레벨 체크
        next_level = Level.objects.filter(
            required_points__lte=self.total_points
        ).order_by('-level').first()
        
        if next_level and next_level.level > self.current_level.level:
            self.current_level = next_level
            
        self.save()
        return self.current_level
    
    @property
    def progress_to_next_level(self):
        """다음 레벨까지의 진행률"""
        next_level = Level.objects.filter(
            level=self.current_level.level + 1
        ).first()
        
        if not next_level:
            return 100  # 최고 레벨
        
        current_required = self.current_level.required_points
        next_required = next_level.required_points
        current_progress = self.total_points - current_required
        total_needed = next_required - current_required
        
        return min(100, (current_progress / total_needed) * 100)
