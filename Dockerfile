FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Add wait_for_db script
COPY wait_for_db.py .

# Run migrations and start server
CMD python wait_for_db.py && \
    python manage.py migrate --noinput && \
    gunicorn healthwise.wsgi:application --bind 0.0.0.0:${PORT:-8000}