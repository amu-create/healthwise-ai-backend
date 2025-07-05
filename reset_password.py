import os
import django
from django.contrib.auth.models import User

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthwise.settings')
django.setup()

# 사용자 확인 및 비밀번호 재설정
try:
    user = User.objects.get(email='ww@ww.ww')
    print(f"Found user: {user.username}")
    user.set_password('ww')
    user.save()
    print("Password reset to 'ww'")
except User.DoesNotExist:
    print("User not found, creating new user...")
    user = User.objects.create_user(
        username='전서기',
        email='ww@ww.ww',
        password='ww'
    )
    print(f"Created user: {user.username}")

# 비밀번호 확인
print(f"Password check: {user.check_password('ww')}")
