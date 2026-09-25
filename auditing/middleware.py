import uuid

from .context import request_id_var


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID') or uuid.uuid4().hex
        request.request_id = request_id
        token = request_id_var.set(request_id)

        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)

        response.headers.setdefault('X-Request-ID', request_id)
        return response
