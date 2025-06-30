#!/bin/bash
# Railway build script

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Running migrations..."
python manage.py migrate --noinput || echo "Migrations skipped"

echo "Build complete!"