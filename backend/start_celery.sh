#!/bin/bash
# Assuming you are in the backend directory and .venv is set up

echo "Starting Celery Worker..."
nohup .venv/bin/celery -A attendix worker -l info > celery_worker.log 2>&1 &

echo "Starting Celery Beat..."
nohup .venv/bin/celery -A attendix beat -l info > celery_beat.log 2>&1 &

echo "Celery and Celery Beat are now running in the background."
