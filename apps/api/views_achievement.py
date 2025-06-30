from rest_framework import viewsets, status, permissions
from .notification_service import NotificationService
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    WorkoutAchievement, UserWorkoutAchievement, UserWorkoutLevel, UserGoal,
    WorkoutRoutineLog, FoodAnalysis, DailyNutrition
)
from .serializers_achievement import (
    WorkoutAchievementSerializer, UserWorkoutAchievementSerializer,
    UserWorkoutLevelSerializer, UserGoalSerializer,
    AchievementProgressSerializer
)
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, F, Prefetch
from apps.social.models import SocialProfile

User = get_user_model()


class AchievementViewSet(viewsets.ReadOnlyModelViewSet):
    """업적 관련 뷰셋"""
    queryset = WorkoutAchievement.objects.filter(is_active=True)
    serializer_class = WorkoutAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Accept-Language 헤더에서 언어 추출
        language = self.request.headers.get('Accept-Language', 'ko')[:2]
        context['language'] = language
        return context
    
    @action(detail=False, methods=['get'])
    def following_leaderboard(self, request):
        """팔로잉하는 사용자들의 업적 리더보드"""
        user = request.user
        
        # 현재 사용자가 팔로잉하는 사람들 가져오기
        try:
            social_profile = user.social_profile_obj
            following_users = social_profile.followers.all()
        except:
            following_users = User.objects.none()
        
        # 팔로잉하는 사용자들의 레벨 정보와 업적 정보 가져오기
        leaderboard_data = []
        
        for followed_user in following_users:
            user_level, _ = UserWorkoutLevel.objects.get_or_create(
                user=followed_user,
                defaults={'level': 1, 'experience_points': 0}
            )
            
            # 완료한 업적 수
            completed_achievements = UserWorkoutAchievement.objects.filter(
                user=followed_user,
                completed=True
            ).count()
            
            # 최근 완료한 업적 3개
            recent_achievements = UserWorkoutAchievement.objects.filter(
                user=followed_user,
                completed=True
            ).select_related('achievement').order_by('-completed_at')[:3]
            
            recent_achievements_data = []
            for ua in recent_achievements:
                recent_achievements_data.append({
                    'id': ua.achievement.id,
                    'name': ua.achievement.get_name(self.request.headers.get('Accept-Language', 'ko')[:2]),
                    'badge_level': ua.achievement.badge_level,
                })
            
            leaderboard_data.append({
                'user': {
                    'id': followed_user.id,
                    'username': followed_user.username,
                    'profile_picture_url': getattr(followed_user.profile, 'profile_image', None) if hasattr(followed_user, 'profile') else None,
                },
                'level': user_level.level,
                'total_points': user_level.total_achievement_points,
                'completed_achievements': completed_achievements,
                'recent_achievements': recent_achievements_data,
            })
        
        # 포인트 순으로 정렬
        leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
        
        return Response({'results': leaderboard_data})
    
    @action(detail=False, methods=['get'])
    def user_achievements(self, request):
        """현재 사용자의 업적 현황"""
        user_achievements = UserWorkoutAchievement.objects.filter(
            user=request.user
        ).select_related('achievement')
        
        # 카테고리별로 그룹화
        achievements_by_category = {}
        for category, _ in WorkoutAchievement.CATEGORY_CHOICES:
            achievements_by_category[category] = []
        
        # 사용자 업적 매핑
        user_achievement_map = {ua.achievement_id: ua for ua in user_achievements}
        
        # 모든 활성 업적 가져오기
        all_achievements = self.get_queryset()
        
        for achievement in all_achievements:
            if achievement.id in user_achievement_map:
                # 사용자가 진행 중인 업적
                ua = user_achievement_map[achievement.id]
                data = UserWorkoutAchievementSerializer(ua, context=self.get_serializer_context()).data
            else:
                # 아직 시작하지 않은 업적
                data = {
                    'id': None,
                    'achievement': WorkoutAchievementSerializer(achievement, context=self.get_serializer_context()).data,
                    'progress': 0,
                    'progress_percentage': 0,
                    'completed': False,
                    'completed_at': None
                }
            
            achievements_by_category[achievement.category].append(data)
        
        return Response(achievements_by_category)
    
    @action(detail=False, methods=['get'])
    def progress_summary(self, request):
        """업적 진행률 요약 (대시보드용)"""
        user = request.user
        
        # 사용자 업적 통계
        user_achievements = UserWorkoutAchievement.objects.filter(user=user)
        completed_count = user_achievements.filter(completed=True).count()
        total_points = user_achievements.filter(
            completed=True
        ).aggregate(
            total=Sum('achievement__points')
        )['total'] or 0
        
        # 전체 업적 수
        total_achievements = WorkoutAchievement.objects.filter(is_active=True).count()
        
        # 최근 완료한 업적 (최근 5개)
        recent_achievements = user_achievements.filter(
            completed=True
        ).order_by('-completed_at')[:5]
        
        # 활성 목표
        active_goals = UserGoal.objects.filter(user=user, is_active=True)
        
        # 사용자 레벨 정보 (없으면 생성)
        user_level, created = UserWorkoutLevel.objects.get_or_create(
            user=user,
            defaults={'level': 1, 'experience_points': 0}
        )
        
        if created or user_level.total_achievement_points != total_points:
            user_level.total_achievement_points = total_points
            user_level.save()
        
        # 완료율 계산
        completion_percentage = (completed_count / total_achievements * 100) if total_achievements > 0 else 0
        
        data = {
            'total_achievements': total_achievements,
            'completed_achievements': completed_count,
            'total_points': total_points,
            'completion_percentage': round(completion_percentage, 1),
            'recent_achievements': UserWorkoutAchievementSerializer(
                recent_achievements, many=True, context=self.get_serializer_context()
            ).data,
            'active_goals': UserGoalSerializer(
                active_goals, many=True, context=self.get_serializer_context()
            ).data,
            'user_level': UserWorkoutLevelSerializer(
                user_level, context=self.get_serializer_context()
            ).data
        }
        
        return Response(data)
    
    @action(detail=False, methods=['post'])
    def check_and_update(self, request):
        """업적 진행 상황 체크 및 업데이트"""
        user = request.user
        updated_achievements = []
        
        with transaction.atomic():
            # 운동 관련 업적 체크
            workout_count = WorkoutRoutineLog.objects.filter(user=user).count()
            self._update_achievement_progress(user, 'workout_beginner', workout_count, updated_achievements)
            self._update_achievement_progress(user, 'workout_intermediate', workout_count, updated_achievements)
            self._update_achievement_progress(user, 'workout_advanced', workout_count, updated_achievements)
            
            # 주간 운동 업적
            week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
            weekly_workouts = WorkoutRoutineLog.objects.filter(
                user=user,
                date__gte=week_start
            ).count()
            if weekly_workouts >= 5:
                self._update_achievement_progress(user, 'weekly_warrior', 1, updated_achievements)
            
            # 월간 운동 업적
            month_start = timezone.now().date().replace(day=1)
            monthly_workouts = WorkoutRoutineLog.objects.filter(
                user=user,
                date__gte=month_start
            ).count()
            if monthly_workouts >= 20:
                self._update_achievement_progress(user, 'monthly_master', 1, updated_achievements)
            
            # 영양 관련 업적 체크
            nutrition_days = DailyNutrition.objects.filter(user=user).count()
            self._update_achievement_progress(user, 'nutrition_tracker', nutrition_days, updated_achievements)
            self._update_achievement_progress(user, 'nutrition_pro', nutrition_days, updated_achievements)
            self._update_achievement_progress(user, 'nutrition_master', nutrition_days, updated_achievements)
            
            # 연속 기록 업적 체크
            self._check_streak_achievements(user, updated_achievements)
        
        return Response({
            'updated_achievements': updated_achievements,
            'message': f'{len(updated_achievements)}개의 업적이 업데이트되었습니다.'
        })
    
    def _update_achievement_progress(self, user, achievement_name, progress_value, updated_list):
        """업적 진행 상황 업데이트"""
        try:
            achievement = WorkoutAchievement.objects.get(name=achievement_name, is_active=True)
            user_achievement, created = UserWorkoutAchievement.objects.get_or_create(
                user=user,
                achievement=achievement,
                defaults={'progress': 0}
            )
            
            if not user_achievement.completed and progress_value > user_achievement.progress:
                user_achievement.progress = progress_value
                
                # 목표 달성 체크
                if user_achievement.progress >= achievement.target_value:
                    user_achievement.completed = True
                    user_achievement.completed_at = timezone.now()
                    
                    # 레벨 시스템에 경험치 추가
                    user_level, _ = UserWorkoutLevel.objects.get_or_create(user=user)
                    previous_level = user_level.level
                    new_level = user_level.add_experience(achievement.points)
                    
                    # 업적 달성 알림
                    NotificationService.send_achievement_notification(user, achievement, user_achievement)
                    
                    # 레벨업 알림
                    if new_level > previous_level:
                        NotificationService.send_level_up_notification(user, new_level, previous_level)
                
                user_achievement.save()
                updated_list.append({
                    'achievement': achievement.name,
                    'progress': user_achievement.progress,
                    'completed': user_achievement.completed
                })
        except WorkoutAchievement.DoesNotExist:
            pass
    
    def _check_streak_achievements(self, user, updated_list):
        """연속 기록 업적 체크"""
        today = timezone.now().date()
        
        # 운동 연속 기록
        workout_streak = 0
        for i in range(30):  # 최대 30일 체크
            check_date = today - timedelta(days=i)
            if WorkoutRoutineLog.objects.filter(user=user, date=check_date).exists():
                workout_streak += 1
            else:
                break
        
        if workout_streak >= 7:
            self._update_achievement_progress(user, 'streak_7days', 1, updated_list)
        if workout_streak >= 30:
            self._update_achievement_progress(user, 'streak_30days', 1, updated_list)
        
        # 영양 연속 기록
        nutrition_streak = 0
        for i in range(30):
            check_date = today - timedelta(days=i)
            if DailyNutrition.objects.filter(user=user, date=check_date).exists():
                nutrition_streak += 1
            else:
                break
        
        if nutrition_streak >= 7:
            self._update_achievement_progress(user, 'nutrition_streak_7days', 1, updated_list)
        if nutrition_streak >= 30:
            self._update_achievement_progress(user, 'nutrition_streak_30days', 1, updated_list)


class UserGoalViewSet(viewsets.ModelViewSet):
    """사용자 목표 관리 뷰셋"""
    serializer_class = UserGoalSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserGoal.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        # 동일한 타입의 기존 목표 비활성화
        UserGoal.objects.filter(
            user=self.request.user,
            goal_type=serializer.validated_data['goal_type']
        ).update(is_active=False)
        
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """목표 진행 상황 업데이트"""
        goal = self.get_object()
        current_value = request.data.get('current_value')
        
        if current_value is not None:
            goal.current_value = float(current_value)
            goal.save()
            
            # 목표 달성 시 업적 체크 및 알림
            if goal.is_completed:
                # 목표 달성 관련 업적 업데이트 로직 추가 가능
                NotificationService.send_goal_achieved_notification(request.user, goal)
            
            return Response(UserGoalSerializer(goal).data)
        
        return Response(
            {'error': 'current_value is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """여러 목표 한번에 업데이트"""
        updates = request.data.get('updates', [])
        updated_goals = []
        
        for update in updates:
            try:
                goal = UserGoal.objects.get(
                    user=request.user,
                    goal_type=update['goal_type'],
                    is_active=True
                )
                goal.current_value = float(update['current_value'])
                goal.save()
                updated_goals.append(goal)
            except (UserGoal.DoesNotExist, KeyError, ValueError):
                continue
        
        serializer = UserGoalSerializer(updated_goals, many=True)
        return Response(serializer.data)


class UserLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """사용자 레벨 정보 뷰셋"""
    serializer_class = UserWorkoutLevelSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserWorkoutLevel.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_level(self, request):
        """현재 사용자의 레벨 정보"""
        user_level, created = UserWorkoutLevel.objects.get_or_create(
            user=request.user,
            defaults={'level': 1, 'experience_points': 0}
        )
        
        serializer = self.get_serializer(user_level)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def set_main_achievements(self, request):
        """대표 업적 설정"""
        achievement_ids = request.data.get('achievement_ids', [])
        
        if not isinstance(achievement_ids, list):
            return Response(
                {'error': 'achievement_ids must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_level, _ = UserWorkoutLevel.objects.get_or_create(user=request.user)
        user_level.set_main_achievements(achievement_ids)
        
        serializer = self.get_serializer(user_level)
        return Response(serializer.data)
