import random

def get_social_posts():
    """소셜 피드 Mock 데이터"""
    return [
        {
            'id': 1,
            'user': {
                'id': 1,
                'username': 'fitness_lover',
                'avatar': 'https://example.com/avatar1.jpg',
                'profile_image': None,
                'profile_picture_url': None,
                'email': 'fitness_lover@example.com'
            },
            'content': '오늘 5km 러닝 완주! 💪 새로운 개인 기록을 세웠어요!',
            'media_file': None,
            'visibility': 'public',
            'workout_data': {
                'type': 'running',
                'duration': 25,
                'distance': 5.0,
                'calories': 420
            },
            'likes': [],
            'likes_count': random.randint(10, 50),
            'comments': [],
            'comments_count': random.randint(2, 15),
            'shares_count': 0,
            'is_liked': False,
            'is_saved': False,
            'created_at': '2024-06-30T08:30:00Z',
            'liked_by_user': False,
            'reactions': [],
            'tags': [],
            'mentions': []
        },
        {
            'id': 2,
            'user': {
                'id': 2,
                'username': 'healthy_eater',
                'avatar': 'https://example.com/avatar2.jpg',
                'profile_image': None,
                'profile_picture_url': None,
                'email': 'healthy_eater@example.com'
            },
            'content': '아침 식사로 준비한 건강한 볼! 🥗 퀴노아, 아보카도, 연어가 들어간 영양가득한 한 그릇',
            'image_url': 'https://example.com/food1.jpg',
            'media_file': 'https://example.com/food1.jpg',
            'visibility': 'public',
            'nutrition_data': {
                'calories': 450,
                'protein': 28,
                'carbs': 35,
                'fat': 22
            },
            'likes': [],
            'likes_count': random.randint(15, 60),
            'comments': [],
            'comments_count': random.randint(3, 20),
            'shares_count': 0,
            'is_liked': True,
            'is_saved': False,
            'created_at': '2024-06-30T07:15:00Z',
            'liked_by_user': True,
            'reactions': [],
            'tags': [],
            'mentions': []
        }
    ]

def create_post(content, workout_session_id=None, image_url=None):
    """새 포스트 생성"""
    return {
        'id': random.randint(1000, 9999),
        'content': content,
        'workout_session_id': workout_session_id,
        'image_url': image_url,
        'likes_count': 0,
        'comments_count': 0,
        'created_at': '2024-06-30T12:00:00Z'
    }

def like_post_action(post_id):
    """포스트 좋아요"""
    return {
        'success': True,
        'post_id': post_id,
        'liked': True,
        'likes_count': random.randint(1, 50)
    }
