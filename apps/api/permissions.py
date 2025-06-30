from rest_framework.permissions import BasePermission, IsAuthenticated, AllowAny


class IsAuthenticatedOrReadOnly(BasePermission):
    """
    인증된 사용자는 모든 권한, 비인증 사용자는 읽기만 가능
    """
    def has_permission(self, request, view):
        # 읽기 권한은 모든 사용자에게 허용
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # 쓰기 권한은 인증된 사용자에게만 허용
        return request.user and request.user.is_authenticated


class IsOwnerOrReadOnly(BasePermission):
    """
    객체 소유자만 수정 가능, 다른 사용자는 읽기만 가능
    """
    def has_object_permission(self, request, view, obj):
        # 읽기 권한은 모든 사용자에게 허용
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        # 쓰기 권한은 소유자에게만 허용
        return obj.user == request.user


class GuestAccessPermission(BasePermission):
    """
    비회원도 제한적으로 접근 가능한 권한
    """
    # 비회원이 접근 가능한 기능들
    GUEST_ALLOWED_VIEWS = [
        'exercise_list',  # 운동 목록 보기
        'workout_videos',  # 운동 영상 보기
        'health_options',  # 건강 옵션 보기
        'daily_recommendations',  # 일일 추천 (제한적)
    ]
    
    def has_permission(self, request, view):
        # 인증된 사용자는 모든 권한
        if request.user and request.user.is_authenticated:
            return True
        
        # 비회원은 특정 뷰만 접근 가능
        view_name = view.__class__.__name__
        if view_name in self.GUEST_ALLOWED_VIEWS:
            return request.method in ['GET', 'HEAD', 'OPTIONS']
        
        return False
