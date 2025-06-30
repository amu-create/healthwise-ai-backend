from django.apps import AppConfig


class WorkoutConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workout'
    verbose_name = '운동 관리'
