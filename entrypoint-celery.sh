#!/bin/sh
set -e

echo "Waiting for database..."
python manage.py wait_for_db --timeout 60

echo "Reading RabbitMQ secret..."
if [ -f "/run/secrets/gaw_rabbitmq_password" ] && [ -z "${CELERY_BROKER_URL}" ]; then
    RABBITMQ_PASSWORD="$(cat /run/secrets/gaw_rabbitmq_password)"
    export CELERY_BROKER_URL="amqp://${RABBITMQ_USER:-gaw_app}:${RABBITMQ_PASSWORD}@${RABBITMQ_HOST:-rabbitmq}:5672//"
fi

echo "Starting Celery..."
exec "$@"
