#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_DIR}/.env.prod"
STACK_FILE="${PROJECT_DIR}/stack.yml"
STACK_NAME="gaw_finance"
RELEASE_SERVICE="${STACK_NAME}_release"
GHCR_IMAGE="ghcr.io/guilhermeandrade07/gaw-finance"
IMAGE_TAG="${GAW_IMAGE_TAG:-}"

while [ "$#" -gt 0 ]; do
    case "$1" in
        --image-tag)
            if [ -z "${2:-}" ]; then
                echo "ERROR: --image-tag requires a value."
                exit 1
            fi
            IMAGE_TAG="$2"
            shift 2
            ;;
        *)
            echo "ERROR: Unknown argument: $1"
            exit 1
            ;;
    esac
done

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

wait_for_release() {
    local service="$1"
    local timeout="$2"
    local waited=0
    local state=""

    while [ "$waited" -lt "$timeout" ]; do
        state="$(docker service ps "$service" --format '{{.CurrentState}}' 2>/dev/null | head -n 1 || true)"

        if [[ "$state" == Complete* ]]; then
            return 0
        fi

        if [[ "$state" == Failed* || "$state" == Rejected* ]]; then
            return 1
        fi

        sleep 5
        waited=$((waited + 5))
    done

    return 1
}

wait_for_service() {
    local service="$1"
    local expected="$2"
    local timeout="$3"
    local waited=0
    local replicas=""

    while [ "$waited" -lt "$timeout" ]; do
        replicas="$(docker service ls --filter "name=${service}" --format '{{.Replicas}}' | head -n 1 || true)"

        if [ "$replicas" = "${expected}/${expected}" ]; then
            return 0
        fi

        sleep 5
        waited=$((waited + 5))
    done

    return 1
}

rollback_app() {
    local previous_image="${1:-}"

    echo "ERROR: Deployment validation failed. Rolling back application."

    if [ -n "$previous_image" ]; then
        docker service update --detach --image "$previous_image" "${STACK_NAME}_app"
    else
        docker service rollback --detach "${STACK_NAME}_app"
    fi
}

echo "=== Loading .env.prod ==="
parse_env "$ENV_FILE"

echo "=== Validating deployment preconditions ==="

if [ -z "$IMAGE_TAG" ]; then
    echo "ERROR: GAW_IMAGE_TAG is required. Example: export GAW_IMAGE_TAG=<commit-sha>"
    exit 1
fi

if [ "$IMAGE_TAG" = "latest" ] || [ "$IMAGE_TAG" = "main" ]; then
    echo "ERROR: Mutable image tags are not allowed."
    exit 1
fi

if ! docker info --format '{{.Swarm.LocalNodeState}}' 2>/dev/null | grep -q 'active'; then
    echo "ERROR: Docker Swarm is not active."
    exit 1
fi

for secret in gaw_secret_key gaw_db_password gaw_rabbitmq_password CLOUDFLARE_DNS_API_TOKEN; do
    if ! docker secret inspect "$secret" >/dev/null 2>&1; then
        echo "ERROR: Docker secret '$secret' not found."
        exit 1
    fi
done

if ! docker network inspect traefik_public >/dev/null 2>&1; then
    echo "ERROR: Network 'traefik_public' not found."
    exit 1
fi

if ! docker network inspect gaw_finance_internal >/dev/null 2>&1; then
    docker network create --driver overlay --internal gaw_finance_internal
fi

if ! docker network inspect gaw_finance_egress >/dev/null 2>&1; then
    docker network create --driver overlay gaw_finance_egress
fi

if [ "${DJANGO_ENV:-}" != "prd" ]; then
    echo "ERROR: DJANGO_ENV must be prd in production."
    exit 1
fi

if [ "${DEBUG:-}" = "True" ] || [ "${DEBUG:-}" = "true" ]; then
    echo "ERROR: DEBUG must be False in production."
    exit 1
fi

if [ -z "${ALLOWED_HOSTS:-}" ] || echo "${ALLOWED_HOSTS}" | grep -q '\*'; then
    echo "ERROR: ALLOWED_HOSTS must be defined without wildcards."
    exit 1
fi

if [ -z "${CSRF_TRUSTED_ORIGINS:-}" ] || echo "${CSRF_TRUSTED_ORIGINS}" | grep -q '\*'; then
    echo "ERROR: CSRF_TRUSTED_ORIGINS must contain exact origins without wildcards."
    exit 1
fi

if [ -z "${DOMAIN:-}" ] || [ "${DOMAIN}" = "yourdomain.com" ]; then
    echo "ERROR: DOMAIN must be configured with the real production domain."
    exit 1
fi

for var in DOMAIN ACME_EMAIL POSTGRES_DB POSTGRES_USER GHCR_USER GHCR_TOKEN; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: $var is not set in .env.prod"
        exit 1
    fi
done

APP_IMAGE="${GHCR_IMAGE}:${IMAGE_TAG}"
export APP_IMAGE

echo "All preconditions OK."
echo "Application image: ${APP_IMAGE}"

echo "=== Logging in to GHCR ==="
echo "${GHCR_TOKEN}" | docker login ghcr.io -u "${GHCR_USER}" --password-stdin

echo "=== Pulling immutable application image ==="
docker pull "$APP_IMAGE"

PREVIOUS_IMAGE="$(docker service inspect --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' "${STACK_NAME}_app" 2>/dev/null || true)"

echo "=== Creating pre-release backup ==="
bash "${SCRIPT_DIR}/backup.sh"

echo "=== Preparing volume ownership ==="
docker run --rm --user 0:0 \
    -v gaw_finance_static_data:/gaw-finance/staticfiles \
    -v gaw_finance_media_data:/gaw-finance/media \
    "$APP_IMAGE" \
    sh -c "chown -R gaw:gaw /gaw-finance/staticfiles /gaw-finance/media"

echo "=== Running one-off release job ==="
docker service rm "$RELEASE_SERVICE" >/dev/null 2>&1 || true

docker service create \
    --name "$RELEASE_SERVICE" \
    --restart-condition none \
    --network gaw_finance_internal \
    --secret gaw_secret_key \
    --secret gaw_db_password \
    --secret gaw_rabbitmq_password \
    --env DJANGO_ENV="${DJANGO_ENV}" \
    --env DEBUG="${DEBUG}" \
    --env ALLOWED_HOSTS="${ALLOWED_HOSTS}" \
    --env CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS}" \
    --env POSTGRES_DB="${POSTGRES_DB}" \
    --env POSTGRES_USER="${POSTGRES_USER}" \
    --env POSTGRES_HOST=db \
    --env POSTGRES_PORT=5432 \
    --env RABBITMQ_USER=gaw_app \
    --env RABBITMQ_HOST=rabbitmq \
    --env CELERY_RESULT_BACKEND=redis://redis:6379/1 \
    --env REDIS_URL=redis://redis:6379/0 \
    --mount type=volume,source=gaw_finance_static_data,target=/gaw-finance/staticfiles \
    --with-registry-auth \
    --entrypoint ./entrypoint-release.sh \
    "$APP_IMAGE"

if ! wait_for_release "$RELEASE_SERVICE" 300; then
    docker service logs --tail 200 "$RELEASE_SERVICE" || true
    docker service rm "$RELEASE_SERVICE" >/dev/null 2>&1 || true
    echo "ERROR: Release job failed."
    exit 1
fi

docker service logs --tail 100 "$RELEASE_SERVICE"
docker service rm "$RELEASE_SERVICE" >/dev/null 2>&1 || true

echo "=== Deploying application stack ==="
docker stack deploy -c "$STACK_FILE" --with-registry-auth "$STACK_NAME"

echo "=== Waiting for service convergence ==="
if ! wait_for_service "${STACK_NAME}_app" 2 300; then
    rollback_app "$PREVIOUS_IMAGE"
    exit 1
fi

if ! wait_for_service "${STACK_NAME}_celery_worker" 1 180; then
    rollback_app "$PREVIOUS_IMAGE"
    exit 1
fi

if ! wait_for_service "${STACK_NAME}_celery_beat" 1 120; then
    rollback_app "$PREVIOUS_IMAGE"
    exit 1
fi

echo "=== Running smoke tests ==="
if ! curl -fsS --max-time 15 "https://${DOMAIN}/ready/" >/dev/null; then
    rollback_app "$PREVIOUS_IMAGE"
    echo "ERROR: Readiness smoke test failed."
    exit 1
fi

if ! curl -fsS --max-time 15 "https://${DOMAIN}/login/" >/dev/null; then
    rollback_app "$PREVIOUS_IMAGE"
    echo "ERROR: Login smoke test failed."
    exit 1
fi

echo "=== Deploy complete ==="
echo "Image: ${APP_IMAGE}"
echo "Check status with: docker stack services $STACK_NAME"
