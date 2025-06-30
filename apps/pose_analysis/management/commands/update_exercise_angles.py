from django.core.management.base import BaseCommand
from apps.pose_analysis.models import Exercise
import json

class Command(BaseCommand):
    help = '운동 데이터에 angleCalculations 추가'

    def handle(self, *args, **options):
        # 스쿼트 업데이트
        try:
            squat = Exercise.objects.get(name='스쿼트')
            squat.angle_calculations = {
                "knee": {
                    "points": [23, 25, 27],  # 엉덩이-무릎-발목
                    "minAngle": 70,
                    "maxAngle": 110,
                    "feedback": "무릎 각도를 90도로 유지하세요"
                },
                "hip": {
                    "points": [11, 23, 25],  # 어깨-엉덩이-무릎
                    "minAngle": 80,
                    "maxAngle": 120,
                    "feedback": "엉덩이를 더 뒤로 빼세요"
                }
            }
            squat.save()
            self.stdout.write(self.style.SUCCESS('스쿼트 업데이트 완료'))
        except Exercise.DoesNotExist:
            self.stdout.write(self.style.ERROR('스쿼트를 찾을 수 없습니다'))

        # 푸시업 업데이트
        try:
            pushup = Exercise.objects.get(name='푸시업')
            pushup.angle_calculations = {
                "elbow": {
                    "points": [11, 13, 15],  # 어깨-팔꿈치-손목
                    "minAngle": 60,
                    "maxAngle": 100,
                    "feedback": "팔꿈치를 90도로 굽히세요"
                },
                "body": {
                    "points": [11, 23, 25],  # 어깨-엉덩이-무릎
                    "minAngle": 160,
                    "maxAngle": 180,
                    "feedback": "몸을 일직선으로 유지하세요"
                }
            }
            pushup.save()
            self.stdout.write(self.style.SUCCESS('푸시업 업데이트 완료'))
        except Exercise.DoesNotExist:
            self.stdout.write(self.style.ERROR('푸시업을 찾을 수 없습니다'))

        # 플랭크 업데이트
        try:
            plank = Exercise.objects.get(name='플랭크')
            plank.angle_calculations = {
                "body": {
                    "points": [11, 23, 25],  # 어깨-엉덩이-무릎
                    "minAngle": 160,
                    "maxAngle": 180,
                    "feedback": "몸을 일직선으로 유지하세요"
                },
                "shoulder": {
                    "points": [13, 11, 23],  # 팔꿈치-어깨-엉덩이
                    "minAngle": 80,
                    "maxAngle": 100,
                    "feedback": "팔꿈치를 어깨 아래에 위치시키세요"
                }
            }
            plank.save()
            self.stdout.write(self.style.SUCCESS('플랭크 업데이트 완료'))
        except Exercise.DoesNotExist:
            self.stdout.write(self.style.ERROR('플랭크를 찾을 수 없습니다'))

        # 런지 업데이트
        try:
            lunge = Exercise.objects.get(name='런지')
            lunge.angle_calculations = {
                "frontKnee": {
                    "points": [23, 25, 27],  # 앞쪽 엉덩이-무릎-발목
                    "minAngle": 80,
                    "maxAngle": 100,
                    "feedback": "앞 무릎을 90도로 유지하세요"
                },
                "backKnee": {
                    "points": [24, 26, 28],  # 뒤쪽 엉덩이-무릎-발목
                    "minAngle": 80,
                    "maxAngle": 100,
                    "feedback": "뒤 무릎도 90도로 유지하세요"
                }
            }
            lunge.save()
            self.stdout.write(self.style.SUCCESS('런지 업데이트 완료'))
        except Exercise.DoesNotExist:
            self.stdout.write(self.style.ERROR('런지를 찾을 수 없습니다'))

        # 버피 업데이트
        try:
            burpee = Exercise.objects.get(name='버피')
            burpee.angle_calculations = {
                "standing": {
                    "points": [11, 23, 25],
                    "minAngle": 170,
                    "maxAngle": 180,
                    "feedback": "서있는 자세에서 시작하세요"
                }
            }
            burpee.save()
            self.stdout.write(self.style.SUCCESS('버피 업데이트 완료'))
        except Exercise.DoesNotExist:
            self.stdout.write(self.style.ERROR('버피를 찾을 수 없습니다'))

        self.stdout.write(self.style.SUCCESS('모든 운동 업데이트 완료!'))
