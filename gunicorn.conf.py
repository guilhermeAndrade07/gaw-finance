import multiprocessing
import os

bind = '0.0.0.0:8000'
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 120
graceful_timeout = 30
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')
accesslog = '-'
errorlog = '-'
