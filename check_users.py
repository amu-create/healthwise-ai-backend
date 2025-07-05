from django.contrib.auth.models import User

# 모든 사용자 출력
users = User.objects.all()
print(f"Total users: {users.count()}")
for user in users:
    print(f"- Username: {user.username}, Email: {user.email}, Active: {user.is_active}")

# ww@ww.ww 이메일로 사용자 찾기
try:
    user = User.objects.get(email='ww@ww.ww')
    print(f"\nFound user: {user.username}")
    print(f"Can authenticate with 'ww': {user.check_password('ww')}")
except User.DoesNotExist:
    print("\nUser with email ww@ww.ww not found")

# 사용자명으로 찾기
try:
    user = User.objects.get(username='전서기')
    print(f"\nFound user by username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Can authenticate with 'ww': {user.check_password('ww')}")
except User.DoesNotExist:
    print("\nUser with username '전서기' not found")
