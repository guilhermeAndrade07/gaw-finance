import json
import logging
import sys

from .context import request_id_var


class JSONFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            'timestamp': self.formatTime(record, '%Y-%m-%dT%H:%M:%S%z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': request_id_var.get(''),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)

        for key, value in getattr(record, 'context', {}).items():
            if key not in payload:
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False, separators=(',', ':'))


def configure_console_handler():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    return handler
