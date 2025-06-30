from datetime import timedelta
from django.utils import timezone
from apps.api.notification_service_v2 import NotificationService
from apps.api.models import UserProfile
import logging

logger = logging.getLogger(__name__)


class HealthNotificationService:
    """건강 추적 관련 알림 서비스"""
    
    @staticmethod
    def send_weight_goal_achievement(user, current_weight, target_weight, previous_weight):
        """체중 목표 달성 알림"""
        weight_change = previous_weight - current_weight
        
        if abs(current_weight - target_weight) < 0.5:  # 목표 체중 도달 (오차 0.5kg)
            NotificationService.create_notification(
                user=user,
                notification_type='achievement',
                title_ko='목표 체중 달성! 🎉',
                title_en='Weight Goal Achieved! 🎉',
                title_es='¡Meta de Peso Lograda! 🎉',
                message_ko=f'축하합니다! 목표 체중 {target_weight}kg에 도달했습니다!',
                message_en=f'Congratulations! You\'ve reached your target weight of {target_weight}kg!',
                message_es=f'¡Felicidades! ¡Has alcanzado tu peso objetivo de {target_weight}kg!',
                metadata={
                    'icon': 'achievement',
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'weight_change': weight_change
                },
                action_url='/health/progress'
            )
    
    @staticmethod
    def send_weight_change_notification(user, current_weight, previous_weight, days_period=7):
        """체중 변화 알림"""
        weight_change = previous_weight - current_weight
        
        if abs(weight_change) >= 1.0:  # 1kg 이상 변화
            if weight_change > 0:
                # 체중 감소
                NotificationService.create_notification(
                    user=user,
                    notification_type='progress',
                    title_ko='체중 감소 성과',
                    title_en='Weight Loss Progress',
                    title_es='Progreso de Pérdida de Peso',
                    message_ko=f'지난 {days_period}일 동안 {weight_change:.1f}kg 감량했습니다! 대단해요!',
                    message_en=f'You\'ve lost {weight_change:.1f}kg in the last {days_period} days! Great job!',
                    message_es=f'¡Has perdido {weight_change:.1f}kg en los últimos {days_period} días! ¡Excelente!',
                    metadata={
                        'icon': 'trending_down',
                        'current_weight': current_weight,
                        'previous_weight': previous_weight,
                        'weight_change': weight_change,
                        'days_period': days_period
                    },
                    action_url='/health/weight'
                )
            else:
                # 체중 증가
                NotificationService.create_notification(
                    user=user,
                    notification_type='info',
                    title_ko='체중 변화 알림',
                    title_en='Weight Change Alert',
                    title_es='Alerta de Cambio de Peso',
                    message_ko=f'지난 {days_period}일 동안 {abs(weight_change):.1f}kg 증가했습니다.',
                    message_en=f'You\'ve gained {abs(weight_change):.1f}kg in the last {days_period} days.',
                    message_es=f'Has ganado {abs(weight_change):.1f}kg en los últimos {days_period} días.',
                    metadata={
                        'icon': 'trending_up',
                        'current_weight': current_weight,
                        'previous_weight': previous_weight,
                        'weight_change': weight_change,
                        'days_period': days_period
                    },
                    action_url='/health/weight'
                )
    
    @staticmethod
    def send_bmi_improvement_notification(user, current_bmi, previous_bmi):
        """BMI 개선 알림"""
        bmi_categories = {
            'underweight': ('저체중', 'Underweight', 'Bajo Peso'),
            'normal': ('정상', 'Normal', 'Normal'),
            'overweight': ('과체중', 'Overweight', 'Sobrepeso'),
            'obese': ('비만', 'Obese', 'Obeso'),
        }
        
        def get_bmi_category(bmi):
            if bmi < 18.5:
                return 'underweight'
            elif bmi < 25:
                return 'normal'
            elif bmi < 30:
                return 'overweight'
            else:
                return 'obese'
        
        current_category = get_bmi_category(current_bmi)
        previous_category = get_bmi_category(previous_bmi)
        
        if current_category != previous_category:
            current_ko, current_en, current_es = bmi_categories[current_category]
            
            NotificationService.create_notification(
                user=user,
                notification_type='health',
                title_ko='BMI 개선!',
                title_en='BMI Improved!',
                title_es='¡BMI Mejorado!',
                message_ko=f'BMI가 {previous_bmi:.1f}에서 {current_bmi:.1f}로 변화하여 {current_ko} 범위에 들어왔습니다!',
                message_en=f'Your BMI changed from {previous_bmi:.1f} to {current_bmi:.1f}, now in the {current_en} range!',
                message_es=f'Tu BMI cambió de {previous_bmi:.1f} a {current_bmi:.1f}, ¡ahora en el rango {current_es}!',
                metadata={
                    'icon': 'health',
                    'current_bmi': current_bmi,
                    'previous_bmi': previous_bmi,
                    'current_category': current_category,
                    'previous_category': previous_category
                },
                action_url='/health/bmi'
            )
    
    @staticmethod
    def send_health_metric_warning(user, metric_type, value, threshold):
        """건강 지표 이상 경고"""
        metric_warnings = {
            'blood_pressure_high': {
                'title': ('고혈압 주의', 'High Blood Pressure Alert', 'Alerta de Presión Alta'),
                'message': ('혈압이 높게 측정되었습니다. 의료진 상담을 권장합니다.',
                           'Your blood pressure is high. Consider consulting a healthcare provider.',
                           'Tu presión arterial está alta. Considera consultar a un médico.')
            },
            'heart_rate_high': {
                'title': ('심박수 이상', 'Abnormal Heart Rate', 'Frecuencia Cardíaca Anormal'),
                'message': ('안정시 심박수가 높습니다. 충분한 휴식을 취하세요.',
                           'Your resting heart rate is high. Make sure to get adequate rest.',
                           'Tu frecuencia cardíaca en reposo es alta. Asegúrate de descansar adecuadamente.')
            },
            'blood_sugar_high': {
                'title': ('혈당 주의', 'Blood Sugar Alert', 'Alerta de Azúcar en Sangre'),
                'message': ('혈당 수치가 높습니다. 식단 관리에 주의하세요.',
                           'Your blood sugar is high. Pay attention to your diet.',
                           'Tu azúcar en sangre está alta. Presta atención a tu dieta.')
            },
        }
        
        if metric_type in metric_warnings:
            warning_data = metric_warnings[metric_type]
            title_ko, title_en, title_es = warning_data['title']
            message_ko, message_en, message_es = warning_data['message']
            
            NotificationService.create_notification(
                user=user,
                notification_type='warning',
                title_ko=title_ko,
                title_en=title_en,
                title_es=title_es,
                message_ko=f'{message_ko} (측정값: {value})',
                message_en=f'{message_en} (Reading: {value})',
                message_es=f'{message_es} (Lectura: {value})',
                metadata={
                    'icon': 'warning',
                    'metric_type': metric_type,
                    'value': value,
                    'threshold': threshold,
                    'severity': 'high'
                },
                action_url='/health/metrics'
            )
    
    @staticmethod
    def send_health_report_ready(user, report_type, report_period):
        """건강 리포트 생성 알림"""
        report_types = {
            'weekly': ('주간 건강 리포트', 'Weekly Health Report', 'Informe de Salud Semanal'),
            'monthly': ('월간 건강 리포트', 'Monthly Health Report', 'Informe de Salud Mensual'),
            'quarterly': ('분기별 건강 리포트', 'Quarterly Health Report', 'Informe de Salud Trimestral'),
        }
        
        title_ko, title_en, title_es = report_types.get(
            report_type,
            ('건강 리포트', 'Health Report', 'Informe de Salud')
        )
        
        NotificationService.create_notification(
            user=user,
            notification_type='report',
            title_ko=f'{title_ko} 준비 완료',
            title_en=f'{title_en} Ready',
            title_es=f'{title_es} Listo',
            message_ko=f'{report_period} 동안의 건강 데이터 분석이 완료되었습니다.',
            message_en=f'Your health data analysis for {report_period} is complete.',
            message_es=f'Tu análisis de datos de salud para {report_period} está completo.',
            metadata={
                'icon': 'report',
                'report_type': report_type,
                'report_period': report_period,
                'generated_at': timezone.now().isoformat()
            },
            action_url=f'/health/reports/{report_type}'
        )
    
    @staticmethod
    def send_health_checkup_reminder(user, last_checkup_date, recommended_interval_days=180):
        """건강 검진 리마인더"""
        days_since_checkup = (timezone.now().date() - last_checkup_date).days
        
        if days_since_checkup >= recommended_interval_days:
            NotificationService.create_notification(
                user=user,
                notification_type='reminder',
                title_ko='건강 검진 시기입니다',
                title_en='Time for Health Checkup',
                title_es='Hora del Chequeo Médico',
                message_ko=f'마지막 검진으로부터 {days_since_checkup}일이 지났습니다. 정기 검진을 예약하세요.',
                message_en=f'It\'s been {days_since_checkup} days since your last checkup. Schedule your regular checkup.',
                message_es=f'Han pasado {days_since_checkup} días desde tu último chequeo. Programa tu chequeo regular.',
                metadata={
                    'icon': 'medical',
                    'last_checkup_date': last_checkup_date.isoformat(),
                    'days_since_checkup': days_since_checkup,
                    'recommended_interval': recommended_interval_days
                },
                action_url='/health/checkup'
            )
    
    @staticmethod
    def send_sleep_quality_alert(user, avg_sleep_hours, sleep_quality_score):
        """수면 품질 알림"""
        if avg_sleep_hours < 6:
            NotificationService.create_notification(
                user=user,
                notification_type='health',
                title_ko='수면 부족 주의',
                title_en='Sleep Deprivation Alert',
                title_es='Alerta de Falta de Sueño',
                message_ko=f'평균 수면 시간이 {avg_sleep_hours:.1f}시간입니다. 충분한 수면이 필요해요.',
                message_en=f'Your average sleep is {avg_sleep_hours:.1f} hours. You need more rest.',
                message_es=f'Tu sueño promedio es de {avg_sleep_hours:.1f} horas. Necesitas más descanso.',
                metadata={
                    'icon': 'sleep',
                    'avg_sleep_hours': avg_sleep_hours,
                    'sleep_quality_score': sleep_quality_score,
                    'recommendation': 'increase_sleep'
                },
                action_url='/health/sleep'
            )
        elif sleep_quality_score < 60:
            NotificationService.create_notification(
                user=user,
                notification_type='health',
                title_ko='수면 품질 개선 필요',
                title_en='Sleep Quality Needs Improvement',
                title_es='La Calidad del Sueño Necesita Mejorar',
                message_ko='수면 품질이 낮습니다. 수면 환경을 점검해보세요.',
                message_en='Your sleep quality is low. Check your sleep environment.',
                message_es='Tu calidad de sueño es baja. Revisa tu entorno de sueño.',
                metadata={
                    'icon': 'sleep',
                    'avg_sleep_hours': avg_sleep_hours,
                    'sleep_quality_score': sleep_quality_score,
                    'recommendation': 'improve_quality'
                },
                action_url='/health/sleep-tips'
            )
