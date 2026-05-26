#!/bin/bash
set -e

echo "Running seed script to populate database..."
python data/seed.py

echo "Starting application..."
exec python api/app.py
