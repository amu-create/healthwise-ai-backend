"""
Supabase Database Configuration for HealthWise
"""

import os
from urllib.parse import urlparse

# Supabase 연결 정보
SUPABASE_URL = "https://dlpgytnjeincukjkwitx.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRscGd5dG5qZWluY3Vramt3aXR4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEyNDc0OTcsImV4cCI6MjA2NjgyMzQ5N30.WknVc0Qsop0DqTkD857MvtfLjmTMG5anupGuh4ZVy7Q"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRscGd5dG5qZWluY3Vramt3aXR4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTI0NzQ5NywiZXhwIjoyMDY2ODIzNDk3fQ.3yQEuFdGrjC9qPDvY7pP5JlKfD4X2UcO6WqGmYvD8Bw"

# Supabase Database URL - Railway 환경에 맞게 설정
def get_supabase_database_config():
    """Get Supabase database configuration"""
    # Direct connection string (for migrations and admin)
    direct_url = "postgresql://postgres.dlpgytnjeincukjkwitx:postgrespostgre@db.dlpgytnjeincukjkwitx.supabase.co:5432/postgres"
    
    # Connection pooler URL (for application)
    pooler_url = "postgresql://postgres.dlpgytnjeincukjkwitx:postgrespostgre@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres"
    
    # Railway 환경에서는 pooler URL 사용
    database_url = os.environ.get('SUPABASE_DATABASE_URL', pooler_url)
    
    # Parse the URL
    parsed = urlparse(database_url)
    
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': parsed.path[1:],  # Remove leading slash
        'USER': parsed.username,
        'PASSWORD': parsed.password,
        'HOST': parsed.hostname,
        'PORT': parsed.port,
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 30,
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
    }

# Supabase Storage 설정
SUPABASE_STORAGE_BUCKET = 'healthwise-uploads'

# Supabase Auth 설정
SUPABASE_JWT_SECRET = "gbZPB0WpsVEFI8ayQAjfUQBWSVJ8EvC+dwtpfgD8KjOG4crbBC8sr0MKvW2fFZPRLSQ4NYm/OT5pgTWpT31w4Q=="
