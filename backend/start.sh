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
    exec gunicorn attendix.wsgi:application --bind 0.0.0.0:8000
elif [ "$COMMAND" = "worker" ]; then
    exec celery -A attendix worker --loglevel=info
elif [ "$COMMAND" = "beat" ]; then
    exec celery -A attendix beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
else
    # Fallback to dev server
    python manage.py migrate
    python manage.py seed_celery_tasks
    exec python manage.py runserver 0.0.0.0:8000
fi
