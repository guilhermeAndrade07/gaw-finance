#!/bin/bash
set -euo pipefail
umask 077

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
STACK_NAME="gaw_finance"
DRY_RUN=true

if [ "$#" -lt 1 ]; then
    echo "Usage: bash scripts/restore.sh <backup-path> [--apply]"
    echo "       By default this script only validates the backup."
    exit 1
fi

BACKUP_PATH="$1"
shift || true
if [ "${1:-}" = "--apply" ]; then
    DRY_RUN=false
fi

if [ ! -d "$BACKUP_PATH" ]; then
    echo "ERROR: Backup path does not exist: $BACKUP_PATH"
    exit 1
fi

parse_env() {
    local env_file="$1"
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

MANIFEST_FILE="${BACKUP_PATH}/MANIFEST.sha256"
DB_ARCHIVE="$(find "$BACKUP_PATH" -maxdepth 1 -type f -name 'db_*.sql.gz' | head -n 1)"
MEDIA_ARCHIVE="$(find "$BACKUP_PATH" -maxdepth 1 -type f -name 'media_*.tar.gz' | head -n 1)"

if [ ! -f "$MANIFEST_FILE" ]; then
    echo "ERROR: Checksum manifest not found."
    exit 1
fi

if [ -z "$DB_ARCHIVE" ]; then
    echo "ERROR: Database archive not found."
    exit 1
fi

cd "$BACKUP_PATH"
echo "=== Validating backup checksums ==="
sha256sum -c "$MANIFEST_FILE"
cd - > /dev/null

if [ "$DRY_RUN" = true ]; then
    echo "Backup validation complete."
    echo "To apply, run: bash scripts/restore.sh \"$BACKUP_PATH\" --apply"
    exit 0
fi

DB_CONTAINER="$(docker ps -qf "name=${STACK_NAME}_db" | head -n 1)"
if [ -z "$DB_CONTAINER" ]; then
    echo "ERROR: No running database container found."
    exit 1
fi

RESTORE_DB="${POSTGRES_DB}_restore_$(date +%Y%m%d_%H%M%S)"
echo "=== Restoring database to temporary database: $RESTORE_DB ==="

if docker exec "$DB_CONTAINER" psql -U "${POSTGRES_USER}" -tAc \
    "SELECT 1 FROM pg_database WHERE datname='${RESTORE_DB}'" | grep -q 1; then
    echo "ERROR: Temporary restore database already exists."
    exit 1
fi

docker exec "$DB_CONTAINER" createdb -U "${POSTGRES_USER}" "$RESTORE_DB"
if ! gzip -dc "$DB_ARCHIVE" | docker exec -i "$DB_CONTAINER" psql -U "${POSTGRES_USER}" -d "$RESTORE_DB" -v ON_ERROR_STOP=1; then
    echo "ERROR: Database restore failed. Dropping temporary database."
    docker exec "$DB_CONTAINER" dropdb -U "${POSTGRES_USER}" "$RESTORE_DB" || true
    exit 1
fi

TABLE_COUNT="$(docker exec "$DB_CONTAINER" psql -U "${POSTGRES_USER}" -d "$RESTORE_DB" -tAc \
    "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'")"

echo "Database restored successfully to $RESTORE_DB"
echo "Public tables restored: $TABLE_COUNT"

if [ -n "$MEDIA_ARCHIVE" ]; then
    RESTORED_MEDIA="${BACKUP_PATH}/restored_media"
    mkdir -p "$RESTORED_MEDIA"
    tar -xzf "$MEDIA_ARCHIVE" -C "$RESTORED_MEDIA" --strip-components=1
    echo "Media restored to staging path: $RESTORED_MEDIA"
    echo "Review the files before replacing the live media volume."
fi

echo "Restore complete."
echo "After validating the restored data, promote it manually to production."
