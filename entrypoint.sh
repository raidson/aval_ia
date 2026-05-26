#!/bin/bash
set -e

echo "Running seed script to populate database..."
python data/seed.py

echo "Starting application..."
# O Gunicorn precisa do módulo e app, no caso de api/app.py é api.app:app
exec gunicorn --bind 0.0.0.0:${PORT:-5000} api.app:app
