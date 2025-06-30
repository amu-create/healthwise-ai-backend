from django.core.management.base import BaseCommand
from apps.api.models import Exercise

class Command(BaseCommand):
    help = 'Populate exercise database with initial data'

    def handle(self, *args, **kwargs):
        exercises = [
            # 가슴 운동
            {'name': '벤치프레스', 'muscle_group': '가슴', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bench-Press.gif', 'default_sets': 4, 'default_reps': 10, 'exercise_type': 'strength'},
            {'name': '인클라인 벤치프레스', 'muscle_group': '가슴', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Incline-Barbell-Bench-Press.gif', 'default_sets': 4, 'default_reps': 10, 'exercise_type': 'strength'},
            {'name': '덤벨 플라이', 'muscle_group': '가슴', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Fly.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '체스트 프레스 머신', 'muscle_group': '가슴', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/06/Chest-Press-Machine.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '푸시업', 'muscle_group': '가슴', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Push-Up.gif', 'default_sets': 3, 'default_reps': 15, 'exercise_type': 'strength'},
            
            # 등 운동
            {'name': '풀업', 'muscle_group': '등', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Pull-up.gif', 'default_sets': 3, 'default_reps': 8, 'exercise_type': 'strength'},
            {'name': '랫풀다운', 'muscle_group': '등', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Lat-Pulldown.gif', 'default_sets': 4, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '바벨로우', 'muscle_group': '등', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Bent-Over-Row.gif', 'default_sets': 4, 'default_reps': 10, 'exercise_type': 'strength'},
            {'name': '시티드 로우', 'muscle_group': '등', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Seated-Cable-Row.gif', 'default_sets': 4, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '데드리프트', 'muscle_group': '등', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Deadlift.gif', 'default_sets': 4, 'default_reps': 8, 'exercise_type': 'strength'},
            
            # 하체 운동
            {'name': '스쿼트', 'muscle_group': '하체', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/BARBELL-SQUAT.gif', 'default_sets': 4, 'default_reps': 10, 'exercise_type': 'strength'},
            {'name': '레그프레스', 'muscle_group': '하체', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Leg-Press.gif', 'default_sets': 4, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '런지', 'muscle_group': '하체', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lunge.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '레그컬', 'muscle_group': '하체', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Leg-Curl.gif', 'default_sets': 3, 'default_reps': 15, 'exercise_type': 'strength'},
            {'name': '레그 익스텐션', 'muscle_group': '하체', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/LEG-EXTENSION.gif', 'default_sets': 3, 'default_reps': 15, 'exercise_type': 'strength'},
            
            # 어깨 운동
            {'name': '숄더프레스', 'muscle_group': '어깨', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Shoulder-Press.gif', 'default_sets': 4, 'default_reps': 10, 'exercise_type': 'strength'},
            {'name': '사이드 레터럴 레이즈', 'muscle_group': '어깨', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Lateral-Raise.gif', 'default_sets': 3, 'default_reps': 15, 'exercise_type': 'strength'},
            {'name': '프론트 레이즈', 'muscle_group': '어깨', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Front-Raise.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '업라이트 로우', 'muscle_group': '어깨', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Upright-Row.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '리어 델트 플라이', 'muscle_group': '어깨', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Rear-Lateral-Raise.gif', 'default_sets': 3, 'default_reps': 15, 'exercise_type': 'strength'},
            
            # 팔 운동
            {'name': '바벨컬', 'muscle_group': '팔', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Curl.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '해머컬', 'muscle_group': '팔', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Hammer-Curl.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '트라이셉스 익스텐션', 'muscle_group': '팔', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Dumbbell-Triceps-Extension.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            {'name': '케이블 푸시다운', 'muscle_group': '팔', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Cable-Pushdown.gif', 'default_sets': 3, 'default_reps': 15, 'exercise_type': 'strength'},
            {'name': '프리처컬', 'muscle_group': '팔', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Barbell-Preacher-Curl.gif', 'default_sets': 3, 'default_reps': 12, 'exercise_type': 'strength'},
            
            # 복근 운동
            {'name': '크런치', 'muscle_group': '복근', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Crunch.gif', 'default_sets': 3, 'default_reps': 20, 'exercise_type': 'core'},
            {'name': '플랭크', 'muscle_group': '복근', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Plank.gif', 'default_sets': 3, 'default_reps': 60, 'exercise_type': 'core'},
            {'name': '레그레이즈', 'muscle_group': '복근', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Leg-Raise.gif', 'default_sets': 3, 'default_reps': 15, 'exercise_type': 'core'},
            {'name': '러시안 트위스트', 'muscle_group': '복근', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/06/Russian-Twist.gif', 'default_sets': 3, 'default_reps': 20, 'exercise_type': 'core'},
            {'name': '바이시클 크런치', 'muscle_group': '복근', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Bicycle-Crunch.gif', 'default_sets': 3, 'default_reps': 20, 'exercise_type': 'core'},
            
            # 유산소 운동 - static images or default
            {'name': '러닝머신', 'muscle_group': '전신', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/05/Treadmill-.gif', 'default_sets': 1, 'default_reps': 30, 'exercise_type': 'cardio'},
            {'name': '사이클', 'muscle_group': '전신', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/05/Stationary-Bike.gif', 'default_sets': 1, 'default_reps': 30, 'exercise_type': 'cardio'},
            {'name': '로잉머신', 'muscle_group': '전신', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/11/Rowing-Machine.gif', 'default_sets': 1, 'default_reps': 20, 'exercise_type': 'cardio'},
            {'name': '버피', 'muscle_group': '전신', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Burpee.gif', 'default_sets': 3, 'default_reps': 10, 'exercise_type': 'cardio'},
            {'name': '점핑잭', 'muscle_group': '전신', 'gif_url': 'https://fitnessprogramer.com/wp-content/uploads/2021/02/Jumping-Jack.gif', 'default_sets': 3, 'default_reps': 30, 'exercise_type': 'cardio'},
        ]

        created_count = 0
        updated_count = 0
        for exercise_data in exercises:
            exercise, created = Exercise.objects.get_or_create(
                name=exercise_data['name'],
                defaults=exercise_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created: {exercise.name}'))
            else:
                # Update existing exercise with new GIF URL
                exercise.gif_url = exercise_data['gif_url']
                exercise.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'Updated: {exercise.name}'))

        self.stdout.write(self.style.SUCCESS(f'\nTotal exercises created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total exercises updated: {updated_count}'))
