from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkoutResultViewSet, WorkoutGoalViewSet

router = DefaultRouter()
router.register(r'workout-results', WorkoutResultViewSet, basename='workoutresult')
router.register(r'workout-goals', WorkoutGoalViewSet, basename='workoutgoal')

urlpatterns = [
    path('', include(router.urls)),
]
