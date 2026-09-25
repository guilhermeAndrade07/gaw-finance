#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

PYTHON="${PYTHON:-python}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
    if [ -x "venv/Scripts/python.exe" ]; then
        PYTHON="venv/Scripts/python.exe"
    elif [ -x "venv/bin/python" ]; then
        PYTHON="venv/bin/python"
    fi
fi

export DJANGO_ENV="${DJANGO_ENV:-test}"
export SECRET_KEY="${SECRET_KEY:-test-key}"
export DEBUG="${DEBUG:-False}"

echo "=== Python dependencies audit ==="
"$PYTHON" -m pip_audit -r requirements.txt --progress-spinner off

echo "=== Python lint ==="
"$PYTHON" -m flake8 .

echo "=== Django checks ==="
"$PYTHON" manage.py check
"$PYTHON" manage.py check --deploy

echo "=== Migrations ==="
"$PYTHON" manage.py makemigrations --check --dry-run

echo "=== Shell syntax ==="
bash -n entrypoint.sh entrypoint-celery.sh entrypoint-release.sh \
    scripts/load_runtime_env.sh scripts/deploy.sh \
    scripts/backup.sh scripts/restore.sh

echo "=== Test suite ==="
"$PYTHON" manage.py test

echo "=== Release gate passed ==="
