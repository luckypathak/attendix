#!/usr/bin/env bash
# Exit on error
set -o errexit

COMMAND=$1

if [ "$COMMAND" = "build" ]; then
    python -m pip install -r requirements.txt
    python manage.py collectstatic --no-input
    python manage.py migrate
    python manage.py seed_celery_tasks
elif [ "$COMMAND" = "web" ]; then
    python manage.py collectstatic --no-input
    python manage.py migrate
    python manage.py seed_celery_tasks
    
    # Start Celery worker in background
    celery -A attendix worker --loglevel=info --concurrency=1 --max-tasks-per-child=50 &
    
    # Remove old beat pid file if it exists, otherwise Beat might crash on restart
    rm -f celerybeat.pid
    
    # Start Celery beat in background
    celery -A attendix beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler &
    
    exec gunicorn attendix.wsgi:application --bind 0.0.0.0:8000
elif [ "$COMMAND" = "worker" ]; then
    exec celery -A attendix worker --loglevel=info --concurrency=1 --max-tasks-per-child=50
elif [ "$COMMAND" = "beat" ]; then
    exec celery -A attendix beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
    # Fallback to dev server
    python manage.py migrate
    python manage.py seed_celery_tasks
    exec python manage.py runserver 0.0.0.0:8000
fi
