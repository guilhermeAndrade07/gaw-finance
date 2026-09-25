#!/bin/bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
BACKUP_DIR="${BACKUP_DIR:-${PROJECT_DIR}/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
STACK_NAME="gaw_finance"

parse_env() {
    local env_file="$1"
    if [ ! -f "$env_file" ]; then
        echo "ERROR: $env_file not found."
        exit 1
    fi
    set -a
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            ''|'#'*) continue ;;
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
DB_FILE="${BACKUP_PATH}/db_${TIMESTAMP}.sql.gz"
MEDIA_ARCHIVE="${BACKUP_PATH}/media_${TIMESTAMP}.tar.gz"
MANIFEST_FILE="${BACKUP_PATH}/MANIFEST.sha256"

mkdir -p "$BACKUP_PATH"
chmod 0700 "$BACKUP_DIR" "$BACKUP_PATH"

echo "=== Creating pre-release backup ==="
DB_CONTAINER="$(docker ps -qf "name=${STACK_NAME}_db" | head -n 1)"
if [ -z "$DB_CONTAINER" ]; then
    echo "ERROR: No running database container found."
    exit 1
fi

if ! docker exec "$DB_CONTAINER" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip -9 > "$DB_FILE"; then
    echo "ERROR: Database backup failed."
    rm -rf "$BACKUP_PATH"
    exit 1
fi

echo "Database backup: $DB_FILE"

APP_CONTAINER="$(docker ps -qf "name=${STACK_NAME}_app" | head -n 1)"
if [ -n "$APP_CONTAINER" ]; then
    if ! docker cp "${APP_CONTAINER}:/gaw-finance/media" "${BACKUP_PATH}/media"; then
        echo "WARNING: Media copy failed."
    else
        tar -C "$BACKUP_PATH" -czf "$MEDIA_ARCHIVE" "media_${TIMESTAMP}"
        rm -rf "${BACKUP_PATH}/media"
        echo "Media backup: $MEDIA_ARCHIVE"
    fi
else
    echo "WARNING: No running app container found for media backup."
fi

cd "$BACKUP_PATH"
find . -maxdepth 1 -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > "$MANIFEST_FILE"
cd - >/dev/null
chmod 0600 "$DB_FILE" "$MANIFEST_FILE"
if [ -f "$MEDIA_ARCHIVE" ]; then
    chmod 0600 "$MEDIA_ARCHIVE"
fi

if ! sha256sum -c "$MANIFEST_FILE" > /dev/null 2>&1; then
    echo "ERROR: Backup checksum validation failed."
    exit 1
fi

printf 'timestamp=%s\ndatabase=%s\nmanifest=%s\n' \
    "$TIMESTAMP" "$DB_FILE" "$MANIFEST_FILE" > "${BACKUP_PATH}/backup.info"
chmod 0600 "${BACKUP_PATH}/backup.info"

echo "=== Rotating backups older than ${RETENTION_DAYS} days ==="
find "$BACKUP_DIR" -maxdepth 1 -type d -mtime "+${RETENTION_DAYS}" -exec rm -rf {} \;

echo "Backup complete: $BACKUP_PATH"
echo "Checksum manifest: $MANIFEST_FILE"
