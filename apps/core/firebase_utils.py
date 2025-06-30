import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

# Firebase Admin SDK 초기화
creds = credentials.Certificate(
    os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
)

# Firebase 앱이 이미 초기화되었는지 확인
if not firebase_admin._apps:
    firebase_admin.initialize_app(creds)

def send_notification(token, title, body, data=None, badge=None):
    """
    FCM을 통해 푸시 알림을 전송합니다.
    
    Args:
        token: FCM 토큰
        title: 알림 제목
        body: 알림 내용
        data: 추가 데이터 (dict)
        badge: iOS 뱃지 카운트
    
    Returns:
        FCM 메시지 ID 또는 None (실패 시)
    """
    try:
        # 메시지 구성
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
        )
        
        # 추가 데이터가 있으면 포함
        if data:
            message.data = {k: str(v) for k, v in data.items()}
        
        # iOS 뱃지 설정
        if badge is not None:
            message.apns = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(badge=badge)
                )
            )
        
        # 안드로이드 설정
        message.android = messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default',
                icon='ic_notification',
                channel_id='healthwise_notifications'
            )
        )
        
        # 메시지 전송
        response = messaging.send(message)
        return response
        
    except Exception as e:
        print(f"FCM 알림 전송 실패: {str(e)}")
        return None


def send_multicast_notification(tokens, title, body, data=None):
    """
    여러 기기에 동시에 알림을 전송합니다.
    
    Args:
        tokens: FCM 토큰 리스트
        title: 알림 제목
        body: 알림 내용
        data: 추가 데이터 (dict)
    
    Returns:
        BatchResponse 객체
    """
    try:
        # 메시지 구성
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            tokens=tokens,
        )
        
        # 추가 데이터가 있으면 포함
        if data:
            message.data = {k: str(v) for k, v in data.items()}
        
        # 안드로이드 설정
        message.android = messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default',
                icon='ic_notification',
                channel_id='healthwise_notifications'
            )
        )
        
        # 메시지 전송
        response = messaging.send_multicast(message)
        return response
        
    except Exception as e:
        print(f"FCM 멀티캐스트 알림 전송 실패: {str(e)}")
        return None


def subscribe_to_topic(tokens, topic_name):
    """
    토픽 구독
    
    Args:
        tokens: FCM 토큰 리스트
        topic_name: 구독할 토픽 이름
    
    Returns:
        성공 여부
    """
    try:
        response = messaging.subscribe_to_topic(tokens, topic_name)
        print(f'{response.success_count} 토큰이 {topic_name} 토픽에 구독되었습니다.')
        return True
    except Exception as e:
        print(f"토픽 구독 실패: {str(e)}")
        return False


def unsubscribe_from_topic(tokens, topic_name):
    """
    토픽 구독 해제
    
    Args:
        tokens: FCM 토큰 리스트
        topic_name: 구독 해제할 토픽 이름
    
    Returns:
        성공 여부
    """
    try:
        response = messaging.unsubscribe_from_topic(tokens, topic_name)
        print(f'{response.success_count} 토큰이 {topic_name} 토픽에서 구독 해제되었습니다.')
        return True
    except Exception as e:
        print(f"토픽 구독 해제 실패: {str(e)}")
        return False


def send_topic_notification(topic_name, title, body, data=None):
    """
    특정 토픽을 구독한 모든 기기에 알림 전송
    
    Args:
        topic_name: 토픽 이름
        title: 알림 제목
        body: 알림 내용
        data: 추가 데이터 (dict)
    
    Returns:
        메시지 ID 또는 None
    """
    try:
        # 메시지 구성
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            topic=topic_name,
        )
        
        # 추가 데이터가 있으면 포함
        if data:
            message.data = {k: str(v) for k, v in data.items()}
        
        # 메시지 전송
        response = messaging.send(message)
        return response
        
    except Exception as e:
        print(f"토픽 알림 전송 실패: {str(e)}")
        return None
