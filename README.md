# HealthWise AI Backend

## Railway Deployment Ready Django Backend

This is a minimal Django backend configured for Railway deployment.

### Features
- Django 5.0+
- Django REST Framework
- PostgreSQL support (via DATABASE_URL)
- Redis support (via REDIS_URL)
- CORS configured for Netlify frontend
- WhiteNoise for static files
- Gunicorn WSGI server

### Railway Deployment

1. Connect this repository to Railway
2. Railway will auto-detect Python and install dependencies
3. Set environment variables:
   - `DATABASE_URL` (auto-provided by Railway PostgreSQL)
   - `REDIS_URL` (auto-provided by Railway Redis)
   - `SECRET_KEY` (generate a secure key)
   - `ALLOWED_HOSTS` (optional, defaults include Railway domains)

### Local Development

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### API Endpoints

- `/` - API status
- `/health/` - Health check
- `/api/test/` - Test endpoint
- `/api/guest/profile/` - Guest profile
- `/api/auth/csrf/` - CSRF token
- `/admin/` - Django admin