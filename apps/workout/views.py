from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Avg, Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import WorkoutResult, WorkoutGoal
from .serializers import (
    WorkoutResultSerializer, 
    WorkoutGoalSerializer,
    ShareWorkoutResultSerializer
)
from apps.achievements.services import check_workout_achievements


class WorkoutResultViewSet(viewsets.ModelViewSet):
    """운동 결과 뷰셋"""
    serializer_class = WorkoutResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = WorkoutResult.objects.filter(user=self.request.user)
        
        # 필터링
        exercise_name = self.request.query_params.get('exercise_name')
        if exercise_name:
            queryset = queryset.filter(exercise_name=exercise_name)
        
        exercise_type = self.request.query_params.get('exercise_type')
        if exercise_type:
            queryset = queryset.filter(exercise_type=exercise_type)
        
        # 날짜 필터링
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        workout_result = serializer.save(user=self.request.user)
        
        # 업적 체크
        new_achievements = check_workout_achievements(self.request.user, workout_result)
        
        # 응답에 새로운 업적 정보 추가
        if new_achievements:
            serializer._new_achievements = new_achievements
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        response_data = serializer.data
        if hasattr(serializer, '_new_achievements'):
            response_data['new_achievements'] = serializer._new_achievements
        
        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)
    
    @action(detail=True, methods=['post'])
    def check_achievements(self, request, pk=None):
        """운동 결과에 대한 업적 체크"""
        workout_result = self.get_object()
        new_achievements = check_workout_achievements(request.user, workout_result)
        
        return Response({
            'new_achievements': new_achievements,
            'message': f"{len(new_achievements)}개의 새로운 업적을 달성했습니다!" if new_achievements else "새로운 업적이 없습니다."
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """운동 통계"""
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        results = self.get_queryset().filter(created_at__gte=start_date)
        
        # 전체 통계
        total_stats = results.aggregate(
            total_workouts=Count('id'),
            total_duration=Sum('duration'),
            avg_score=Avg('average_score'),
            total_calories=Sum('calories_burned'),
            total_reps=Sum('rep_count')
        )
        
        # 운동별 통계
        exercise_stats = results.values('exercise_name').annotate(
            count=Count('id'),
            avg_duration=Avg('duration'),
            avg_score=Avg('average_score'),
            total_calories=Sum('calories_burned'),
            total_reps=Sum('rep_count')
        ).order_by('-count')
        
        # 일별 통계
        daily_stats = []
        for i in range(days):
            date = (timezone.now() - timedelta(days=i)).date()
            day_results = results.filter(created_at__date=date)
            daily_stats.append({
                'date': date,
                'workouts': day_results.count(),
                'duration': day_results.aggregate(Sum('duration'))['duration__sum'] or 0,
                'calories': day_results.aggregate(Sum('calories_burned'))['calories_burned__sum'] or 0
            })
        
        return Response({
            'total_stats': total_stats,
            'exercise_stats': list(exercise_stats),
            'daily_stats': daily_stats
        })
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """최근 운동 결과"""
        limit = int(request.query_params.get('limit', 10))
        results = self.get_queryset()[:limit]
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)


class WorkoutGoalViewSet(viewsets.ModelViewSet):
    """운동 목표 뷰셋"""
    serializer_class = WorkoutGoalSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = WorkoutGoal.objects.filter(user=self.request.user)
        
        # 활성 목표만 필터링
        active_only = self.request.query_params.get('active_only', 'false').lower() == 'true'
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        # 같은 운동의 기존 활성 목표는 비활성화
        exercise_name = serializer.validated_data['exercise_name']
        WorkoutGoal.objects.filter(
            user=self.request.user,
            exercise_name=exercise_name,
            is_active=True
        ).update(is_active=False)
        
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """목표 비활성화"""
        goal = self.get_object()
        goal.is_active = False
        goal.save()
        
        serializer = self.get_serializer(goal)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def progress_summary(self, request):
        """전체 목표 진행 상황 요약"""
        active_goals = self.get_queryset().filter(is_active=True)
        
        summary = []
        for goal in active_goals:
            serializer = self.get_serializer(goal)
            goal_data = serializer.data
            summary.append({
                'goal': goal_data,
                'recent_workouts': WorkoutResultSerializer(
                    WorkoutResult.objects.filter(
                        user=request.user,
                        exercise_name=goal.exercise_name,
                        created_at__gte=goal.start_date
                    ).order_by('-created_at')[:3],
                    many=True
                ).data
            })
        
        return Response(summary)
