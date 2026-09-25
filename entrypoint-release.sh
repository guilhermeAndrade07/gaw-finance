#!/bin/sh
set -eu

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
. "${PROJECT_DIR}/scripts/load_runtime_env.sh"

echo "Waiting for database..."
python manage.py wait_for_db --timeout 120

echo "Running release migrations..."
python manage.py migrate_safe --no-input

echo "Collecting static files..."
python manage.py collectstatic --clear --no-input

echo "Validating production configuration..."
python manage.py check --deploy

echo "Release completed."
