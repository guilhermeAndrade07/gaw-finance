#!/bin/sh
set -eu

read_secret() {
    secret_path="/run/secrets/$1"
    if [ -f "$secret_path" ]; then
        cat "$secret_path"
    fi
}

urlencode() {
    VALUE_TO_ENCODE="$1" python -c 'import os; from urllib.parse import quote; print(quote(os.environ["VALUE_TO_ENCODE"], safe=""))'
}

if [ -z "${SECRET_KEY:-}" ]; then
    secret_value="$(read_secret gaw_secret_key)"
    if [ -n "$secret_value" ]; then
        export SECRET_KEY="$secret_value"
    fi
fi

if [ -z "${DATABASE_URL:-}" ]; then
    secret_value="$(read_secret gaw_db_password)"
    if [ -n "$secret_value" ]; then
        database_user="$(urlencode "${POSTGRES_USER:-postgres}")"
        database_password="$(urlencode "$secret_value")"
        database_host="${POSTGRES_HOST:-db}"
        database_port="${POSTGRES_PORT:-5432}"
        database_name="$(urlencode "${POSTGRES_DB:-gaw_db}")"
        export DATABASE_URL="postgres://${database_user}:${database_password}@${database_host}:${database_port}/${database_name}"
    fi
fi

if [ -z "${CELERY_BROKER_URL:-}" ]; then
    secret_value="$(read_secret gaw_rabbitmq_password)"
    if [ -n "$secret_value" ]; then
        rabbit_user="$(urlencode "${RABBITMQ_USER:-gaw_app}")"
        rabbit_password="$(urlencode "$secret_value")"
        rabbit_host="${RABBITMQ_HOST:-rabbitmq}"
        export CELERY_BROKER_URL="amqp://${rabbit_user}:${rabbit_password}@${rabbit_host}:5672//"
    fi
fi
