FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    mariadb-client-compat \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install the package
RUN pip install -e .

# Create directories
RUN mkdir -p /backups /logs /config

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_FILE_PATH=/logs/backup.log

# Entry point
ENTRYPOINT ["dbbackup"]
CMD ["--help"]
