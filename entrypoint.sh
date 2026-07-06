#!/bin/sh
set -e

echo "Reading Docker Secrets..."
if [ -f "/run/secrets/gaw_secret_key" ]; then
    export SECRET_KEY="$(cat /run/secrets/gaw_secret_key)"
fi

if [ -f "/run/secrets/gaw_db_password" ] && [ -z "${DATABASE_URL}" ]; then
    DB_PASSWORD="$(cat /run/secrets/gaw_db_password)"
    export DATABASE_URL="postgres://${POSTGRES_USER:-postgres}:${DB_PASSWORD}@${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-gaw_db}"
fi

echo "Waiting for database..."
python manage.py wait_for_db --timeout 60

echo "Running migrations (with advisory lock)..."
python manage.py migrate_safe --no-input

echo "Collecting static files..."
python manage.py collectstatic --clear --no-input

echo "Starting Gunicorn..."
exec gunicorn app.wsgi:application --config gunicorn.conf.py
