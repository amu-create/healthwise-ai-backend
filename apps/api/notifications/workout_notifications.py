from datetime import timedelta
from django.utils import timezone
from apps.api.notification_service_v2 import NotificationService
from apps.api.models import WorkoutRoutineLog
import logging

logger = logging.getLogger(__name__)


class WorkoutNotificationService:
    """운동 관련 알림 서비스"""
    
    @staticmethod
    def send_workout_completed_notification(user, workout_log):
        """운동 완료 알림"""
        workout_name = workout_log.routine.name if workout_log.routine else "운동"
        calories = workout_log.calories_burned or 0
        duration = workout_log.duration or 0
        
        NotificationService.create_notification(
            user=user,
            notification_type='workout',
            title_ko='운동 완료!',
            title_en='Workout Completed!',
            title_es='¡Ejercicio Completado!',
            message_ko=f'{workout_name}을(를) {duration}분 동안 수행하여 {calories}kcal를 소모했습니다!',
            message_en=f'You completed {workout_name} for {duration} minutes and burned {calories}kcal!',
            message_es=f'¡Completaste {workout_name} durante {duration} minutos y quemaste {calories}kcal!',
            metadata={
                'icon': 'fitness',
                'workout_id': workout_log.id,
                'duration': duration,
                'calories': calories
            },
            action_url='/workouts/history'
        )
        
        # 연속 운동 체크
        WorkoutNotificationService.check_workout_streak(user)
    
    @staticmethod
    def check_workout_streak(user):
        """연속 운동 기록 체크 및 알림"""
        today = timezone.now().date()
        
        # 최근 30일간의 운동 기록 확인
        workout_dates = set(
            WorkoutRoutineLog.objects.filter(
                user=user,
                completed_at__gte=today - timedelta(days=30)
            ).values_list('completed_at__date', flat=True)
        )
        
        # 연속 일수 계산
        streak = 0
        check_date = today
        
        while check_date in workout_dates:
            streak += 1
            check_date -= timedelta(days=1)
        
        # 마일스톤 알림
        milestones = {
            3: ('3일 연속 운동!', '3 Day Workout Streak!', '¡3 días consecutivos de ejercicio!'),
            7: ('일주일 연속 운동!', '1 Week Workout Streak!', '¡1 semana consecutiva de ejercicio!'),
            14: ('2주 연속 운동!', '2 Week Workout Streak!', '¡2 semanas consecutivas de ejercicio!'),
            30: ('한 달 연속 운동!', '1 Month Workout Streak!', '¡1 mes consecutivo de ejercicio!'),
            50: ('50일 연속 운동!', '50 Day Workout Streak!', '¡50 días consecutivos de ejercicio!'),
            100: ('100일 연속 운동!', '100 Day Workout Streak!', '¡100 días consecutivos de ejercicio!'),
        }
        
        if streak in milestones:
            title_ko, title_en, title_es = milestones[streak]
            
            NotificationService.create_notification(
                user=user,
                notification_type='achievement',
                title_ko=title_ko,
                title_en=title_en,
                title_es=title_es,
                message_ko=f'대단해요! {streak}일 연속으로 운동을 완료했습니다! 💪',
                message_en=f'Amazing! You\'ve completed workouts for {streak} consecutive days! 💪',
                message_es=f'¡Increíble! ¡Has completado ejercicios durante {streak} días consecutivos! 💪',
                metadata={
                    'icon': 'achievement',
                    'streak_days': streak,
                    'badge_type': 'workout_streak'
                },
                action_url='/achievements'
            )
            
            # 실시간 알림 전송
            NotificationService.send_realtime_notification(user, {
                'type': 'achievement_unlocked',
                'achievement': {
                    'name': f'{streak}일 연속 운동',
                    'name_en': f'{streak} Day Workout Streak',
                    'name_es': f'{streak} días consecutivos',
                    'badge_level': 'gold' if streak >= 30 else 'silver' if streak >= 7 else 'bronze',
                    'points': streak * 10
                },
                'animation': True
            })
    
    @staticmethod
    def send_workout_reminder(user, scheduled_time):
        """운동 리마인더 알림"""
        NotificationService.create_notification(
            user=user,
            notification_type='reminder',
            title_ko='운동 시간입니다!',
            title_en='Time to Work Out!',
            title_es='¡Hora de Ejercitarse!',
            message_ko=f'설정하신 {scheduled_time.strftime("%H:%M")} 운동 시간이 되었습니다. 오늘도 화이팅!',
            message_en=f'It\'s your scheduled workout time at {scheduled_time.strftime("%H:%M")}. Let\'s go!',
            message_es=f'Es tu hora programada de ejercicio a las {scheduled_time.strftime("%H:%M")}. ¡Vamos!',
            metadata={
                'icon': 'alarm',
                'scheduled_time': scheduled_time.isoformat(),
                'reminder_type': 'workout'
            },
            action_url='/workouts'
        )
    
    @staticmethod
    def send_workout_goal_progress(user, goal_type, current_value, target_value):
        """운동 목표 진행 상황 알림"""
        progress_percentage = int((current_value / target_value) * 100)
        
        goal_types = {
            'weekly_workouts': ('주간 운동 목표', 'Weekly Workout Goal', 'Meta de Ejercicio Semanal'),
            'monthly_workouts': ('월간 운동 목표', 'Monthly Workout Goal', 'Meta de Ejercicio Mensual'),
            'weekly_minutes': ('주간 운동 시간', 'Weekly Exercise Minutes', 'Minutos de Ejercicio Semanal'),
            'monthly_calories': ('월간 칼로리 소모', 'Monthly Calories Burned', 'Calorías Quemadas Mensuales'),
        }
        
        goal_name_ko, goal_name_en, goal_name_es = goal_types.get(
            goal_type,
            ('운동 목표', 'Workout Goal', 'Meta de Ejercicio')
        )
        
        if progress_percentage >= 100:
            # 목표 달성
            NotificationService.create_notification(
                user=user,
                notification_type='achievement',
                title_ko='목표 달성! 🎉',
                title_en='Goal Achieved! 🎉',
                title_es='¡Meta Lograda! 🎉',
                message_ko=f'{goal_name_ko}를 달성했습니다! ({current_value}/{target_value})',
                message_en=f'You achieved your {goal_name_en}! ({current_value}/{target_value})',
                message_es=f'¡Lograste tu {goal_name_es}! ({current_value}/{target_value})',
                metadata={
                    'icon': 'trophy',
                    'goal_type': goal_type,
                    'achievement_value': current_value,
                    'target_value': target_value
                },
                action_url='/goals'
            )
        elif progress_percentage >= 80:
            # 목표 근접
            NotificationService.create_notification(
                user=user,
                notification_type='progress',
                title_ko='목표가 눈앞에!',
                title_en='Almost There!',
                title_es='¡Casi lo Logras!',
                message_ko=f'{goal_name_ko} {progress_percentage}% 달성! 조금만 더 힘내세요!',
                message_en=f'{progress_percentage}% of your {goal_name_en} completed! Keep going!',
                message_es=f'¡{progress_percentage}% de tu {goal_name_es} completado! ¡Sigue así!',
                metadata={
                    'icon': 'progress',
                    'goal_type': goal_type,
                    'progress': progress_percentage,
                    'current_value': current_value,
                    'target_value': target_value
                },
                action_url='/goals'
            )
    
    @staticmethod
    def send_workout_intensity_suggestion(user, recent_workouts):
        """운동 강도 증가 제안 알림"""
        # 최근 운동들의 평균 강도 분석
        avg_duration = sum(w.duration for w in recent_workouts) / len(recent_workouts)
        avg_calories = sum(w.calories_burned for w in recent_workouts) / len(recent_workouts)
        
        if len(recent_workouts) >= 10:  # 10회 이상 운동 기록이 있을 때
            NotificationService.create_notification(
                user=user,
                notification_type='suggestion',
                title_ko='운동 레벨업 제안',
                title_en='Level Up Your Workout',
                title_es='Mejora tu Entrenamiento',
                message_ko=f'최근 운동이 안정적으로 진행되고 있어요. 강도를 조금 높여보는 건 어떨까요?',
                message_en=f'Your workouts have been consistent. Ready to increase the intensity?',
                message_es=f'Tus entrenamientos han sido consistentes. ¿Listo para aumentar la intensidad?',
                metadata={
                    'icon': 'trending_up',
                    'avg_duration': avg_duration,
                    'avg_calories': avg_calories,
                    'suggestion_type': 'intensity_increase'
                },
                action_url='/workouts/plans'
            )
    
    @staticmethod
    def send_rest_day_reminder(user, consecutive_workout_days):
        """휴식일 권장 알림"""
        if consecutive_workout_days >= 6:
            NotificationService.create_notification(
                user=user,
                notification_type='health',
                title_ko='휴식도 중요해요',
                title_en='Rest is Important Too',
                title_es='El Descanso También es Importante',
                message_ko=f'{consecutive_workout_days}일 연속 운동하셨네요! 오늘은 가벼운 스트레칭이나 휴식을 추천드려요.',
                message_en=f'You\'ve worked out for {consecutive_workout_days} days straight! Consider light stretching or rest today.',
                message_es=f'¡Has entrenado durante {consecutive_workout_days} días seguidos! Considera estiramientos ligeros o descanso hoy.',
                metadata={
                    'icon': 'rest',
                    'consecutive_days': consecutive_workout_days,
                    'suggestion_type': 'rest_day'
                },
                action_url='/workouts/recovery'
            )
