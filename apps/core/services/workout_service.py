"""
운동 관련 서비스 레이어
성능 최적화를 위한 비즈니스 로직 캡슐화
"""
from django.db import transaction
from django.db.models import Q, Count, Avg, Sum, F, Prefetch
from django.utils import timezone
from datetime import timedelta, date
from typing import Dict, List, Optional, Tuple
from ..models import (
    WorkoutLog, WorkoutVideo, WorkoutCategory, 
    ExerciseLocation, User, UserProfile
)

class WorkoutService:
    """운동 관련 서비스"""
    
    @staticmethod
    def get_workout_videos_optimized(
        category_id: Optional[int] = None,
        difficulty: Optional[str] = None,
        limit: int = 20
    ) -> List[WorkoutVideo]:
        """운동 영상 목록 조회 (최적화)"""
        queryset = WorkoutVideo.objects.select_related('category')
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        return queryset.order_by('-view_count', '-created_at')[:limit]
    
    @staticmethod
    def get_workout_categories_with_counts() -> List[Dict]:
        """카테고리별 영상 수 포함 조회"""
        return WorkoutCategory.objects.annotate(
            video_count=Count('videos'),
            avg_duration=Avg('videos__duration'),
            total_views=Sum('videos__view_count')
        ).order_by('name')
    
    @staticmethod
    @transaction.atomic
    def create_workout_log(user: User, workout_data: Dict) -> WorkoutLog:
        """운동 기록 생성 (트랜잭션 사용)"""
        # 칼로리 자동 계산 (없을 경우)
        if not workout_data.get('calories_burned'):
            workout_data['calories_burned'] = WorkoutService._calculate_calories(
                workout_type=workout_data.get('workout_type', 'other'),
                duration=workout_data.get('duration', 0),
                weight=user.profile.weight if hasattr(user, 'profile') else 70
            )
        
        # 운동 기록 생성
        workout_log = WorkoutLog.objects.create(
            user=user,
            **workout_data
        )
        
        # 관련 영상이 있을 경우 조회수 증가
        if workout_log.video:
            WorkoutVideo.objects.filter(id=workout_log.video.id).update(
                view_count=F('view_count') + 1
            )
        
        return workout_log
    
    @staticmethod
    def _calculate_calories(workout_type: str, duration: int, weight: float) -> int:
        """운동 종류별 칼로리 계산"""
        # MET (Metabolic Equivalent of Task) 값
        met_values = {
            'running': 9.8,
            'cycling': 7.5,
            'swimming': 8.0,
            'gym': 6.0,
            'yoga': 3.0,
            'pilates': 3.8,
            'hiking': 6.5,
            'sports': 7.0,
            'home': 5.0,
            'other': 4.0
        }
        
        met = met_values.get(workout_type, 4.0)
        # 칼로리 = MET * 체중(kg) * 시간(시간)
        calories = met * weight * (duration / 60)
        
        return int(calories)
    
    @staticmethod
    def get_user_workout_summary(user: User, period_days: int = 30) -> Dict:
        """사용자 운동 요약 통계"""
        start_date = timezone.now().date() - timedelta(days=period_days)
        
        # 기본 통계
        basic_stats = WorkoutLog.objects.filter(
            user=user,
            date__gte=start_date
        ).aggregate(
            total_workouts=Count('id'),
            total_duration=Sum('duration'),
            total_calories=Sum('calories_burned'),
            avg_duration=Avg('duration'),
            total_distance=Sum('distance')
        )
        
        # 운동 종류별 통계
        type_stats = WorkoutLog.objects.filter(
            user=user,
            date__gte=start_date
        ).values('workout_type').annotate(
            count=Count('id'),
            total_duration=Sum('duration'),
            total_calories=Sum('calories_burned')
        ).order_by('-count')
        
        # 주간 트렌드
        weekly_trend = []
        for i in range(4):  # 최근 4주
            week_start = start_date + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)
            
            week_stats = WorkoutLog.objects.filter(
                user=user,
                date__range=[week_start, week_end]
            ).aggregate(
                workouts=Count('id'),
                duration=Sum('duration'),
                calories=Sum('calories_burned')
            )
            
            weekly_trend.append({
                'week': i + 1,
                'start_date': week_start,
                'end_date': week_end,
                **week_stats
            })
        
        return {
            'basic_stats': basic_stats,
            'type_stats': list(type_stats),
            'weekly_trend': weekly_trend,
            'period_days': period_days
        }
    
    @staticmethod
    def get_nearby_exercise_locations(
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        location_type: Optional[str] = None
    ) -> List[ExerciseLocation]:
        """주변 운동 장소 조회 (거리 계산 최적화)"""
        # Haversine 공식을 사용한 거리 계산
        # 단순화를 위해 대략적인 계산 사용 (1도 = 약 111km)
        lat_diff = radius_km / 111.0
        lon_diff = radius_km / (111.0 * abs(latitude))
        
        queryset = ExerciseLocation.objects.filter(
            latitude__range=(latitude - lat_diff, latitude + lat_diff),
            longitude__range=(longitude - lon_diff, longitude + lon_diff)
        )
        
        if location_type:
            queryset = queryset.filter(location_type=location_type)
        
        # 평점순 정렬
        return queryset.order_by('-rating', '-review_count')
    
    @staticmethod
    def get_recommended_workouts(user: User, limit: int = 5) -> List[WorkoutVideo]:
        """사용자 맞춤 운동 추천"""
        profile = user.profile if hasattr(user, 'profile') else None
        
        if not profile:
            # 프로필이 없으면 인기 영상 반환
            return WorkoutVideo.objects.order_by('-view_count')[:limit]
        
        # 사용자 선호 운동 종류 가져오기
        preferred_exercises = profile.preferred_exercises or []
        
        # 최근 운동 기록에서 선호도 분석
        recent_workouts = WorkoutLog.objects.filter(
            user=user,
            date__gte=timezone.now().date() - timedelta(days=30)
        ).values('workout_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 추천 쿼리 구성
        queryset = WorkoutVideo.objects.select_related('category')
        
        # 난이도에 따른 필터링
        if profile.exercise_experience:
            difficulty_map = {
                'beginner': 'beginner',
                'intermediate': ['beginner', 'intermediate'],
                'advanced': ['intermediate', 'advanced'],
                'expert': 'advanced'
            }
            difficulties = difficulty_map.get(profile.exercise_experience, 'beginner')
            if isinstance(difficulties, list):
                queryset = queryset.filter(difficulty__in=difficulties)
            else:
                queryset = queryset.filter(difficulty=difficulties)
        
        # 선호 운동 종류 우선순위
        if preferred_exercises:
            # 선호 운동과 관련된 카테고리 찾기
            preferred_q = Q()
            for exercise in preferred_exercises:
                preferred_q |= Q(category__name__icontains=exercise)
            
            preferred_videos = queryset.filter(preferred_q)[:limit]
            
            if preferred_videos.count() < limit:
                # 부족한 만큼 인기 영상으로 채우기
                popular_videos = queryset.exclude(
                    id__in=[v.id for v in preferred_videos]
                ).order_by('-view_count')[:(limit - preferred_videos.count())]
                
                return list(preferred_videos) + list(popular_videos)
            
            return list(preferred_videos)
        
        # 선호도가 없으면 인기 영상 반환
        return list(queryset.order_by('-view_count')[:limit])
    
    @staticmethod
    def get_workout_streak(user: User) -> Dict:
        """운동 연속 일수 계산"""
        today = timezone.now().date()
        
        # 최근 운동 기록 조회 (날짜 역순)
        workout_dates = WorkoutLog.objects.filter(
            user=user
        ).values_list('date', flat=True).distinct().order_by('-date')
        
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        last_date = None
        
        for workout_date in workout_dates:
            if last_date is None:
                # 첫 번째 날짜
                if workout_date == today:
                    current_streak = 1
                temp_streak = 1
            else:
                # 연속된 날짜인지 확인
                if (last_date - workout_date).days == 1:
                    temp_streak += 1
                    if workout_date == today or (today - workout_date).days == 1:
                        current_streak = temp_streak
                else:
                    # 연속이 끊김
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            
            last_date = workout_date
        
        longest_streak = max(longest_streak, temp_streak)
        
        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'last_workout_date': workout_dates[0] if workout_dates else None,
            'total_workout_days': len(workout_dates)
        }
