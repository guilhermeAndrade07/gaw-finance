FROM python:3.13-slim@sha256:37134a49d21d2120e4c4d73bb76f8a4ab9aef31f096f7ec2ead48c2feead4332

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /gaw-finance

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod 0755 entrypoint.sh entrypoint-celery.sh entrypoint-release.sh scripts/load_runtime_env.sh scripts/deploy.sh scripts/backup.sh \
    && groupadd --gid 10001 gaw \
    && useradd --uid 10001 --gid gaw --create-home gaw \
    && mkdir -p /gaw-finance/media /gaw-finance/staticfiles \
    && chown gaw:gaw /gaw-finance/media /gaw-finance/staticfiles

USER gaw

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready/', timeout=5)"]

ENTRYPOINT ["./entrypoint.sh"]
