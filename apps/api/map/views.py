from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Q
import math
from .models import FitnessProfile, WorkoutRecord, MusicPreference, WorkoutMusic
from apps.core.models import ExerciseLocation
from .serializers import (
    FitnessProfileSerializer, WorkoutRecordSerializer,
    MusicPreferenceSerializer, WorkoutMusicSerializer,
    UserProfileSerializer
)


class FitnessProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint for fitness profiles
    """
    serializer_class = FitnessProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FitnessProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkoutRecordViewSet(viewsets.ModelViewSet):
    """
    API endpoint for workout records
    """
    serializer_class = WorkoutRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WorkoutRecord.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get workout statistics for the current user"""
        records = self.get_queryset()
        total_workouts = records.count()
        total_duration = sum(r.duration for r in records)
        total_distance = sum(r.distance or 0 for r in records)
        total_calories = sum(r.calories_burned or 0 for r in records)
        
        stats = {
            'total_workouts': total_workouts,
            'total_duration': total_duration,
            'total_distance': total_distance,
            'total_calories': total_calories,
            'workout_types': records.values('workout_type').distinct()
        }
        
        return Response(stats)


class MusicPreferenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for music preferences
    """
    serializer_class = MusicPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return MusicPreference.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user profile with fitness data
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_exercise_locations(request):
    """
    운동 장소 검색 API
    
    Query Parameters:
    - latitude: 위도
    - longitude: 경도
    - radius: 검색 반경 (km)
    - type: 장소 유형 (optional)
    """
    try:
        latitude = float(request.GET.get('latitude', 0))
        longitude = float(request.GET.get('longitude', 0))
        radius = float(request.GET.get('radius', 5))  # 기본 5km
        location_type = request.GET.get('type', None)
        
        if not latitude or not longitude:
            return Response(
                {'error': '위도와 경도가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Haversine 공식을 사용한 거리 계산을 위한 좌표 범위 계산
        # 대략적인 위도/경도 차이 계산 (1도 ≈ 111km)
        lat_range = radius / 111
        lon_range = radius / (111 * math.cos(math.radians(latitude)))
        
        # 범위 내 장소 필터링
        locations = ExerciseLocation.objects.filter(
            latitude__range=(latitude - lat_range, latitude + lat_range),
            longitude__range=(longitude - lon_range, longitude + lon_range)
        )
        
        if location_type:
            locations = locations.filter(location_type=location_type)
        
        # 거리 계산 및 정렬
        results = []
        for location in locations:
            # Haversine 공식으로 정확한 거리 계산
            lat1, lon1 = math.radians(latitude), math.radians(longitude)
            lat2, lon2 = math.radians(location.latitude), math.radians(location.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = 6371 * c  # 지구 반경 (km)
            
            if distance <= radius:
                results.append({
                    'id': location.id,
                    'name': location.name,
                    'type': location.location_type,
                    'type_display': location.get_location_type_display(),
                    'address': location.address,
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'distance': round(distance, 2),
                    'phone': location.phone,
                    'website': location.website,
                    'operating_hours': location.operating_hours,
                    'rating': location.rating,
                    'review_count': location.review_count,
                })
        
        # 거리순으로 정렬
        results.sort(key=lambda x: x['distance'])
        
        return Response({
            'count': len(results),
            'results': results
        })
        
    except ValueError as e:
        return Response(
            {'error': '잘못된 파라미터 형식입니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
