from django.urls import path
from . import views

urlpatterns = [
    path('ai-keywords/', views.get_ai_keywords, name='get_ai_keywords'),
    path('youtube-api-key/', views.get_youtube_api_key, name='get_youtube_api_key'),
    path('save-feedback/', views.save_playlist_feedback, name='save_playlist_feedback'),
    path('youtube-search/', views.youtube_search, name='youtube_search'),
    path('popular-tracks/', views.get_popular_tracks, name='get_popular_tracks'),
]
