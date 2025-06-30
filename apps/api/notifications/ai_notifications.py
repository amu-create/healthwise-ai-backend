from datetime import timedelta
from django.utils import timezone
from apps.api.notification_service_v2 import NotificationService
from apps.api.models import UserProfile, WorkoutRoutineLog, DailyNutrition, FoodAnalysis
import logging
import random

logger = logging.getLogger(__name__)


class AINotificationService:
    """AI 기반 맞춤 알림 서비스"""
    
    @staticmethod
    def send_ai_workout_recommendation(user, recommendation):
        """AI 운동 추천 알림"""
        workout_type = recommendation.get('workout_type', '운동')
        duration = recommendation.get('duration', 30)
        intensity = recommendation.get('intensity', 'moderate')
        
        intensity_text = {
            'low': ('저강도', 'Low Intensity', 'Baja Intensidad'),
            'moderate': ('중강도', 'Moderate Intensity', 'Intensidad Moderada'),
            'high': ('고강도', 'High Intensity', 'Alta Intensidad'),
        }
        
        intensity_ko, intensity_en, intensity_es = intensity_text.get(
            intensity,
            ('중강도', 'Moderate Intensity', 'Intensidad Moderada')
        )
        
        NotificationService.create_notification(
            user=user,
            notification_type='ai',
            title_ko='AI 맞춤 운동 추천',
            title_en='AI Workout Recommendation',
            title_es='Recomendación de Ejercicio AI',
            message_ko=f'오늘은 {intensity_ko} {workout_type} {duration}분을 추천드려요!',
            message_en=f'Today\'s recommendation: {duration} minutes of {intensity_en} {workout_type}!',
            message_es=f'Recomendación de hoy: ¡{duration} minutos de {workout_type} de {intensity_es}!',
            metadata={
                'icon': 'ai_recommendation',
                'workout_type': workout_type,
                'duration': duration,
                'intensity': intensity,
                'recommendation_id': recommendation.get('id'),
                'reasoning': recommendation.get('reasoning')
            },
            action_url='/ai/workout-recommendations'
        )
        
        # 실시간 알림
        NotificationService.send_realtime_notification(user, {
            'type': 'ai_recommendation',
            'recommendation': recommendation,
            'category': 'workout'
        })
    
    @staticmethod
    def send_ai_meal_recommendation(user, meal_plan):
        """AI 식단 추천 알림"""
        meal_type = meal_plan.get('meal_type', 'meal')
        calories = meal_plan.get('total_calories', 0)
        main_nutrients = meal_plan.get('main_nutrients', [])
        
        meal_types = {
            'breakfast': ('아침', 'Breakfast', 'Desayuno'),
            'lunch': ('점심', 'Lunch', 'Almuerzo'),
            'dinner': ('저녁', 'Dinner', 'Cena'),
            'snack': ('간식', 'Snack', 'Merienda'),
        }
        
        meal_ko, meal_en, meal_es = meal_types.get(
            meal_type,
            ('식사', 'Meal', 'Comida')
        )
        
        NotificationService.create_notification(
            user=user,
            notification_type='ai',
            title_ko=f'AI {meal_ko} 추천',
            title_en=f'AI {meal_en} Recommendation',
            title_es=f'Recomendación AI de {meal_es}',
            message_ko=f'오늘 {meal_ko}로 {calories}kcal의 균형잡힌 식단을 추천드려요!',
            message_en=f'Today\'s {meal_en.lower()} recommendation: A balanced {calories}kcal meal!',
            message_es=f'Recomendación de {meal_es.lower()} de hoy: ¡Una comida balanceada de {calories}kcal!',
            metadata={
                'icon': 'ai_meal',
                'meal_type': meal_type,
                'total_calories': calories,
                'main_nutrients': main_nutrients,
                'meal_plan_id': meal_plan.get('id'),
                'recipes': meal_plan.get('recipes', [])
            },
            action_url='/ai/meal-recommendations'
        )
    
    @staticmethod
    def send_personalized_health_tip(user, tip_data):
        """개인화된 건강 팁 알림"""
        tip_category = tip_data.get('category', 'general')
        tip_content = tip_data.get('content', {})
        
        categories = {
            'exercise': ('운동 팁', 'Exercise Tip', 'Consejo de Ejercicio'),
            'nutrition': ('영양 팁', 'Nutrition Tip', 'Consejo Nutricional'),
            'sleep': ('수면 팁', 'Sleep Tip', 'Consejo de Sueño'),
            'stress': ('스트레스 관리', 'Stress Management', 'Manejo del Estrés'),
            'hydration': ('수분 섭취', 'Hydration', 'Hidratación'),
            'recovery': ('회복 팁', 'Recovery Tip', 'Consejo de Recuperación'),
        }
        
        category_ko, category_en, category_es = categories.get(
            tip_category,
            ('건강 팁', 'Health Tip', 'Consejo de Salud')
        )
        
        NotificationService.create_notification(
            user=user,
            notification_type='ai',
            title_ko=f'오늘의 {category_ko}',
            title_en=f'Today\'s {category_en}',
            title_es=f'{category_es} de Hoy',
            message_ko=tip_content.get('ko', '건강한 하루 보내세요!'),
            message_en=tip_content.get('en', 'Have a healthy day!'),
            message_es=tip_content.get('es', '¡Ten un día saludable!'),
            metadata={
                'icon': 'tips',
                'category': tip_category,
                'tip_id': tip_data.get('id'),
                'personalization_factors': tip_data.get('personalization_factors', [])
            },
            action_url='/health/tips'
        )
    
    @staticmethod
    def send_exercise_form_improvement(user, exercise_analysis):
        """운동 폼 개선 제안 알림"""
        exercise_name = exercise_analysis.get('exercise_name', '운동')
        issues = exercise_analysis.get('form_issues', [])
        improvement_score = exercise_analysis.get('improvement_potential', 0)
        
        if issues:
            main_issue = issues[0]
            
            NotificationService.create_notification(
                user=user,
                notification_type='ai',
                title_ko='운동 폼 개선 제안',
                title_en='Exercise Form Improvement',
                title_es='Mejora de Forma de Ejercicio',
                message_ko=f'{exercise_name} 폼을 개선하면 {improvement_score}% 더 효과적일 수 있어요!',
                message_en=f'Improving your {exercise_name} form could be {improvement_score}% more effective!',
                message_es=f'¡Mejorar tu forma de {exercise_name} podría ser {improvement_score}% más efectivo!',
                metadata={
                    'icon': 'form_improvement',
                    'exercise_name': exercise_name,
                    'main_issue': main_issue,
                    'all_issues': issues,
                    'improvement_score': improvement_score,
                    'analysis_id': exercise_analysis.get('id')
                },
                action_url=f'/exercises/form-guide/{exercise_name}'
            )
    
    @staticmethod
    def send_ai_progress_analysis(user, analysis_data):
        """AI 진행 상황 분석 알림"""
        period = analysis_data.get('period', '주간')
        overall_score = analysis_data.get('overall_score', 0)
        key_achievements = analysis_data.get('key_achievements', [])
        recommendations = analysis_data.get('recommendations', [])
        
        NotificationService.create_notification(
            user=user,
            notification_type='ai',
            title_ko=f'{period} AI 분석 완료',
            title_en=f'{period} AI Analysis Complete',
            title_es=f'Análisis AI {period} Completo',
            message_ko=f'당신의 {period} 운동 성과는 {overall_score}점입니다! 상세 분석을 확인하세요.',
            message_en=f'Your {period} fitness score is {overall_score}! Check your detailed analysis.',
            message_es=f'¡Tu puntuación de fitness {period} es {overall_score}! Revisa tu análisis detallado.',
            metadata={
                'icon': 'analytics',
                'period': period,
                'overall_score': overall_score,
                'key_achievements': key_achievements[:3],  # Top 3
                'top_recommendation': recommendations[0] if recommendations else None,
                'analysis_id': analysis_data.get('id')
            },
            action_url='/ai/progress-analysis'
        )
    
    @staticmethod
    def send_ai_injury_prevention_alert(user, risk_analysis):
        """AI 부상 예방 알림"""
        risk_level = risk_analysis.get('risk_level', 'low')
        risk_factors = risk_analysis.get('risk_factors', [])
        prevention_tips = risk_analysis.get('prevention_tips', [])
        
        risk_levels = {
            'low': ('낮음', 'Low', 'Bajo'),
            'medium': ('보통', 'Medium', 'Medio'),
            'high': ('높음', 'High', 'Alto'),
        }
        
        risk_ko, risk_en, risk_es = risk_levels.get(
            risk_level,
            ('보통', 'Medium', 'Medio')
        )
        
        if risk_level in ['medium', 'high']:
            NotificationService.create_notification(
                user=user,
                notification_type='warning',
                title_ko='부상 위험 경고',
                title_en='Injury Risk Alert',
                title_es='Alerta de Riesgo de Lesión',
                message_ko=f'현재 부상 위험도: {risk_ko}. 예방 조치를 취하세요!',
                message_en=f'Current injury risk: {risk_en}. Take preventive measures!',
                message_es=f'Riesgo actual de lesión: {risk_es}. ¡Toma medidas preventivas!',
                metadata={
                    'icon': 'warning',
                    'risk_level': risk_level,
                    'main_risk_factor': risk_factors[0] if risk_factors else None,
                    'top_prevention_tip': prevention_tips[0] if prevention_tips else None,
                    'analysis_id': risk_analysis.get('id')
                },
                action_url='/health/injury-prevention'
            )
    
    @staticmethod
    def send_ai_recovery_recommendation(user, recovery_data):
        """AI 회복 추천 알림"""
        recovery_needed = recovery_data.get('recovery_score', 0) < 70
        suggested_activities = recovery_data.get('suggested_activities', [])
        
        if recovery_needed:
            NotificationService.create_notification(
                user=user,
                notification_type='ai',
                title_ko='회복이 필요해요',
                title_en='Recovery Needed',
                title_es='Recuperación Necesaria',
                message_ko='AI 분석 결과 충분한 회복이 필요합니다. 추천 활동을 확인하세요.',
                message_en='AI analysis suggests you need more recovery. Check recommended activities.',
                message_es='El análisis AI sugiere que necesitas más recuperación. Revisa las actividades recomendadas.',
                metadata={
                    'icon': 'recovery',
                    'recovery_score': recovery_data.get('recovery_score'),
                    'suggested_activities': suggested_activities[:3],
                    'estimated_recovery_time': recovery_data.get('estimated_recovery_time')
                },
                action_url='/recovery/recommendations'
            )
