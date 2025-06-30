from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FitnessProfileViewSet, WorkoutRecordViewSet,
    MusicPreferenceViewSet, UserProfileViewSet,
    get_exercise_locations
)
from .views_location import get_user_location

router = DefaultRouter()
router.register(r'fitness-profiles', FitnessProfileViewSet, basename='fitness-profile')
router.register(r'workouts', WorkoutRecordViewSet, basename='workout')
router.register(r'music-preferences', MusicPreferenceViewSet, basename='music-preference')
router.register(r'user-profile', UserProfileViewSet, basename='user-profile')

urlpatterns = [
    path('', include(router.urls)),
    path('exercise-locations/', get_exercise_locations, name='exercise-locations'),
    path('user-location/', get_user_location, name='user-location'),
]
