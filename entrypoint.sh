#!/bin/sh
echo "Aguardando banco..."
until nc -z gaw_db 5432; do
  sleep 1
done

echo "Migrations..."
python manage.py migrate

echo "Static..."
python manage.py collectstatic --no-input

echo "Iniciando Gunicorn..."
exec gunicorn app.wsgi:application --bind 0.0.0.0:8000 --workers 3