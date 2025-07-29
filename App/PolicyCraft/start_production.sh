#!/bin/bash
# Production startup script for PolicyCraft
# Author: Jacek Robert Kszczot

echo "🚀 Starting PolicyCraft in production mode..."

# Set production environment variables
export FLASK_ENV=production
export FLASK_DEBUG=False

# Create necessary directories
python -c "from config import create_secure_directories; create_secure_directories()"

# Install spaCy model if not present
python -m spacy download en_core_web_sm 2>/dev/null || echo "spaCy model already installed"

# Start Gunicorn server
echo "🌐 Starting Gunicorn server..."
gunicorn --bind 0.0.0.0:5001 --workers 4 --timeout 120 --max-requests 1000 --preload wsgi:application
