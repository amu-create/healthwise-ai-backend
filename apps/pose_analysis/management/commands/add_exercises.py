from django.core.management.base import BaseCommand
from apps.pose_analysis.models import Exercise

class Command(BaseCommand):
    help = '기본 운동 데이터 추가'

    def handle(self, *args, **options):
        exercises = [
            {
                'name': '스쿼트',
                'name_en': 'Squat',
                'category': 'lower',
                'difficulty': 'beginner',
                'description': '하체 근력 강화를 위한 기본 운동',
                'target_muscles': ['대퇴사두근', '대둔근', '햄스트링'],
                'angle_calculations': {
                    'knee': {
                        'points': [23, 25, 27],  # 엉덩이, 무릎, 발목
                        'minAngle': 70,
                        'maxAngle': 100,
                        'feedback': '무릎 각도를 90도로 유지하세요'
                    },
                    'hip': {
                        'points': [11, 23, 25],  # 어깨, 엉덩이, 무릎
                        'minAngle': 80,
                        'maxAngle': 120,
                        'feedback': '상체를 곧게 세우세요'
                    }
                },
                'key_points': ['무릎이 발끝을 넘지 않도록', '허리를 곧게 유지', '천천히 내려가고 올라오기'],
                'icon': '🏋️'
            },
            {
                'name': '푸시업',
                'name_en': 'Push-up',
                'category': 'upper',
                'difficulty': 'beginner',
                'description': '상체 근력 강화를 위한 기본 운동',
                'target_muscles': ['가슴', '삼두근', '전면 삼각근'],
                'angle_calculations': {
                    'elbow': {
                        'points': [11, 13, 15],  # 어깨, 팔꿈치, 손목
                        'minAngle': 60,
                        'maxAngle': 90,
                        'feedback': '팔꿈치를 90도까지 굽히세요'
                    }
                },
                'key_points': ['몸을 일직선으로 유지', '가슴이 바닥에 거의 닿을 때까지', '팔꿈치는 몸통에서 45도'],
                'icon': '💪'
            },
            {
                'name': '런지',
                'name_en': 'Lunge',
                'category': 'lower',
                'difficulty': 'intermediate',
                'description': '하체 균형과 근력 강화 운동',
                'target_muscles': ['대퇴사두근', '대둔근', '종아리'],
                'angle_calculations': {
                    'frontKnee': {
                        'points': [23, 25, 27],  # 앞쪽 다리
                        'minAngle': 80,
                        'maxAngle': 100,
                        'feedback': '앞 무릎을 90도로 유지하세요'
                    }
                },
                'key_points': ['앞 무릎이 발끝을 넘지 않도록', '상체를 곧게 유지', '균형 잡기'],
                'icon': '🦵'
            }
        ]

        for exercise_data in exercises:
            exercise, created = Exercise.objects.get_or_create(
                name=exercise_data['name'],
                defaults=exercise_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'운동 추가됨: {exercise.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'이미 존재: {exercise.name}'))
