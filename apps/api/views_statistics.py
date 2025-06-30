from django.db.models import Sum, Count, Avg, Q, F
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta
from apps.core.models import WorkoutLog, UserProfile
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workout_statistics(request):
    """
    사용자의 운동 통계를 반환합니다.
    기간별 (주간/월간/연간) 통계를 제공합니다.
    """
    try:
        user = request.user
        period = request.GET.get('period', 'week')  # week, month, year
        
        # 현재 시간 기준으로 기간 설정
        now = timezone.now()
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=7)
        
        # 기간 내 운동 기록 조회
        workouts = WorkoutLog.objects.filter(
            user=user,
            date__gte=start_date.date()
        )
        
        # 통계 계산
        stats = {
            'period': period,
            'start_date': start_date.date().isoformat(),
            'end_date': now.date().isoformat(),
            'total_workouts': workouts.count(),
            'total_duration': workouts.aggregate(Sum('duration'))['duration__sum'] or 0,
            'total_calories': workouts.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0,
            'total_distance': workouts.aggregate(Sum('distance'))['distance__sum'] or 0,
            'avg_duration': workouts.aggregate(Avg('duration'))['duration__avg'] or 0,
            'avg_calories': workouts.aggregate(Avg('calories_burned'))['calories_burned__avg'] or 0,
            'avg_distance': workouts.aggregate(Avg('distance'))['distance__avg'] or 0,
        }
        
        # 운동 유형별 통계
        workout_types = workouts.values('workout_type').annotate(
            count=Count('id'),
            total_duration=Sum('duration'),
            total_calories=Sum('calories_burned')
        ).order_by('-count')
        
        stats['workout_types'] = list(workout_types)
        
        # 일별 운동 횟수 (최근 7일)
        daily_stats = []
        for i in range(7):
            date = (now - timedelta(days=i)).date()
            count = workouts.filter(date=date).count()
            daily_stats.append({
                'date': date.isoformat(),
                'count': count
            })
        stats['daily_stats'] = daily_stats
        
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Error getting workout statistics: {str(e)}")
        return Response(
            {'error': 'Failed to get workout statistics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workout_goals(request):
    """
    사용자의 운동 목표 정보를 반환합니다.
    """
    try:
        user = request.user
        profile = user.profile
        
        goals = {
            'goal': profile.goal,
            'custom_goal': profile.custom_goal,
            'workout_days_per_week': profile.workout_days_per_week,
            'weekly_workout_goal': profile.weekly_workout_goal,
            'monthly_distance_goal': profile.monthly_distance_goal,
            'monthly_calories_goal': profile.monthly_calories_goal,
            'daily_steps_goal': profile.daily_steps_goal,
            'weight_unit': profile.weight_unit,
            'distance_unit': profile.distance_unit,
        }
        
        return Response(goals)
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting workout goals: {str(e)}")
        return Response(
            {'error': 'Failed to get workout goals'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_workout_goals(request):
    """
    사용자의 운동 목표를 업데이트합니다.
    """
    try:
        user = request.user
        profile = user.profile
        
        # 업데이트 가능한 필드들
        updatable_fields = [
            'goal', 'custom_goal', 'workout_days_per_week',
            'weekly_workout_goal', 'monthly_distance_goal',
            'monthly_calories_goal', 'daily_steps_goal',
            'weight_unit', 'distance_unit'
        ]
        
        # 요청 데이터에서 업데이트할 필드만 추출
        update_data = {}
        for field in updatable_fields:
            if field in request.data:
                update_data[field] = request.data[field]
        
        # 프로필 업데이트
        for field, value in update_data.items():
            setattr(profile, field, value)
        profile.save()
        
        # 업데이트된 목표 정보 반환
        goals = {
            'goal': profile.goal,
            'custom_goal': profile.custom_goal,
            'workout_days_per_week': profile.workout_days_per_week,
            'weekly_workout_goal': profile.weekly_workout_goal,
            'monthly_distance_goal': profile.monthly_distance_goal,
            'monthly_calories_goal': profile.monthly_calories_goal,
            'daily_steps_goal': profile.daily_steps_goal,
            'weight_unit': profile.weight_unit,
            'distance_unit': profile.distance_unit,
        }
        
        return Response(goals)
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error updating workout goals: {str(e)}")
        return Response(
            {'error': 'Failed to update workout goals'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def workout_summary(request):
    """
    사용자의 운동 요약 정보와 목표 달성률을 반환합니다.
    """
    try:
        user = request.user
        profile = user.profile
        now = timezone.now()
        
        # 이번 주 시작일 (월요일)
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 이번 달 시작일
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # 주간 운동 횟수
        weekly_workouts = WorkoutLog.objects.filter(
            user=user,
            date__gte=week_start.date()
        ).count()
        
        # 월간 통계
        monthly_workouts = WorkoutLog.objects.filter(
            user=user,
            date__gte=month_start.date()
        )
        
        monthly_distance = monthly_workouts.aggregate(Sum('distance'))['distance__sum'] or 0
        monthly_calories = monthly_workouts.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0
        
        # 오늘 걸음 수 (가장 최근 운동 기록에서)
        today_steps = WorkoutLog.objects.filter(
            user=user,
            date=now.date()
        ).aggregate(Sum('steps'))['steps__sum'] or 0
        
        # 목표 달성률 계산
        weekly_progress = (weekly_workouts / profile.weekly_workout_goal * 100) if profile.weekly_workout_goal > 0 else 0
        distance_progress = (monthly_distance / profile.monthly_distance_goal * 100) if profile.monthly_distance_goal > 0 else 0
        calories_progress = (monthly_calories / profile.monthly_calories_goal * 100) if profile.monthly_calories_goal > 0 else 0
        steps_progress = (today_steps / profile.daily_steps_goal * 100) if profile.daily_steps_goal > 0 else 0
        
        summary = {
            'current_stats': {
                'weekly_workouts': weekly_workouts,
                'monthly_distance': round(monthly_distance, 2),
                'monthly_calories': monthly_calories,
                'today_steps': today_steps,
            },
            'goals': {
                'weekly_workout_goal': profile.weekly_workout_goal,
                'monthly_distance_goal': profile.monthly_distance_goal,
                'monthly_calories_goal': profile.monthly_calories_goal,
                'daily_steps_goal': profile.daily_steps_goal,
            },
            'progress': {
                'weekly_workout_progress': round(weekly_progress, 1),
                'monthly_distance_progress': round(distance_progress, 1),
                'monthly_calories_progress': round(calories_progress, 1),
                'daily_steps_progress': round(steps_progress, 1),
            },
            'units': {
                'weight': profile.weight_unit,
                'distance': profile.distance_unit,
            }
        }
        
        # 연속 운동 일수 계산
        consecutive_days = calculate_consecutive_days(user)
        summary['consecutive_days'] = consecutive_days
        
        return Response(summary)
        
    except UserProfile.DoesNotExist:
        return Response(
            {'error': 'User profile not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error getting workout summary: {str(e)}")
        return Response(
            {'error': 'Failed to get workout summary'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def calculate_consecutive_days(user):
    """
    사용자의 연속 운동 일수를 계산합니다.
    """
    today = timezone.now().date()
    consecutive_days = 0
    current_date = today
    
    while True:
        if WorkoutLog.objects.filter(user=user, date=current_date).exists():
            consecutive_days += 1
            current_date -= timedelta(days=1)
        else:
            # 어제 운동하지 않았다면 오늘 운동했는지 확인
            if current_date == today - timedelta(days=1):
                if WorkoutLog.objects.filter(user=user, date=today).exists():
                    consecutive_days = 1
            break
    
    return consecutive_days
