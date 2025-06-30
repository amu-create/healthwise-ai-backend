from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from .models import Notification
from .serializers import NotificationSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_list(request):
    """알림 목록 조회"""
    notifications = Notification.objects.filter(user=request.user)
    
    # 페이지네이션
    page = request.GET.get('page', 1)
    page_size = request.GET.get('page_size', 20)
    
    paginator = Paginator(notifications, page_size)
    try:
        page_obj = paginator.page(page)
    except:
        return Response({
            'results': [],
            'count': 0,
            'unread_count': 0
        })
    
    # 직렬화
    serializer = NotificationSerializer(
        page_obj.object_list, 
        many=True,
        context={'request': request}
    )
    
    # 읽지 않은 알림 개수
    unread_count = notifications.filter(is_read=False).count()
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous(),
        'unread_count': unread_count
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read(request, pk):
    """개별 알림 읽음 처리"""
    try:
        notification = Notification.objects.get(
            pk=pk,
            user=request.user
        )
        notification.is_read = True
        notification.save()
        
        return Response({'message': '알림을 읽음 처리했습니다.'})
    except Notification.DoesNotExist:
        return Response(
            {'error': '알림을 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_all_notifications_read(request):
    """모든 알림 읽음 처리"""
    updated = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)
    
    return Response({
        'message': f'{updated}개의 알림을 읽음 처리했습니다.'
    })


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_notification(request, pk):
    """알림 삭제"""
    try:
        notification = Notification.objects.get(
            pk=pk,
            user=request.user
        )
        notification.delete()
        
        return Response({'message': '알림을 삭제했습니다.'})
    except Notification.DoesNotExist:
        return Response(
            {'error': '알림을 찾을 수 없습니다.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_all_notifications(request):
    """모든 알림 삭제"""
    deleted = Notification.objects.filter(user=request.user).delete()
    
    return Response({
        'message': f'{deleted[0]}개의 알림을 삭제했습니다.'
    })
