"""
Supabase configuration for healthwise project
"""
import os
import dj_database_url

# Supabase configuration
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://dlpgytnjeincukjkwitx.supabase.co')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRscGd5dG5qZWluY3Vramt3aXR4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEyNDc0OTcsImV4cCI6MjA2NjgyMzQ5N30.WknVc0Qsop0DqTkD857MvtfLjmTMG5anupGuh4ZVy7Q')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRscGd5dG5qZWluY3Vramt3aXR4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTI0NzQ5NywiZXhwIjoyMDY2ODIzNDk3fQ.nHaGaEhc0xzkkqBxHJCCfwF5RO7gQMjzh-d3ZOPSgKo')

# Database URL for Supabase
SUPABASE_DATABASE_URL = os.environ.get('SUPABASE_DATABASE_URL', 'postgresql://postgres.dlpgytnjeincukjkwitx:postgrespostgre@aws-0-ap-northeast-2.pooler.supabase.com:6543/postgres')

def get_supabase_database_config():
    """Get Supabase database configuration"""
    # 🚨 SUPABASE_DATABASE_URL을 우선 사용 (Railway 자동 DATABASE_URL 무시)
    database_url = os.environ.get('SUPABASE_DATABASE_URL') or SUPABASE_DATABASE_URL
    
    # Railway의 자동 DATABASE_URL 무시하고 강제로 Supabase 사용
    print(f"Using Supabase database: {database_url[:50]}...")
    
    config = dj_database_url.config(
        default=database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
    # SSL 설정 추가 (Supabase 필수)
    config['OPTIONS'] = {
        'sslmode': 'require',
        'connect_timeout': 60,
        'options': '-c default_transaction_isolation=read_committed'
    }
    return config
