#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthwise.settings')
    
    # 마이그레이션 적용
    from django.core.management import execute_from_command_line
    
    # collectstatic 실행 전에 마이그레이션
    if 'collectstatic' not in sys.argv:
        try:
            execute_from_command_line(['manage.py', 'migrate', '--noinput'])
        except Exception as e:
            print(f"Migration failed: {e}")
    
    execute_from_command_line(sys.argv)
