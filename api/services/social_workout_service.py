# api/services/social_workout_service.py
from datetime import datetime
import random

class SocialWorkoutService:
    """소셜 운동 공유 서비스"""
    
    def __init__(self):
        self.mock_posts = []
        
    def create_workout_post(self, user_id, workout_log_id, content=None, visibility='public'):
        """운동 완료 후 소셜 포스트 생성"""
        
        # 운동 정보 가져오기 (실제로는 DB에서)
        workout_info = self._get_workout_info(workout_log_id)
        
        # 자동 생성 콘텐츠
        if not content:
            content = self._generate_workout_content(workout_info)
        
        post = {
            'id': random.randint(1000, 9999),
            'user_id': user_id,
            'workout_log_id': workout_log_id,
            'content': content,
            'workout_info': workout_info,
            'visibility': visibility,
            'likes': 0,
            'comments': [],
            'created_at': datetime.now().isoformat(),
            'type': 'workout_complete'
        }
        
        self.mock_posts.append(post)
        return post
    
    def _get_workout_info(self, workout_log_id):
        """운동 정보 반환 (모의 데이터)"""
        return {
            'routine_name': '상체 운동 루틴',
            'duration': 45,
            'calories_burned': 320,
            'exercises_completed': 6,
            'total_sets': 18
        }
    
    def _generate_workout_content(self, workout_info):
        """운동 완료 메시지 자동 생성"""
        messages = [
            f"오늘도 {workout_info['duration']}분간 열심히 운동했어요! 💪",
            f"{workout_info['routine_name']} 완료! {workout_info['calories_burned']}kcal 소모했습니다 🔥",
            f"운동 {workout_info['exercises_completed']}개, 총 {workout_info['total_sets']}세트 완료! 뿌듯해요 😊",
            f"오늘의 운동 미션 클리어! {workout_info['duration']}분 동안 최선을 다했습니다 🎯"
        ]
        return random.choice(messages)
    
    def share_achievement(self, user_id, achievement_type, achievement_data):
        """업적 달성 공유"""
        content = self._generate_achievement_content(achievement_type, achievement_data)
        
        post = {
            'id': random.randint(1000, 9999),
            'user_id': user_id,
            'content': content,
            'achievement': {
                'type': achievement_type,
                'data': achievement_data
            },
            'visibility': 'public',
            'likes': 0,
            'comments': [],
            'created_at': datetime.now().isoformat(),
            'type': 'achievement'
        }
        
        self.mock_posts.append(post)
        return post
    
    def _generate_achievement_content(self, achievement_type, data):
        """업적 메시지 생성"""
        if achievement_type == 'streak':
            return f"🔥 {data['days']}일 연속 운동 달성! 꾸준함이 최고의 무기입니다!"
        elif achievement_type == 'milestone':
            return f"🎉 누적 운동 {data['total_workouts']}회 달성! 새로운 이정표를 세웠어요!"
        elif achievement_type == 'personal_best':
            return f"🏆 개인 최고 기록 갱신! {data['exercise']}에서 {data['weight']}kg 성공!"
        else:
            return "🌟 새로운 업적을 달성했어요!"
    
    def get_workout_feed(self, user_id, page=1, limit=10):
        """운동 관련 피드 가져오기"""
        # 실제로는 팔로우하는 사용자들의 운동 포스트를 가져옴
        start = (page - 1) * limit
        end = start + limit
        
        # 모의 데이터 생성
        if not self.mock_posts:
            self._generate_mock_posts()
        
        return {
            'posts': self.mock_posts[start:end],
            'total': len(self.mock_posts),
            'page': page,
            'has_next': end < len(self.mock_posts)
        }
    
    def _generate_mock_posts(self):
        """모의 포스트 데이터 생성"""
        for i in range(20):
            post_type = random.choice(['workout_complete', 'achievement', 'progress'])
            
            if post_type == 'workout_complete':
                self.mock_posts.append({
                    'id': i,
                    'user': {
                        'id': f'user_{i}',
                        'username': f'fitness_lover_{i}',
                        'profile_image': None
                    },
                    'content': f"오늘의 운동 완료! {random.randint(30, 90)}분간 열심히 했어요 💪",
                    'workout_info': {
                        'routine_name': random.choice(['전신 운동', '상체 운동', '하체 운동']),
                        'duration': random.randint(30, 90),
                        'calories_burned': random.randint(200, 500)
                    },
                    'likes': random.randint(0, 50),
                    'comments': random.randint(0, 10),
                    'created_at': datetime.now().isoformat(),
                    'type': 'workout_complete'
                })
            elif post_type == 'achievement':
                self.mock_posts.append({
                    'id': i,
                    'user': {
                        'id': f'user_{i}',
                        'username': f'achiever_{i}',
                        'profile_image': None
                    },
                    'content': f"🏆 {random.randint(7, 30)}일 연속 운동 달성!",
                    'achievement': {
                        'type': 'streak',
                        'days': random.randint(7, 30)
                    },
                    'likes': random.randint(10, 100),
                    'comments': random.randint(5, 20),
                    'created_at': datetime.now().isoformat(),
                    'type': 'achievement'
                })
    
    def add_workout_buddy(self, user_id, buddy_id):
        """운동 친구 추가"""
        return {
            'success': True,
            'message': '운동 친구가 추가되었습니다!',
            'buddy': {
                'id': buddy_id,
                'username': f'buddy_{buddy_id}'
            }
        }
    
    def get_workout_buddies(self, user_id):
        """운동 친구 목록 가져오기"""
        # 모의 데이터
        buddies = []
        for i in range(5):
            buddies.append({
                'id': f'buddy_{i}',
                'username': f'workout_buddy_{i}',
                'last_workout': datetime.now().isoformat(),
                'streak': random.randint(1, 30),
                'total_workouts': random.randint(10, 200)
            })
        return buddies
    
    def create_workout_challenge(self, creator_id, challenge_data):
        """운동 챌린지 생성"""
        challenge = {
            'id': random.randint(1000, 9999),
            'creator_id': creator_id,
            'name': challenge_data.get('name', '30일 운동 챌린지'),
            'description': challenge_data.get('description', '매일 30분 이상 운동하기'),
            'start_date': challenge_data.get('start_date', datetime.now().isoformat()),
            'end_date': challenge_data.get('end_date'),
            'participants': [creator_id],
            'type': challenge_data.get('type', 'duration'),  # duration, frequency, specific_exercise
            'goal': challenge_data.get('goal', {'minutes': 30, 'days': 30}),
            'created_at': datetime.now().isoformat()
        }
        return challenge
    
    def join_challenge(self, user_id, challenge_id):
        """챌린지 참가"""
        return {
            'success': True,
            'message': '챌린지에 참가했습니다!',
            'challenge_id': challenge_id
        }
    
    def get_leaderboard(self, challenge_id=None, period='week'):
        """리더보드 가져오기"""
        leaderboard = []
        
        for i in range(10):
            leaderboard.append({
                'rank': i + 1,
                'user': {
                    'id': f'user_{i}',
                    'username': f'athlete_{i}',
                    'profile_image': None
                },
                'stats': {
                    'total_workouts': random.randint(5, 30),
                    'total_duration': random.randint(150, 1000),
                    'calories_burned': random.randint(1000, 5000),
                    'streak': random.randint(1, 30)
                }
            })
        
        return {
            'period': period,
            'challenge_id': challenge_id,
            'leaderboard': leaderboard
        }

# 싱글톤 인스턴스
social_workout_service = SocialWorkoutService()
