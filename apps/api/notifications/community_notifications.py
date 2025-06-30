from datetime import timedelta
from django.utils import timezone
from apps.api.notification_service_v2 import NotificationService
from apps.social.models import SocialProfile, SocialPost
import logging

logger = logging.getLogger(__name__)


class CommunityNotificationService:
    """커뮤니티 관련 알림 서비스"""
    
    @staticmethod
    def send_friend_request_notification(from_user, to_user, message=None):
        """친구 요청 알림"""
        from_profile = getattr(from_user, 'social_profile', None)
        
        NotificationService.create_notification(
            user=to_user,
            notification_type='social',
            title_ko='새로운 친구 요청',
            title_en='New Friend Request',
            title_es='Nueva Solicitud de Amistad',
            message_ko=f'{from_user.username}님이 친구 요청을 보냈습니다.',
            message_en=f'{from_user.username} sent you a friend request.',
            message_es=f'{from_user.username} te envió una solicitud de amistad.',
            metadata={
                'icon': 'person_add',
                'from_user_id': from_user.id,
                'from_username': from_user.username,
                'from_profile_picture': from_profile.profile_picture_url if from_profile else None,
                'request_message': message
            },
            action_url='/social/friend-requests'
        )
        
        # 실시간 알림
        NotificationService.send_realtime_notification(to_user, {
            'type': 'friend_request',
            'from_user': {
                'id': from_user.id,
                'username': from_user.username,
                'profile_picture': from_profile.profile_picture_url if from_profile else None
            },
            'message': message
        })
    
    @staticmethod
    def send_friend_request_accepted(accepted_by, requested_user):
        """친구 요청 수락 알림"""
        accepted_profile = getattr(accepted_by, 'social_profile', None)
        
        NotificationService.create_notification(
            user=requested_user,
            notification_type='social',
            title_ko='친구 요청 수락됨',
            title_en='Friend Request Accepted',
            title_es='Solicitud de Amistad Aceptada',
            message_ko=f'{accepted_by.username}님이 친구 요청을 수락했습니다!',
            message_en=f'{accepted_by.username} accepted your friend request!',
            message_es=f'¡{accepted_by.username} aceptó tu solicitud de amistad!',
            metadata={
                'icon': 'check_circle',
                'user_id': accepted_by.id,
                'username': accepted_by.username,
                'profile_picture': accepted_profile.profile_picture_url if accepted_profile else None
            },
            action_url=f'/profile/{accepted_by.username}'
        )
    
    @staticmethod
    def send_workout_challenge_invitation(from_user, to_user, challenge):
        """운동 챌린지 초대 알림"""
        NotificationService.create_notification(
            user=to_user,
            notification_type='challenge',
            title_ko='운동 챌린지 초대',
            title_en='Workout Challenge Invitation',
            title_es='Invitación al Desafío de Ejercicio',
            message_ko=f'{from_user.username}님이 "{challenge.name}" 챌린지에 초대했습니다!',
            message_en=f'{from_user.username} invited you to the "{challenge.name}" challenge!',
            message_es=f'¡{from_user.username} te invitó al desafío "{challenge.name}"!',
            metadata={
                'icon': 'challenge',
                'from_user_id': from_user.id,
                'from_username': from_user.username,
                'challenge_id': challenge.id,
                'challenge_name': challenge.name,
                'challenge_type': challenge.type,
                'duration_days': challenge.duration_days
            },
            action_url=f'/challenges/{challenge.id}'
        )
    
    @staticmethod
    def send_group_workout_invitation(organizer, invited_users, workout_session):
        """그룹 운동 초대 알림"""
        for user in invited_users:
            NotificationService.create_notification(
                user=user,
                notification_type='social',
                title_ko='그룹 운동 초대',
                title_en='Group Workout Invitation',
                title_es='Invitación a Ejercicio Grupal',
                message_ko=f'{organizer.username}님이 {workout_session.scheduled_at.strftime("%m월 %d일 %H:%M")} 그룹 운동에 초대했습니다.',
                message_en=f'{organizer.username} invited you to a group workout on {workout_session.scheduled_at.strftime("%b %d at %I:%M %p")}.',
                message_es=f'{organizer.username} te invitó a un ejercicio grupal el {workout_session.scheduled_at.strftime("%d de %b a las %H:%M")}.',
                metadata={
                    'icon': 'group',
                    'organizer_id': organizer.id,
                    'organizer_username': organizer.username,
                    'session_id': workout_session.id,
                    'workout_type': workout_session.workout_type,
                    'scheduled_at': workout_session.scheduled_at.isoformat(),
                    'location': workout_session.location
                },
                action_url=f'/workouts/group/{workout_session.id}'
            )
    
    @staticmethod
    def send_workout_partner_match(user1, user2, match_score):
        """운동 파트너 매칭 알림"""
        # user1에게 알림
        user2_profile = getattr(user2, 'social_profile', None)
        NotificationService.create_notification(
            user=user1,
            notification_type='match',
            title_ko='운동 파트너 매칭!',
            title_en='Workout Partner Match!',
            title_es='¡Compañero de Ejercicio Encontrado!',
            message_ko=f'{user2.username}님과 {match_score}% 매칭되었습니다! 비슷한 운동 목표를 가지고 있어요.',
            message_en=f'You matched {match_score}% with {user2.username}! You have similar fitness goals.',
            message_es=f'¡Coincidiste {match_score}% con {user2.username}! Tienen objetivos de fitness similares.',
            metadata={
                'icon': 'fitness_center',
                'matched_user_id': user2.id,
                'matched_username': user2.username,
                'matched_profile_picture': user2_profile.profile_picture_url if user2_profile else None,
                'match_score': match_score
            },
            action_url=f'/profile/{user2.username}'
        )
        
        # user2에게도 알림
        user1_profile = getattr(user1, 'social_profile', None)
        NotificationService.create_notification(
            user=user2,
            notification_type='match',
            title_ko='운동 파트너 매칭!',
            title_en='Workout Partner Match!',
            title_es='¡Compañero de Ejercicio Encontrado!',
            message_ko=f'{user1.username}님과 {match_score}% 매칭되었습니다! 비슷한 운동 목표를 가지고 있어요.',
            message_en=f'You matched {match_score}% with {user1.username}! You have similar fitness goals.',
            message_es=f'¡Coincidiste {match_score}% con {user1.username}! Tienen objetivos de fitness similares.',
            metadata={
                'icon': 'fitness_center',
                'matched_user_id': user1.id,
                'matched_username': user1.username,
                'matched_profile_picture': user1_profile.profile_picture_url if user1_profile else None,
                'match_score': match_score
            },
            action_url=f'/profile/{user1.username}'
        )
    
    @staticmethod
    def send_community_milestone_notification(user, milestone_type, value):
        """커뮤니티 활동 마일스톤 알림"""
        milestones = {
            'first_post': {
                'title': ('첫 게시물 작성!', 'First Post!', '¡Primera Publicación!'),
                'message': ('커뮤니티에 첫 발걸음을 내디뎠습니다!', 
                           'You\'ve taken your first step in the community!',
                           '¡Has dado tu primer paso en la comunidad!')
            },
            'posts_10': {
                'title': ('10개 게시물 달성!', '10 Posts Milestone!', '¡10 Publicaciones!'),
                'message': ('활발한 커뮤니티 활동을 하고 있어요!',
                           'You\'re an active community member!',
                           '¡Eres un miembro activo de la comunidad!')
            },
            'followers_10': {
                'title': ('팔로워 10명 달성!', '10 Followers!', '¡10 Seguidores!'),
                'message': ('많은 사람들이 당신의 운동 여정을 응원합니다!',
                           'Many people are supporting your fitness journey!',
                           '¡Muchas personas apoyan tu viaje de fitness!')
            },
            'followers_100': {
                'title': ('팔로워 100명 달성!', '100 Followers!', '¡100 Seguidores!'),
                'message': ('당신은 피트니스 인플루언서입니다!',
                           'You\'re a fitness influencer!',
                           '¡Eres un influencer de fitness!')
            },
        }
        
        if milestone_type in milestones:
            milestone_data = milestones[milestone_type]
            title_ko, title_en, title_es = milestone_data['title']
            message_ko, message_en, message_es = milestone_data['message']
            
            NotificationService.create_notification(
                user=user,
                notification_type='achievement',
                title_ko=title_ko,
                title_en=title_en,
                title_es=title_es,
                message_ko=message_ko,
                message_en=message_en,
                message_es=message_es,
                metadata={
                    'icon': 'achievement',
                    'milestone_type': milestone_type,
                    'value': value,
                    'badge_type': 'community'
                },
                action_url='/achievements'
            )
    
    @staticmethod
    def send_trending_post_notification(user, post):
        """인기 게시물 알림"""
        likes_count = post.likes.count()
        comments_count = post.comments.count()
        
        NotificationService.create_notification(
            user=user,
            notification_type='social',
            title_ko='게시물이 인기를 얻고 있어요! 🔥',
            title_en='Your Post is Trending! 🔥',
            title_es='¡Tu Publicación es Tendencia! 🔥',
            message_ko=f'게시물이 {likes_count}개의 좋아요와 {comments_count}개의 댓글을 받았습니다!',
            message_en=f'Your post received {likes_count} likes and {comments_count} comments!',
            message_es=f'¡Tu publicación recibió {likes_count} me gusta y {comments_count} comentarios!',
            metadata={
                'icon': 'trending',
                'post_id': post.id,
                'likes_count': likes_count,
                'comments_count': comments_count,
                'engagement_rate': (likes_count + comments_count) * 100 / max(post.views_count, 1)
            },
            action_url=f'/social/post/{post.id}'
        )
    
    @staticmethod
    def send_mention_notification(mentioned_user, mentioning_user, post):
        """멘션 알림"""
        content_preview = post.content[:50] + '...' if len(post.content) > 50 else post.content
        
        NotificationService.create_notification(
            user=mentioned_user,
            notification_type='social',
            title_ko='새로운 멘션',
            title_en='New Mention',
            title_es='Nueva Mención',
            message_ko=f'{mentioning_user.username}님이 게시물에서 당신을 언급했습니다.',
            message_en=f'{mentioning_user.username} mentioned you in a post.',
            message_es=f'{mentioning_user.username} te mencionó en una publicación.',
            metadata={
                'icon': 'mention',
                'from_user_id': mentioning_user.id,
                'from_username': mentioning_user.username,
                'post_id': post.id,
                'content_preview': content_preview
            },
            action_url=f'/social/post/{post.id}'
        )
