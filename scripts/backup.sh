#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_DIR}/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
STACK_NAME="gaw_finance"

# Safe .env parser (never uses source/.)
parse_env() {
    local env_file="$1"
    if [ ! -f "$env_file" ]; then
        echo "ERROR: $env_file not found."
        exit 1
    fi
    set -a
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|#*) continue ;;
        esac
        key="${line%%=*}"
        value="${line#*=}"
        value="${value#\"}"; value="${value%\"}"
        value="${value#\'}"; value="${value%\'}"
        export "$key=$value"
    done < "$env_file"
    set +a
}

parse_env "$ENV_FILE"

TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"
mkdir -p "$BACKUP_PATH"

echo "=== Backup PostgreSQL ==="
DB_CONTAINER=$(docker ps -qf "name=${STACK_NAME}_db" | head -1)
if [ -n "$DB_CONTAINER" ]; then
    docker exec "$DB_CONTAINER" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "${BACKUP_PATH}/db_${TIMESTAMP}.sql.gz"
    echo "Database backup: ${BACKUP_PATH}/db_${TIMESTAMP}.sql.gz"
else
    echo "ERROR: No running database container found."
    exit 1
fi

echo "=== Backup media ==="
APP_CONTAINER=$(docker ps -qf "name=${STACK_NAME}_app" | head -1)
if [ -n "$APP_CONTAINER" ]; then
    docker cp "${APP_CONTAINER}:/gaw-finance/media" "${BACKUP_PATH}/media"
    echo "Media backup: ${BACKUP_PATH}/media"
else
    echo "WARNING: No running app container found for media backup."
fi

echo "=== Rotating old backups (>${RETENTION_DAYS} days) ==="
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime +"$RETENTION_DAYS" -exec rm -rf {} \;

echo "=== Backup complete: $BACKUP_PATH ==="
