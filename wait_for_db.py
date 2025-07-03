#!/usr/bin/env python
"""
Wait for database to be ready before starting the application
"""
import os
import sys
import time
import psycopg2
from psycopg2 import OperationalError


def wait_for_db(max_retries=30, delay=2):
    """Wait for database to be ready"""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not set!")
        return False
    
    print(f"📝 DATABASE_URL found: {database_url[:50]}...")
    
    for attempt in range(max_retries):
        try:
            print(f"🔄 Attempt {attempt + 1}/{max_retries}: Connecting to database...")
            conn = psycopg2.connect(database_url)
            conn.close()
            print("✅ Successfully connected to database!")
            return True
        except OperationalError as e:
            print(f"⏳ Database not ready yet: {str(e)}")
            if attempt < max_retries - 1:
                print(f"⏰ Waiting {delay} seconds before retry...")
                time.sleep(delay)
            else:
                print("❌ Failed to connect to database after all retries")
                return False
    
    return False


if __name__ == "__main__":
    print("🚀 Starting database connection check...")
    
    # Print all environment variables for debugging
    print("\n📋 Environment Variables:")
    for key, value in os.environ.items():
        if 'DATABASE' in key or 'POSTGRES' in key or 'REDIS' in key:
            # Mask sensitive parts
            if 'URL' in key or 'PASSWORD' in key:
                masked_value = value[:20] + '...' if value else 'NOT SET'
                print(f"  {key}: {masked_value}")
            else:
                print(f"  {key}: {value}")
    
    if wait_for_db():
        print("\n✅ Database is ready! Starting application...")
        sys.exit(0)
    else:
        print("\n❌ Database connection failed!")
        sys.exit(1)
