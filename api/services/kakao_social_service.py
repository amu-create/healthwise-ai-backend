"""
카카오 소셜 API 서비스
"""
import os
import logging
import requests
from django.conf import settings
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class KakaoSocialService:
    """카카오 소셜 API 통합 서비스"""
    
    def __init__(self):
        """카카오 API 초기화"""
        self.api_key = settings.KAKAO_API_KEY
        self.base_url = "https://kapi.kakao.com"
        
        if not self.api_key or self.api_key == "your-kakao-api-key-here":
            logger.warning("Kakao API key not configured")
    
    def share_workout_result(self, user_token: str, workout_data: Dict) -> Dict:
        """운동 결과를 카카오톡으로 공유"""
        try:
            # 템플릿 메시지 생성
            template = {
                "object_type": "feed",
                "content": {
                    "title": f"오늘의 운동 완료! 💪",
                    "description": f"{workout_data.get('exercise_type', '운동')} {workout_data.get('duration', 30)}분 완료!\n소모 칼로리: {workout_data.get('calories', 0)}kcal",
                    "image_url": workout_data.get('image_url', 'https://example.com/workout.jpg'),
                    "link": {
                        "web_url": "https://healthwiseaipro.netlify.app",
                        "mobile_web_url": "https://healthwiseaipro.netlify.app"
                    }
                },
                "social": {
                    "like_count": workout_data.get('likes', 0),
                    "comment_count": workout_data.get('comments', 0)
                },
                "buttons": [
                    {
                        "title": "자세히 보기",
                        "link": {
                            "web_url": f"https://healthwiseaipro.netlify.app/workout/{workout_data.get('id')}",
                            "mobile_web_url": f"https://healthwiseaipro.netlify.app/workout/{workout_data.get('id')}"
                        }
                    }
                ]
            }
            
            # 카카오톡 메시지 전송 API 호출
            headers = {
                'Authorization': f'Bearer {user_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(
                f"{self.base_url}/v2/api/talk/memo/default/send",
                headers=headers,
                data={'template_object': str(template)}
            )
            
            if response.status_code == 200:
                return {'success': True, 'message': '카카오톡 공유 성공'}
            else:
                return {'success': False, 'error': response.text}
                
        except Exception as e:
            logger.error(f"Kakao share error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_fitness_friends(self, user_token: str) -> List[Dict]:
        """운동 친구 목록 가져오기"""
        try:
            # 친구 목록 API 호출
            headers = {
                'Authorization': f'Bearer {user_token}'
            }
            
            response = requests.get(
                f"{self.base_url}/v1/api/talk/friends",
                headers=headers
            )
            
            if response.status_code == 200:
                friends = response.json().get('elements', [])
                # 운동 관련 친구만 필터링 (실제로는 앱 사용자 확인 필요)
                fitness_friends = [
                    {
                        'id': friend['id'],
                        'nickname': friend['profile_nickname'],
                        'profile_image': friend.get('profile_thumbnail_image', ''),
                        'is_fitness_user': True  # 실제로는 DB 확인 필요
                    }
                    for friend in friends
                ]
                return fitness_friends
            else:
                logger.error(f"Kakao friends API error: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Get fitness friends error: {str(e)}")
            return []
    
    def invite_to_challenge(self, user_token: str, friend_ids: List[str], challenge_data: Dict) -> Dict:
        """친구를 운동 챌린지에 초대"""
        try:
            # 초대 메시지 템플릿
            template = {
                "object_type": "text",
                "text": f"🏃‍♂️ {challenge_data.get('title', '운동 챌린지')}에 초대합니다!\n\n"
                       f"기간: {challenge_data.get('duration', '7일')}\n"
                       f"목표: {challenge_data.get('goal', '매일 30분 운동')}\n\n"
                       f"함께 건강한 습관을 만들어봐요! 💪",
                "link": {
                    "web_url": f"https://healthwiseaipro.netlify.app/challenge/{challenge_data.get('id')}",
                    "mobile_web_url": f"https://healthwiseaipro.netlify.app/challenge/{challenge_data.get('id')}"
                },
                "button_title": "챌린지 참여하기"
            }
            
            # 친구에게 메시지 전송
            headers = {
                'Authorization': f'Bearer {user_token}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            success_count = 0
            for friend_id in friend_ids:
                response = requests.post(
                    f"{self.base_url}/v1/api/talk/friends/message/default/send",
                    headers=headers,
                    data={
                        'receiver_uuids': f'["{friend_id}"]',
                        'template_object': str(template)
                    }
                )
                
                if response.status_code == 200:
                    success_count += 1
            
            return {
                'success': True,
                'invited_count': success_count,
                'total_count': len(friend_ids)
            }
            
        except Exception as e:
            logger.error(f"Invite to challenge error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_fitness_group(self, user_token: str, group_data: Dict) -> Dict:
        """운동 그룹 생성 (카카오톡 오픈채팅)"""
        # 실제 구현은 카카오톡 오픈채팅 API 연동 필요
        # 현재는 모의 구현
        return {
            'success': True,
            'group_id': 'mock_group_123',
            'invite_link': 'https://open.kakao.com/o/gXXXXXXX',
            'message': '운동 그룹이 생성되었습니다.'
        }


# 전역 인스턴스
_kakao_service = None

def get_kakao_service() -> KakaoSocialService:
    """카카오 서비스 인스턴스 가져오기 (싱글톤)"""
    global _kakao_service
    if not _kakao_service:
        _kakao_service = KakaoSocialService()
    return _kakao_service
