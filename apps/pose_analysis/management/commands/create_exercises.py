# Create initial pose analysis exercises
from django.core.management.base import BaseCommand
from apps.pose_analysis.models import Exercise
import json


class Command(BaseCommand):
    help = 'Create initial pose analysis exercises'

    def handle(self, *args, **options):
        exercises = [
            {
                'name': '스쿼트',
                'category': 'lower_body',
                'difficulty': 'beginner',
                'calories_per_minute': 8.0,
                'target_muscles': ['대퇴사두근', '둔근', '햄스트링'],
                'description': '하체 근력 운동의 기본이 되는 운동입니다.',
                'instructions': [
                    '발을 어깨 너비로 벌리고 섭니다',
                    '가슴을 펴고 시선은 정면을 봅니다',
                    '엉덩이를 뒤로 빼면서 천천히 앉습니다',
                    '허벅지가 바닥과 평행할 때까지 내려갑니다',
                    '발뒤꿈치로 바닥을 밀며 일어섭니다'
                ],
                'key_points': {
                    'hip_knee_ankle': {
                        'points': ['LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE'],
                        'ideal_angle': 90,
                        'tolerance': 15,
                        'feedback': '무릎 각도를 확인하세요'
                    },
                    'knee_alignment': {
                        'points': ['LEFT_HIP', 'LEFT_KNEE', 'LEFT_FOOT_INDEX'],
                        'ideal_angle': 180,
                        'tolerance': 10,
                        'feedback': '무릎이 발끝 방향과 일치하도록 하세요'
                    }
                },
                'is_active': True
            },
            {
                'name': '푸시업',
                'category': 'upper_body',
                'difficulty': 'beginner',
                'calories_per_minute': 7.0,
                'target_muscles': ['가슴', '삼두근', '전면 삼각근'],
                'description': '상체 근력을 키우는 기본 운동입니다.',
                'instructions': [
                    '바닥에 엎드려 손을 어깨 너비보다 약간 넓게 놓습니다',
                    '발을 모으고 몸을 일직선으로 만듭니다',
                    '팔꿈치를 구부리며 가슴이 바닥에 가까워질 때까지 내려갑니다',
                    '팔을 펴며 시작 자세로 돌아옵니다'
                ],
                'key_points': {
                    'elbow_angle': {
                        'points': ['LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST'],
                        'ideal_angle': 90,
                        'tolerance': 15,
                        'feedback': '팔꿈치 각도를 90도로 유지하세요'
                    },
                    'body_alignment': {
                        'points': ['LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_ANKLE'],
                        'ideal_angle': 180,
                        'tolerance': 10,
                        'feedback': '몸을 일직선으로 유지하세요'
                    }
                },
                'is_active': True
            },
            {
                'name': '플랭크',
                'category': 'core',
                'difficulty': 'beginner',
                'calories_per_minute': 5.0,
                'target_muscles': ['복직근', '복사근', '척추기립근'],
                'description': '코어 근육을 강화하는 정적 운동입니다.',
                'instructions': [
                    '팔꿈치를 어깨 아래에 놓고 엎드립니다',
                    '발끝으로 바닥을 지지하며 몸을 들어올립니다',
                    '머리부터 발끝까지 일직선을 유지합니다',
                    '복부에 힘을 주고 자세를 유지합니다'
                ],
                'key_points': {
                    'body_alignment': {
                        'points': ['LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_ANKLE'],
                        'ideal_angle': 180,
                        'tolerance': 8,
                        'feedback': '엉덩이가 너무 높거나 낮지 않게 유지하세요'
                    },
                    'elbow_position': {
                        'points': ['LEFT_SHOULDER', 'LEFT_ELBOW', 'LEFT_WRIST'],
                        'ideal_angle': 90,
                        'tolerance': 10,
                        'feedback': '팔꿈치는 어깨 바로 아래에 위치하세요'
                    }
                },
                'is_active': True
            },
            {
                'name': '런지',
                'category': 'lower_body',
                'difficulty': 'intermediate',
                'calories_per_minute': 9.0,
                'target_muscles': ['대퇴사두근', '둔근', '햄스트링', '종아리'],
                'description': '하체와 균형 감각을 동시에 향상시키는 운동입니다.',
                'instructions': [
                    '발을 어깨 너비로 벌리고 섭니다',
                    '한 발을 크게 앞으로 내딛습니다',
                    '뒷 무릎이 바닥에 닿을 듯 내려갑니다',
                    '앞 무릎은 90도 각도를 유지합니다',
                    '앞발로 바닥을 밀며 시작 자세로 돌아옵니다'
                ],
                'key_points': {
                    'front_knee_angle': {
                        'points': ['LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE'],
                        'ideal_angle': 90,
                        'tolerance': 15,
                        'feedback': '앞 무릎을 90도로 유지하세요'
                    },
                    'back_knee_angle': {
                        'points': ['RIGHT_HIP', 'RIGHT_KNEE', 'RIGHT_ANKLE'],
                        'ideal_angle': 90,
                        'tolerance': 15,
                        'feedback': '뒷 무릎도 90도 각도를 유지하세요'
                    }
                },
                'is_active': True
            },
            {
                'name': '브릿지',
                'category': 'core',
                'difficulty': 'beginner',
                'calories_per_minute': 6.0,
                'target_muscles': ['둔근', '햄스트링', '하부 등근육'],
                'description': '둔근과 코어를 강화하는 운동입니다.',
                'instructions': [
                    '바닥에 누워 무릎을 구부립니다',
                    '발은 어깨 너비로 벌리고 바닥에 붙입니다',
                    '엉덩이를 들어올려 어깨부터 무릎까지 일직선을 만듭니다',
                    '정점에서 잠시 멈춘 후 천천히 내려옵니다'
                ],
                'key_points': {
                    'hip_alignment': {
                        'points': ['LEFT_SHOULDER', 'LEFT_HIP', 'LEFT_KNEE'],
                        'ideal_angle': 180,
                        'tolerance': 10,
                        'feedback': '엉덩이를 충분히 들어올리세요'
                    },
                    'knee_angle': {
                        'points': ['LEFT_HIP', 'LEFT_KNEE', 'LEFT_ANKLE'],
                        'ideal_angle': 90,
                        'tolerance': 15,
                        'feedback': '무릎은 90도를 유지하세요'
                    }
                },
                'is_active': True
            }
        ]

        for exercise_data in exercises:
            exercise, created = Exercise.objects.update_or_create(
                name=exercise_data['name'],
                defaults={
                    'category': exercise_data['category'],
                    'difficulty': exercise_data['difficulty'],
                    'calories_per_minute': exercise_data['calories_per_minute'],
                    'target_muscles': exercise_data['target_muscles'],
                    'description': exercise_data['description'],
                    'instructions': exercise_data['instructions'],
                    'key_points': exercise_data['key_points'],
                    'is_active': exercise_data['is_active']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created exercise: {exercise.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Updated exercise: {exercise.name}'))

        self.stdout.write(self.style.SUCCESS('Successfully created/updated all exercises'))
