from datetime import timedelta, datetime
from django.utils import timezone
from apps.api.notification_service_v2 import NotificationService
from apps.api.models import UserProfile, WorkoutRoutineLog
import logging
import random

logger = logging.getLogger(__name__)


class MotivationNotificationService:
    """동기부여 알림 서비스"""
    
    # 동기부여 메시지 풀
    DAILY_MOTIVATION_MESSAGES = [
        {
            'ko': '오늘도 최선을 다하는 당신, 멋져요! 💪',
            'en': 'You\'re doing your best today, amazing! 💪',
            'es': '¡Estás dando lo mejor de ti hoy, increíble! 💪'
        },
        {
            'ko': '작은 변화가 큰 결과를 만듭니다. 계속해요!',
            'en': 'Small changes create big results. Keep going!',
            'es': '¡Los pequeños cambios crean grandes resultados. Sigue adelante!'
        },
        {
            'ko': '어제의 당신보다 오늘의 당신이 더 강해졌어요!',
            'en': 'You\'re stronger today than you were yesterday!',
            'es': '¡Eres más fuerte hoy que ayer!'
        },
        {
            'ko': '포기하지 마세요. 시작이 반입니다!',
            'en': 'Don\'t give up. Starting is half the battle!',
            'es': '¡No te rindas. Empezar es la mitad de la batalla!'
        },
        {
            'ko': '당신의 노력은 반드시 결실을 맺을 거예요! 🌟',
            'en': 'Your efforts will definitely pay off! 🌟',
            'es': '¡Tus esfuerzos definitivamente darán frutos! 🌟'
        }
    ]
    
    @staticmethod
    def send_daily_motivation(user):
        """일일 동기부여 메시지"""
        # 사용자의 현재 상태 분석
        user_profile = getattr(user, 'profile', None)
        recent_workouts = WorkoutRoutineLog.objects.filter(
            user=user,
            completed_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # 맞춤형 메시지 선택
        if recent_workouts == 0:
            message_data = {
                'ko': '운동을 시작하기 좋은 날이에요! 작은 것부터 시작해볼까요? 🌱',
                'en': 'It\'s a great day to start exercising! Shall we start small? 🌱',
                'es': '¡Es un gran día para empezar a ejercitarse! ¿Empezamos poco a poco? 🌱'
            }
        elif recent_workouts >= 5:
            message_data = {
                'ko': '대단해요! 이번 주도 열심히 운동하셨네요! 🔥',
                'en': 'Amazing! You\'ve been working out hard this week! 🔥',
                'es': '¡Increíble! ¡Has estado entrenando duro esta semana! 🔥'
            }
        else:
            message_data = random.choice(DAILY_MOTIVATION_MESSAGES)
        
        NotificationService.create_notification(
            user=user,
            notification_type='motivation',
            title_ko='오늘의 동기부여',
            title_en='Daily Motivation',
            title_es='Motivación Diaria',
            message_ko=message_data['ko'],
            message_en=message_data['en'],
            message_es=message_data['es'],
            metadata={
                'icon': 'motivation',
                'message_type': 'daily',
                'recent_workout_count': recent_workouts
            },
            action_url='/dashboard'
        )
    
    @staticmethod
    def send_workout_encouragement(user, workout_context):
        """운동 격려 메시지"""
        workout_type = workout_context.get('type', 'workout')
        duration = workout_context.get('duration', 0)
        
        if duration < 20:
            NotificationService.create_notification(
                user=user,
                notification_type='motivation',
                title_ko='좋은 시작이에요!',
                title_en='Great Start!',
                title_es='¡Buen Comienzo!',
                message_ko='짧은 운동도 운동입니다! 꾸준함이 중요해요 👏',
                message_en='Even a short workout counts! Consistency is key 👏',
                message_es='¡Incluso un ejercicio corto cuenta! La consistencia es clave 👏',
                metadata={
                    'icon': 'encouragement',
                    'workout_type': workout_type,
                    'duration': duration
                },
                action_url='/workouts'
            )
        elif duration >= 60:
            NotificationService.create_notification(
                user=user,
                notification_type='motivation',
                title_ko='정말 대단해요!',
                title_en='Absolutely Amazing!',
                title_es='¡Absolutamente Increíble!',
                message_ko=f'{duration}분 운동 완료! 당신은 진정한 운동 전사예요! 🏆',
                message_en=f'{duration} minutes completed! You\'re a true fitness warrior! 🏆',
                message_es=f'¡{duration} minutos completados! ¡Eres un verdadero guerrero del fitness! 🏆',
                metadata={
                    'icon': 'trophy',
                    'workout_type': workout_type,
                    'duration': duration
                },
                action_url='/achievements'
            )
    
    @staticmethod
    def send_goal_celebration(user, goal_data):
        """목표 달성 축하 메시지"""
        goal_type = goal_data.get('type')
        achievement_value = goal_data.get('value')
        
        celebrations = {
            'weight_loss': {
                'title': ('체중 감량 성공!', 'Weight Loss Success!', '¡Éxito en Pérdida de Peso!'),
                'message': (f'{achievement_value}kg 감량에 성공했어요! 당신의 노력이 빛나고 있어요! ✨',
                           f'You\'ve lost {achievement_value}kg! Your efforts are shining! ✨',
                           f'¡Has perdido {achievement_value}kg! ¡Tus esfuerzos están brillando! ✨')
            },
            'muscle_gain': {
                'title': ('근육량 증가!', 'Muscle Gain!', '¡Ganancia Muscular!'),
                'message': ('꾸준한 운동의 결과가 나타나고 있어요! 💪',
                           'The results of your consistent workouts are showing! 💪',
                           '¡Los resultados de tus entrenamientos constantes se están mostrando! 💪')
            },
            'streak': {
                'title': ('연속 운동 달성!', 'Workout Streak Achieved!', '¡Racha de Ejercicio Lograda!'),
                'message': (f'{achievement_value}일 연속 운동! 습관이 만들어지고 있어요! 🔥',
                           f'{achievement_value} days in a row! You\'re building a habit! 🔥',
                           f'¡{achievement_value} días seguidos! ¡Estás creando un hábito! 🔥')
            }
        }
        
        if goal_type in celebrations:
            celebration = celebrations[goal_type]
            title_ko, title_en, title_es = celebration['title']
            message_ko, message_en, message_es = celebration['message']
            
            NotificationService.create_notification(
                user=user,
                notification_type='celebration',
                title_ko=title_ko,
                title_en=title_en,
                title_es=title_es,
                message_ko=message_ko,
                message_en=message_en,
                message_es=message_es,
                metadata={
                    'icon': 'celebration',
                    'goal_type': goal_type,
                    'achievement_value': achievement_value,
                    'animation': True
                },
                action_url='/achievements'
            )
            
            # 실시간 축하 애니메이션
            NotificationService.send_realtime_notification(user, {
                'type': 'celebration',
                'animation': 'confetti',
                'duration': 3000
            })
    
    @staticmethod
    def send_friend_achievement_notification(user, friend, achievement):
        """운동 친구의 성과 알림"""
        friend_profile = getattr(friend, 'social_profile', None)
        
        NotificationService.create_notification(
            user=user,
            notification_type='social',
            title_ko='친구의 성과',
            title_en='Friend\'s Achievement',
            title_es='Logro del Amigo',
            message_ko=f'{friend.username}님이 {achievement.name}을(를) 달성했어요! 축하 메시지를 보내보세요 🎉',
            message_en=f'{friend.username} achieved {achievement.name_en or achievement.name}! Send a congratulations 🎉',
            message_es=f'¡{friend.username} logró {achievement.name_es or achievement.name}! Envía felicitaciones 🎉',
            metadata={
                'icon': 'people',
                'friend_id': friend.id,
                'friend_username': friend.username,
                'friend_profile_picture': friend_profile.profile_picture_url if friend_profile else None,
                'achievement_name': achievement.name,
                'achievement_points': achievement.points
            },
            action_url=f'/profile/{friend.username}'
        )
    
    @staticmethod
    def send_comeback_motivation(user, days_inactive):
        """복귀 동기부여 메시지"""
        if days_inactive >= 7:
            NotificationService.create_notification(
                user=user,
                notification_type='motivation',
                title_ko='다시 만나서 반가워요!',
                title_en='Welcome Back!',
                title_es='¡Bienvenido de Nuevo!',
                message_ko='잠시 쉬어가는 것도 괜찮아요. 오늘부터 다시 시작해볼까요? 🌈',
                message_en='It\'s okay to take a break. Ready to start again today? 🌈',
                message_es='Está bien tomar un descanso. ¿Listo para empezar de nuevo hoy? 🌈',
                metadata={
                    'icon': 'comeback',
                    'days_inactive': days_inactive,
                    'message_type': 'comeback'
                },
                action_url='/workouts/quick-start'
            )
    
    @staticmethod
    def send_milestone_countdown(user, milestone_type, current_value, target_value):
        """마일스톤 카운트다운 알림"""
        remaining = target_value - current_value
        percentage = (current_value / target_value) * 100
        
        if percentage >= 90:
            milestones = {
                'workouts_100': ('100회 운동', '100 Workouts', '100 Entrenamientos'),
                'calories_10000': ('10,000 칼로리 소모', '10,000 Calories Burned', '10,000 Calorías Quemadas'),
                'days_365': ('1년 운동', '1 Year of Fitness', '1 Año de Fitness'),
            }
            
            milestone_ko, milestone_en, milestone_es = milestones.get(
                milestone_type,
                ('마일스톤', 'Milestone', 'Hito')
            )
            
            NotificationService.create_notification(
                user=user,
                notification_type='motivation',
                title_ko='곧 달성해요!',
                title_en='Almost There!',
                title_es='¡Casi lo Logras!',
                message_ko=f'{milestone_ko}까지 {remaining}만 남았어요! 마지막 스퍼트! 🏃‍♂️',
                message_en=f'Only {remaining} to go for {milestone_en}! Final sprint! 🏃‍♂️',
                message_es=f'¡Solo {remaining} para {milestone_es}! ¡Sprint final! 🏃‍♂️',
                metadata={
                    'icon': 'milestone',
                    'milestone_type': milestone_type,
                    'current_value': current_value,
                    'target_value': target_value,
                    'percentage': percentage
                },
                action_url='/achievements'
            )
    
    @staticmethod
    def send_weekly_reflection(user, week_stats):
        """주간 회고 메시지"""
        workouts_completed = week_stats.get('workouts_completed', 0)
        calories_burned = week_stats.get('calories_burned', 0)
        
        NotificationService.create_notification(
            user=user,
            notification_type='motivation',
            title_ko='이번 주 운동 회고',
            title_en='Weekly Fitness Reflection',
            title_es='Reflexión Semanal de Fitness',
            message_ko=f'이번 주 {workouts_completed}회 운동으로 {calories_burned}kcal를 소모했어요! 수고하셨어요 👏',
            message_en=f'This week: {workouts_completed} workouts, {calories_burned}kcal burned! Great job 👏',
            message_es=f'Esta semana: {workouts_completed} entrenamientos, {calories_burned}kcal quemadas! ¡Buen trabajo 👏',
            metadata={
                'icon': 'reflection',
                'workouts_completed': workouts_completed,
                'calories_burned': calories_burned,
                'week_number': timezone.now().isocalendar()[1]
            },
            action_url='/reports/weekly'
        )
