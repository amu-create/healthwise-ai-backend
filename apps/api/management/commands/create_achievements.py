from django.core.management.base import BaseCommand
from django.db import transaction
from apps.api.models import Achievement


class Command(BaseCommand):
    help = '초기 업적 데이터를 생성합니다'

    def handle(self, *args, **options):
        achievements_data = [
            # 운동 업적
            {
                'name': 'workout_beginner',
                'name_en': 'Workout Beginner',
                'name_es': 'Principiante de Ejercicio',
                'description': '운동을 10회 완료했습니다',
                'description_en': 'Completed 10 workouts',
                'description_es': 'Completaste 10 entrenamientos',
                'category': 'workout',
                'badge_level': 'bronze',
                'icon_name': 'fitness_center',
                'target_value': 10,
                'points': 50
            },
            {
                'name': 'workout_intermediate',
                'name_en': 'Workout Intermediate',
                'name_es': 'Intermedio de Ejercicio',
                'description': '운동을 50회 완료했습니다',
                'description_en': 'Completed 50 workouts',
                'description_es': 'Completaste 50 entrenamientos',
                'category': 'workout',
                'badge_level': 'silver',
                'icon_name': 'fitness_center',
                'target_value': 50,
                'points': 100
            },
            {
                'name': 'workout_advanced',
                'name_en': 'Workout Advanced',
                'name_es': 'Avanzado de Ejercicio',
                'description': '운동을 100회 완료했습니다',
                'description_en': 'Completed 100 workouts',
                'description_es': 'Completaste 100 entrenamientos',
                'category': 'workout',
                'badge_level': 'gold',
                'icon_name': 'fitness_center',
                'target_value': 100,
                'points': 200
            },
            {
                'name': 'weekly_warrior',
                'name_en': 'Weekly Warrior',
                'name_es': 'Guerrero Semanal',
                'description': '한 주에 5회 이상 운동했습니다',
                'description_en': 'Worked out 5 times in a week',
                'description_es': 'Entrenaste 5 veces en una semana',
                'category': 'workout',
                'badge_level': 'silver',
                'icon_name': 'event_available',
                'target_value': 1,
                'points': 75
            },
            {
                'name': 'monthly_master',
                'name_en': 'Monthly Master',
                'name_es': 'Maestro Mensual',
                'description': '한 달에 20회 이상 운동했습니다',
                'description_en': 'Worked out 20 times in a month',
                'description_es': 'Entrenaste 20 veces en un mes',
                'category': 'workout',
                'badge_level': 'gold',
                'icon_name': 'calendar_month',
                'target_value': 1,
                'points': 150
            },
            
            # 영양 업적
            {
                'name': 'nutrition_tracker',
                'name_en': 'Nutrition Tracker',
                'name_es': 'Rastreador de Nutrición',
                'description': '7일 동안 영양 정보를 기록했습니다',
                'description_en': 'Tracked nutrition for 7 days',
                'description_es': 'Registraste nutrición durante 7 días',
                'category': 'nutrition',
                'badge_level': 'bronze',
                'icon_name': 'restaurant_menu',
                'target_value': 7,
                'points': 50
            },
            {
                'name': 'nutrition_pro',
                'name_en': 'Nutrition Pro',
                'name_es': 'Pro de Nutrición',
                'description': '30일 동안 영양 정보를 기록했습니다',
                'description_en': 'Tracked nutrition for 30 days',
                'description_es': 'Registraste nutrición durante 30 días',
                'category': 'nutrition',
                'badge_level': 'silver',
                'icon_name': 'restaurant_menu',
                'target_value': 30,
                'points': 100
            },
            {
                'name': 'nutrition_master',
                'name_en': 'Nutrition Master',
                'name_es': 'Maestro de Nutrición',
                'description': '100일 동안 영양 정보를 기록했습니다',
                'description_en': 'Tracked nutrition for 100 days',
                'description_es': 'Registraste nutrición durante 100 días',
                'category': 'nutrition',
                'badge_level': 'gold',
                'icon_name': 'restaurant_menu',
                'target_value': 100,
                'points': 200
            },
            
            # 연속 기록 업적
            {
                'name': 'streak_7days',
                'name_en': '7-Day Workout Streak',
                'name_es': 'Racha de 7 Días de Ejercicio',
                'description': '7일 연속으로 운동했습니다',
                'description_en': 'Worked out 7 days in a row',
                'description_es': 'Entrenaste 7 días seguidos',
                'category': 'streak',
                'badge_level': 'bronze',
                'icon_name': 'trending_up',
                'target_value': 1,
                'points': 75
            },
            {
                'name': 'streak_30days',
                'name_en': '30-Day Workout Streak',
                'name_es': 'Racha de 30 Días de Ejercicio',
                'description': '30일 연속으로 운동했습니다',
                'description_en': 'Worked out 30 days in a row',
                'description_es': 'Entrenaste 30 días seguidos',
                'category': 'streak',
                'badge_level': 'gold',
                'icon_name': 'trending_up',
                'target_value': 1,
                'points': 200
            },
            {
                'name': 'nutrition_streak_7days',
                'name_en': '7-Day Nutrition Streak',
                'name_es': 'Racha de 7 Días de Nutrición',
                'description': '7일 연속으로 영양 정보를 기록했습니다',
                'description_en': 'Tracked nutrition 7 days in a row',
                'description_es': 'Registraste nutrición 7 días seguidos',
                'category': 'streak',
                'badge_level': 'bronze',
                'icon_name': 'show_chart',
                'target_value': 1,
                'points': 75
            },
            {
                'name': 'nutrition_streak_30days',
                'name_en': '30-Day Nutrition Streak',
                'name_es': 'Racha de 30 Días de Nutrición',
                'description': '30일 연속으로 영양 정보를 기록했습니다',
                'description_en': 'Tracked nutrition 30 days in a row',
                'description_es': 'Registraste nutrición 30 días seguidos',
                'category': 'streak',
                'badge_level': 'gold',
                'icon_name': 'show_chart',
                'target_value': 1,
                'points': 200
            },
            
            # 마일스톤 업적
            {
                'name': '첫 목표 달성',
                'name_en': 'First Goal Achieved',
                'name_es': 'Primera Meta Lograda',
                'description': '첫 번째 개인 목표를 달성했습니다',
                'description_en': 'Achieved your first personal goal',
                'description_es': 'Lograste tu primera meta personal',
                'category': 'milestone',
                'badge_level': 'bronze',
                'icon_name': 'flag',
                'target_value': 1,
                'points': 50
            },
            {
                'name': '체중 목표 달성',
                'name_en': 'Weight Goal Achieved',
                'name_es': 'Meta de Peso Lograda',
                'description': '목표 체중에 도달했습니다',
                'description_en': 'Reached your target weight',
                'description_es': 'Alcanzaste tu peso objetivo',
                'category': 'milestone',
                'badge_level': 'gold',
                'icon_name': 'monitor_weight',
                'target_value': 1,
                'points': 150
            },
            {
                'name': '피트니스 레벨 10',
                'name_en': 'Fitness Level 10',
                'name_es': 'Nivel de Fitness 10',
                'description': '피트니스 레벨 10에 도달했습니다',
                'description_en': 'Reached fitness level 10',
                'description_es': 'Alcanzaste el nivel de fitness 10',
                'category': 'milestone',
                'badge_level': 'silver',
                'icon_name': 'military_tech',
                'target_value': 10,
                'points': 100
            },
            
            # 챌린지 업적
            {
                'name': '100칼로리 소모',
                'name_en': '100 Calories Burned',
                'name_es': '100 Calorías Quemadas',
                'description': '하루에 100칼로리를 소모했습니다',
                'description_en': 'Burned 100 calories in a day',
                'description_es': 'Quemaste 100 calorías en un día',
                'category': 'challenge',
                'badge_level': 'bronze',
                'icon_name': 'local_fire_department',
                'target_value': 100,
                'points': 30
            },
            {
                'name': '500칼로리 소모',
                'name_en': '500 Calories Burned',
                'name_es': '500 Calorías Quemadas',
                'description': '하루에 500칼로리를 소모했습니다',
                'description_en': 'Burned 500 calories in a day',
                'description_es': 'Quemaste 500 calorías en un día',
                'category': 'challenge',
                'badge_level': 'silver',
                'icon_name': 'local_fire_department',
                'target_value': 500,
                'points': 75
            },
            {
                'name': '1000칼로리 소모',
                'name_en': '1000 Calories Burned',
                'name_es': '1000 Calorías Quemadas',
                'description': '하루에 1000칼로리를 소모했습니다',
                'description_en': 'Burned 1000 calories in a day',
                'description_es': 'Quemaste 1000 calorías en un día',
                'category': 'challenge',
                'badge_level': 'gold',
                'icon_name': 'local_fire_department',
                'target_value': 1000,
                'points': 150
            },
        ]

        with transaction.atomic():
            created_count = 0
            updated_count = 0
            
            for achievement_data in achievements_data:
                achievement, created = Achievement.objects.update_or_create(
                    name=achievement_data['name'],
                    defaults=achievement_data
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'생성됨: {achievement.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'업데이트됨: {achievement.name}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n총 {created_count}개의 업적이 생성되고, '
                    f'{updated_count}개의 업적이 업데이트되었습니다.'
                )
            )
