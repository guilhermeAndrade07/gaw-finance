#!/bin/sh
set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
. "${PROJECT_DIR}/scripts/load_runtime_env.sh"

echo "Waiting for database..."
python manage.py wait_for_db --timeout 60

echo "Starting Gunicorn..."
exec gunicorn app.wsgi:application --config gunicorn.conf.py
