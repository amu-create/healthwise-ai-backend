from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'exercises', views.ExerciseViewSet, basename='exercise')
router.register(r'sessions', views.AnalysisSessionViewSet, basename='analysis-session')
router.register(r'stats', views.UserExerciseStatsViewSet, basename='user-stats')

app_name = 'pose_analysis'

urlpatterns = [
    path('', include(router.urls)),
]
