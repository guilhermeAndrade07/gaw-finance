#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py wait_for_db --timeout 60

echo "Starting Celery..."
exec "$@"
