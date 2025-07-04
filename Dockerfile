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

# Add wait_for_db script
COPY wait_for_db.py .

# Set executable permissions for start script
RUN chmod +x railway-start.sh

# Run migrations and start server
CMD ["./railway-start.sh"]
