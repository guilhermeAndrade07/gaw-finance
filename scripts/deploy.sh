#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
STACK_FILE="${PROJECT_DIR}/stack.yml"
STACK_NAME="gaw_finance"
IMAGE="ghcr.io/guilhermeAndrade07/gaw-finance:latest"

SKIP_BUILD=false
if [ "${1:-}" = "--skip-build" ]; then
    SKIP_BUILD=true
fi

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

echo "=== Loading .env.prod ==="
parse_env "$ENV_FILE"

echo "=== Validating pre-conditions ==="

if ! docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null | grep -q 'active'; then
    echo "ERROR: Docker Swarm is not active. Run 'docker swarm init' first."
    exit 1
fi

for secret in gaw_secret_key gaw_db_password CLOUDFLARE_DNS_API_TOKEN; do
    if ! docker secret inspect "$secret" >/dev/null 2>&1; then
        echo "ERROR: Docker secret '$secret' not found."
        echo "  Create with: echo -n 'value' | docker secret create $secret -"
        exit 1
    fi
done

if ! docker network inspect traefik_public >/dev/null 2>&1; then
    echo "ERROR: Network 'traefik_public' not found."
    echo "  Create with: docker network create --driver overlay traefik_public"
    exit 1
fi

if [ "${DEBUG}" = "True" ] || [ "${DEBUG}" = "true" ]; then
    echo "ERROR: DEBUG must be False in production."
    exit 1
fi

if ! echo "${ALLOWED_HOSTS}" | grep -q 'localhost'; then
    echo "ERROR: localhost must be in ALLOWED_HOSTS for container healthcheck."
    exit 1
fi

for var in DOMAIN ACME_EMAIL POSTGRES_DB POSTGRES_USER GHCR_USER GHCR_TOKEN; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: $var is not set in .env.prod"
        exit 1
    fi
done

echo "All pre-conditions OK."

echo "=== Pulling code ==="
cd "$PROJECT_DIR"
git pull origin main

if [ "$SKIP_BUILD" = false ]; then
    echo "=== Building and pushing image ==="
    docker build -t "$IMAGE" .
    docker push "$IMAGE"
else
    echo "=== Skipping build (--skip-build) ==="
fi

echo "=== Logging in to GHCR ==="
echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USER}" --password-stdin

echo "=== Deploying stack ==="
docker stack deploy -c "$STACK_FILE" --with-registry-auth "$STACK_NAME"

echo "=== Forcing rollout ==="
docker service update --force gaw_finance_app 2>/dev/null || true
docker service update --force gaw_finance_traefik 2>/dev/null || true

echo "=== Deploy complete ==="
echo "Check status with: docker stack services $STACK_NAME"
