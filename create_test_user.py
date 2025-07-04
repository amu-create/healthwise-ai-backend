#!/usr/bin/env python
"""
테스트 사용자 생성 스크립트
"""
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthwise.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import UserProfile

def create_test_user():
    """테스트 사용자 생성 또는 업데이트"""
    email = 'ww@ww.ww'
    username = '전서기'
    password = 'test123'
    
    try:
        # 기존 사용자 확인
        try:
            user = User.objects.get(email=email)
            print(f"기존 사용자 발견: {user.username}")
            
            # 비밀번호 업데이트
            user.set_password(password)
            user.save()
            print(f"비밀번호 업데이트 완료: {password}")
            
        except User.DoesNotExist:
            # 새 사용자 생성
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            print(f"새 사용자 생성: {username}")
        
        # 프로필 확인 및 생성
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                'birth_date': '1990-01-01',
                'gender': 'M',
                'height': 170.0,
                'weight': 70.0,
                'fitness_level': 'intermediate',
                'fitness_goals': ['weight_loss', 'muscle_gain']
            }
        )
        
        if created:
            print(f"프로필 생성 완료")
        else:
            print(f"기존 프로필 사용")
        
        print(f"\n=== 테스트 계정 정보 ===")
        print(f"이메일: {email}")
        print(f"사용자명: {username}")
        print(f"비밀번호: {password}")
        print(f"사용자 ID: {user.id}")
        print(f"프로필 ID: {profile.id}")
        
        return True
        
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        return False

if __name__ == '__main__':
    create_test_user()
