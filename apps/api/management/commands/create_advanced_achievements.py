from django.core.management.base import BaseCommand
from apps.api.models import Achievement

class Command(BaseCommand):
    help = '고급 업적 시스템 생성'

    def handle(self, *args, **options):
        # 기존 업적 삭제
        Achievement.objects.all().delete()
        
        achievements = [
            # 운동 업적 - 초급
            {
                'name': '첫 걸음',
                'name_en': 'First Step',
                'name_es': 'Primer Paso',
                'description': '첫 운동 기록을 완료하세요',
                'description_en': 'Complete your first workout log',
                'description_es': 'Completa tu primer registro de ejercicio',
                'category': 'workout',
                'badge_level': 'bronze',
                'target_value': 1,
                'points': 10,
                'icon_name': 'footsteps'
            },
            {
                'name': '운동 초보자',
                'name_en': 'Exercise Beginner',
                'name_es': 'Principiante de Ejercicio',
                'description': '총 10회 운동을 완료하세요',
                'description_en': 'Complete 10 workouts in total',
                'description_es': 'Completa 10 ejercicios en total',
                'category': 'workout',
                'badge_level': 'bronze',
                'target_value': 10,
                'points': 50,
                'icon_name': 'fitness_center'
            },
            {
                'name': '주간 전사',
                'name_en': 'Weekly Warrior',
                'name_es': 'Guerrero Semanal',
                'description': '일주일 동안 매일 운동하세요',
                'description_en': 'Exercise every day for a week',
                'description_es': 'Ejercita todos los días durante una semana',
                'category': 'workout',
                'badge_level': 'silver',
                'target_value': 7,
                'points': 100,
                'icon_name': 'calendar_today'
            },
            {
                'name': '운동 중독자',
                'name_en': 'Workout Addict',
                'name_es': 'Adicto al Ejercicio',
                'description': '총 50회 운동을 완료하세요',
                'description_en': 'Complete 50 workouts in total',
                'description_es': 'Completa 50 ejercicios en total',
                'category': 'workout',
                'badge_level': 'silver',
                'target_value': 50,
                'points': 200,
                'icon_name': 'sports_gymnastics'
            },
            {
                'name': '월간 챔피언',
                'name_en': 'Monthly Champion',
                'name_es': 'Campeón Mensual',
                'description': '한 달 동안 25일 이상 운동하세요',
                'description_en': 'Exercise for 25+ days in a month',
                'description_es': 'Ejercita más de 25 días en un mes',
                'category': 'workout',
                'badge_level': 'gold',
                'target_value': 25,
                'points': 500,
                'icon_name': 'emoji_events'
            },
            {
                'name': '100일 마스터',
                'name_en': '100 Days Master',
                'name_es': 'Maestro de 100 Días',
                'description': '총 100회 운동을 완료하세요',
                'description_en': 'Complete 100 workouts in total',
                'description_es': 'Completa 100 ejercicios en total',
                'category': 'workout',
                'badge_level': 'gold',
                'target_value': 100,
                'points': 1000,
                'icon_name': 'military_tech'
            },
            {
                'name': '피트니스 레전드',
                'name_en': 'Fitness Legend',
                'name_es': 'Leyenda del Fitness',
                'description': '총 365회 운동을 완료하세요',
                'description_en': 'Complete 365 workouts in total',
                'description_es': 'Completa 365 ejercicios en total',
                'category': 'workout',
                'badge_level': 'platinum',
                'target_value': 365,
                'points': 5000,
                'icon_name': 'workspace_premium'
            },
            {
                'name': '운동의 신',
                'name_en': 'God of Exercise',
                'name_es': 'Dios del Ejercicio',
                'description': '총 1000회 운동을 완료하세요',
                'description_en': 'Complete 1000 workouts in total',
                'description_es': 'Completa 1000 ejercicios en total',
                'category': 'workout',
                'badge_level': 'diamond',
                'target_value': 1000,
                'points': 10000,
                'icon_name': 'auto_awesome'
            },
            
            # 영양 업적
            {
                'name': '영양 기록자',
                'name_en': 'Nutrition Logger',
                'name_es': 'Registrador de Nutrición',
                'description': '첫 식단을 기록하세요',
                'description_en': 'Log your first meal',
                'description_es': 'Registra tu primera comida',
                'category': 'nutrition',
                'badge_level': 'bronze',
                'target_value': 1,
                'points': 10,
                'icon_name': 'restaurant_menu'
            },
            {
                'name': '칼로리 관리자',
                'name_en': 'Calorie Manager',
                'name_es': 'Gestor de Calorías',
                'description': '7일 연속 칼로리 목표를 달성하세요',
                'description_en': 'Achieve calorie goal for 7 consecutive days',
                'description_es': 'Alcanza tu objetivo de calorías durante 7 días consecutivos',
                'category': 'nutrition',
                'badge_level': 'silver',
                'target_value': 7,
                'points': 100,
                'icon_name': 'local_fire_department'
            },
            {
                'name': '균형잡힌 식단',
                'name_en': 'Balanced Diet',
                'name_es': 'Dieta Equilibrada',
                'description': '30일 동안 영양 목표를 달성하세요',
                'description_en': 'Achieve nutrition goals for 30 days',
                'description_es': 'Alcanza tus objetivos nutricionales durante 30 días',
                'category': 'nutrition',
                'badge_level': 'gold',
                'target_value': 30,
                'points': 500,
                'icon_name': 'pie_chart'
            },
            {
                'name': '영양 전문가',
                'name_en': 'Nutrition Expert',
                'name_es': 'Experto en Nutrición',
                'description': '100일 동안 식단을 기록하세요',
                'description_en': 'Log meals for 100 days',
                'description_es': 'Registra comidas durante 100 días',
                'category': 'nutrition',
                'badge_level': 'platinum',
                'target_value': 100,
                'points': 2000,
                'icon_name': 'insights'
            },
            
            # 연속 기록 업적
            {
                'name': '3일 연속',
                'name_en': '3 Day Streak',
                'name_es': 'Racha de 3 Días',
                'description': '3일 연속으로 운동하세요',
                'description_en': 'Exercise for 3 consecutive days',
                'description_es': 'Ejercita durante 3 días consecutivos',
                'category': 'streak',
                'badge_level': 'bronze',
                'target_value': 3,
                'points': 30,
                'icon_name': 'trending_up'
            },
            {
                'name': '주간 스트릭',
                'name_en': 'Weekly Streak',
                'name_es': 'Racha Semanal',
                'description': '7일 연속으로 운동하세요',
                'description_en': 'Exercise for 7 consecutive days',
                'description_es': 'Ejercita durante 7 días consecutivos',
                'category': 'streak',
                'badge_level': 'silver',
                'target_value': 7,
                'points': 100,
                'icon_name': 'whatshot'
            },
            {
                'name': '월간 스트릭',
                'name_en': 'Monthly Streak',
                'name_es': 'Racha Mensual',
                'description': '30일 연속으로 운동하세요',
                'description_en': 'Exercise for 30 consecutive days',
                'description_es': 'Ejercita durante 30 días consecutivos',
                'category': 'streak',
                'badge_level': 'gold',
                'target_value': 30,
                'points': 1000,
                'icon_name': 'local_fire_department'
            },
            {
                'name': '100일 스트릭',
                'name_en': '100 Day Streak',
                'name_es': 'Racha de 100 Días',
                'description': '100일 연속으로 운동하세요',
                'description_en': 'Exercise for 100 consecutive days',
                'description_es': 'Ejercita durante 100 días consecutivos',
                'category': 'streak',
                'badge_level': 'platinum',
                'target_value': 100,
                'points': 5000,
                'icon_name': 'whatshot'
            },
            {
                'name': '1년 스트릭',
                'name_en': 'Year Streak',
                'name_es': 'Racha Anual',
                'description': '365일 연속으로 운동하세요',
                'description_en': 'Exercise for 365 consecutive days',
                'description_es': 'Ejercita durante 365 días consecutivos',
                'category': 'streak',
                'badge_level': 'diamond',
                'target_value': 365,
                'points': 20000,
                'icon_name': 'stars'
            },
            
            # 마일스톤 업적
            {
                'name': '체중 감량 5kg',
                'name_en': 'Lost 5kg',
                'name_es': 'Perdió 5kg',
                'description': '목표 체중에서 5kg을 감량하세요',
                'description_en': 'Lose 5kg from your target weight',
                'description_es': 'Pierde 5kg de tu peso objetivo',
                'category': 'milestone',
                'badge_level': 'silver',
                'target_value': 5,
                'points': 300,
                'icon_name': 'trending_down'
            },
            {
                'name': '근육량 증가',
                'name_en': 'Muscle Gain',
                'name_es': 'Ganancia Muscular',
                'description': '근육량을 2kg 증가시키세요',
                'description_en': 'Gain 2kg of muscle mass',
                'description_es': 'Gana 2kg de masa muscular',
                'category': 'milestone',
                'badge_level': 'gold',
                'target_value': 2,
                'points': 500,
                'icon_name': 'fitness_center'
            },
            {
                'name': '마라톤 완주',
                'name_en': 'Marathon Finisher',
                'name_es': 'Finalista de Maratón',
                'description': '총 42.195km를 달리세요',
                'description_en': 'Run a total of 42.195km',
                'description_es': 'Corre un total de 42.195km',
                'category': 'milestone',
                'badge_level': 'platinum',
                'target_value': 42195,
                'points': 2000,
                'icon_name': 'directions_run'
            },
            
            # 챌린지 업적
            {
                'name': '새벽 운동가',
                'name_en': 'Early Bird',
                'name_es': 'Madrugador',
                'description': '오전 6시 이전에 10회 운동하세요',
                'description_en': 'Exercise 10 times before 6 AM',
                'description_es': 'Ejercita 10 veces antes de las 6 AM',
                'category': 'challenge',
                'badge_level': 'silver',
                'target_value': 10,
                'points': 200,
                'icon_name': 'wb_sunny'
            },
            {
                'name': '야간 운동가',
                'name_en': 'Night Owl',
                'name_es': 'Búho Nocturno',
                'description': '오후 9시 이후에 10회 운동하세요',
                'description_en': 'Exercise 10 times after 9 PM',
                'description_es': 'Ejercita 10 veces después de las 9 PM',
                'category': 'challenge',
                'badge_level': 'silver',
                'target_value': 10,
                'points': 200,
                'icon_name': 'nights_stay'
            },
            {
                'name': '주말 전사',
                'name_en': 'Weekend Warrior',
                'name_es': 'Guerrero de Fin de Semana',
                'description': '주말에만 20회 운동하세요',
                'description_en': 'Exercise 20 times only on weekends',
                'description_es': 'Ejercita 20 veces solo los fines de semana',
                'category': 'challenge',
                'badge_level': 'gold',
                'target_value': 20,
                'points': 500,
                'icon_name': 'weekend'
            },
            {
                'name': '다양성 추구자',
                'name_en': 'Variety Seeker',
                'name_es': 'Buscador de Variedad',
                'description': '10가지 다른 운동을 시도하세요',
                'description_en': 'Try 10 different exercises',
                'description_es': 'Prueba 10 ejercicios diferentes',
                'category': 'challenge',
                'badge_level': 'gold',
                'target_value': 10,
                'points': 400,
                'icon_name': 'shuffle'
            },
            {
                'name': '소셜 피트니스',
                'name_en': 'Social Fitness',
                'name_es': 'Fitness Social',
                'description': '운동 기록을 50회 공유하세요',
                'description_en': 'Share 50 workout logs',
                'description_es': 'Comparte 50 registros de ejercicio',
                'category': 'challenge',
                'badge_level': 'platinum',
                'target_value': 50,
                'points': 1500,
                'icon_name': 'share'
            }
        ]
        
        for achievement_data in achievements:
            Achievement.objects.create(**achievement_data)
        
        self.stdout.write(
            self.style.SUCCESS(f'{len(achievements)}개의 고급 업적이 생성되었습니다.')
        )
