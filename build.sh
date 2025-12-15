#!/usr/bin/env bash
set -o errexit

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Skip migrations during build - database might not be ready
echo "Skipping database migrations during build (will run at runtime if needed)"
# python manage.py migrate --noinput || echo "Database migration failed - continuing build..."
