"""
최적화된 API ViewSet
Django REST Framework의 ViewSet을 활용한 성능 최적화
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch, Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import timedelta

from apps.core.models import (
    User, UserProfile, WorkoutLog, DietLog, WorkoutVideo,
    WorkoutCategory, ExerciseLocation, ChatSession, ChatMessage,
    DailyRecommendation
)
from apps.api.serializers import (
    UserSerializer, UserProfileSerializer, WorkoutLogSerializer,
    DietLogSerializer, WorkoutVideoSerializer, WorkoutCategorySerializer,
    ExerciseLocationSerializer, ChatSessionSerializer, ChatMessageSerializer,
    DailyRecommendationSerializer
)
from apps.core.services.user_service import UserService
from apps.core.services.workout_service import WorkoutService
from apps.core.services.nutrition_service import NutritionService

import logging
logger = logging.getLogger(__name__)


class OptimizedUserViewSet(viewsets.ModelViewSet):
    """최적화된 사용자 ViewSet"""
    queryset = User.objects.select_related('profile').prefetch_related(
        'workout_logs', 'diet_logs', 'chat_sessions'
    )
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """사용자는 자신의 정보만 조회 가능"""
        return self.queryset.filter(id=self.request.user.id)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """사용자 통계 정보"""
        user = self.get_object()
        days = int(request.query_params.get('days', 30))
        
        stats = UserService.get_user_statistics(user, days)
        return Response(stats)
    
    @action(detail=True, methods=['get'])
    def recent_activities(self, request, pk=None):
        """최근 활동 내역"""
        user = self.get_object()
        limit = int(request.query_params.get('limit', 10))
        
        activities = UserService.get_user_recent_activities(user, limit)
        return Response({'activities': activities})
    
    @action(detail=True, methods=['post'])
    def update_preferences(self, request, pk=None):
        """사용자 선호도 업데이트"""
        user = self.get_object()
        preferences = request.data
        
        try:
            profile = UserService.update_user_preferences(user, preferences)
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class OptimizedWorkoutViewSet(viewsets.ModelViewSet):
    """최적화된 운동 기록 ViewSet"""
    serializer_class = WorkoutLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """쿼리 최적화 및 필터링"""
        queryset = WorkoutLog.objects.select_related(
            'user', 'video'
        ).prefetch_related(
            'played_music'
        ).filter(user=self.request.user)
        
        # 날짜 필터링
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        workout_type = self.request.query_params.get('workout_type')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if workout_type:
            queryset = queryset.filter(workout_type=workout_type)
        
        return queryset.order_by('-date', '-created_at')
    
    def create(self, request, *args, **kwargs):
        """운동 기록 생성 (최적화)"""
        workout_data = request.data.copy()
        
        try:
            workout_log = WorkoutService.create_workout_log(
                request.user, 
                workout_data
            )
            serializer = self.get_serializer(workout_log)
            return Response(
                serializer.data, 
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """운동 요약 통계"""
        period_days = int(request.query_params.get('days', 30))
        summary = WorkoutService.get_user_workout_summary(
            request.user, 
            period_days
        )
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def streak(self, request):
        """운동 연속 일수"""
        streak_data = WorkoutService.get_workout_streak(request.user)
        return Response(streak_data)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """추천 운동 영상"""
        limit = int(request.query_params.get('limit', 5))
        videos = WorkoutService.get_recommended_workouts(request.user, limit)
        serializer = WorkoutVideoSerializer(videos, many=True)
        return Response(serializer.data)


class OptimizedNutritionViewSet(viewsets.ModelViewSet):
    """최적화된 식단 기록 ViewSet"""
    serializer_class = DietLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """쿼리 최적화 및 필터링"""
        queryset = DietLog.objects.select_related('user').filter(
            user=self.request.user
        )
        
        # 날짜 필터링
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        meal_type = self.request.query_params.get('meal_type')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        if meal_type:
            queryset = queryset.filter(meal_type=meal_type)
        
        return queryset.order_by('-date', 'meal_type')
    
    def create(self, request, *args, **kwargs):
        """식단 기록 생성 (영양 정보 자동 계산)"""
        diet_data = request.data.copy()
        diet_data['user'] = request.user.id
        
        try:
            diet_log = NutritionService.create_diet_log(
                request.user,
                diet_data
            )
            serializer = self.get_serializer(diet_log)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """영양 섭취 요약"""
        period_days = int(request.query_params.get('days', 7))
        summary = NutritionService.get_nutrition_summary(
            request.user,
            period_days
        )
        return Response(summary)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """영양 권장량"""
        recommendations = NutritionService.get_nutrition_recommendations(
            request.user
        )
        return Response(recommendations)
    
    @action(detail=False, methods=['get'])
    def balance_analysis(self, request):
        """영양 균형 분석"""
        days = int(request.query_params.get('days', 7))
        analysis = NutritionService.analyze_nutrition_balance(
            request.user,
            days
        )
        return Response(analysis)


class OptimizedWorkoutVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """최적화된 운동 영상 ViewSet"""
    serializer_class = WorkoutVideoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """쿼리 최적화 및 필터링"""
        queryset = WorkoutVideo.objects.select_related('category')
        
        # 필터링
        category_id = self.request.query_params.get('category')
        difficulty = self.request.query_params.get('difficulty')
        search = self.request.query_params.get('search')
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )
        
        # 정렬
        sort_by = self.request.query_params.get('sort', '-view_count')
        return queryset.order_by(sort_by)
    
    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        """조회수 증가"""
        video = self.get_object()
        WorkoutVideo.objects.filter(id=video.id).update(
            view_count=F('view_count') + 1
        )
        return Response({'status': 'success'})
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """카테고리 목록 (영상 수 포함)"""
        categories = WorkoutService.get_workout_categories_with_counts()
        serializer = WorkoutCategorySerializer(categories, many=True)
        return Response(serializer.data)


class OptimizedExerciseLocationViewSet(viewsets.ReadOnlyModelViewSet):
    """최적화된 운동 장소 ViewSet"""
    queryset = ExerciseLocation.objects.all()
    serializer_class = ExerciseLocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """위치 기반 필터링"""
        queryset = super().get_queryset()
        
        # 위치 파라미터
        latitude = self.request.query_params.get('latitude')
        longitude = self.request.query_params.get('longitude')
        radius = float(self.request.query_params.get('radius', 5.0))
        location_type = self.request.query_params.get('type')
        
        if latitude and longitude:
            locations = WorkoutService.get_nearby_exercise_locations(
                float(latitude),
                float(longitude),
                radius,
                location_type
            )
            # ID 목록으로 필터링
            location_ids = [loc.id for loc in locations]
            queryset = queryset.filter(id__in=location_ids)
        elif location_type:
            queryset = queryset.filter(location_type=location_type)
        
        return queryset.order_by('-rating', '-review_count')
    
    @action(detail=False, methods=['get'])
    def types(self, request):
        """장소 유형 목록"""
        types = ExerciseLocation.LOCATION_TYPE_CHOICES
        return Response({
            'types': [{'value': t[0], 'label': t[1]} for t in types]
        })


class OptimizedChatSessionViewSet(viewsets.ModelViewSet):
    """최적화된 챗봇 세션 ViewSet"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """사용자 세션만 조회"""
        return ChatSession.objects.filter(
            user=self.request.user
        ).select_related('user').prefetch_related(
            Prefetch(
                'messages',
                queryset=ChatMessage.objects.order_by('created_at')
            )
        ).order_by('-started_at')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """활성 세션 조회"""
        session = UserService.get_active_chat_session(request.user)
        if session:
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        return Response({'message': 'No active session'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def start_new(self, request):
        """새 세션 시작"""
        session = UserService.create_chat_session(request.user)
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """세션 종료"""
        session = self.get_object()
        session.end_session()
        return Response({'message': 'Session ended successfully'})
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """세션 메시지 조회"""
        session = self.get_object()
        messages = session.messages.order_by('created_at')
        
        # 페이지네이션
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = ChatMessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ChatMessageSerializer(messages, many=True)
        return Response(serializer.data)


class OptimizedDailyRecommendationViewSet(viewsets.ReadOnlyModelViewSet):
    """최적화된 일일 추천 ViewSet"""
    serializer_class = DailyRecommendationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """사용자 추천만 조회"""
        queryset = DailyRecommendation.objects.filter(
            user=self.request.user
        ).select_related('user')
        
        # 날짜 필터링
        date = self.request.query_params.get('date')
        recommendation_type = self.request.query_params.get('type')
        
        if date:
            queryset = queryset.filter(date=date)
        else:
            # 기본값: 오늘
            queryset = queryset.filter(date=timezone.now().date())
        
        if recommendation_type:
            queryset = queryset.filter(type=recommendation_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, pk=None):
        """추천에 대한 피드백"""
        recommendation = self.get_object()
        is_accepted = request.data.get('is_accepted')
        feedback = request.data.get('feedback', '')
        
        recommendation.is_accepted = is_accepted
        recommendation.user_feedback = feedback
        recommendation.save(update_fields=['is_accepted', 'user_feedback'])
        
        return Response({'message': 'Feedback saved successfully'})
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """오늘의 추천"""
        today_recommendations = self.get_queryset().filter(
            date=timezone.now().date()
        )
        serializer = self.get_serializer(today_recommendations, many=True)
        return Response({
            'date': timezone.now().date().isoformat(),
            'recommendations': serializer.data
        })
