#!/usr/bin/env bash

# Wait for database to be ready (simple check)
echo "Waiting for database connection..."
sleep 2

# Run migrations
python manage.py migrate --noinput

# Create admin if environment variables are set and no admin exists
if [ -n "$DEFAULT_ADMIN_EMAIL" ] && [ -n "$DEFAULT_ADMIN_PASSWORD" ]; then
    echo "Checking if admin user needs to be created..."
    python -c "
import os
import django
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating admin user...')
    User.objects.create_superuser(
        username=os.getenv('DEFAULT_ADMIN_USERNAME', 'admin'),
        email=os.getenv('DEFAULT_ADMIN_EMAIL'),
        password=os.getenv('DEFAULT_ADMIN_PASSWORD')
    )
    print('Admin user created')
else:
    print('Admin user already exists')
" || echo "Admin check failed"
fi

# Start Gunicorn
exec gunicorn booking_system.wsgi:application --bind 0.0.0.0:$PORT
