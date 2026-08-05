import json
import logging
import traceback
from collections.abc import Mapping
from rest_framework.views import exception_handler as drf_exception_handler


logger = logging.getLogger('core.errors')
SENSITIVE_KEYS = {
    'access',
    'authorization',
    'cookie',
    'csrfmiddlewaretoken',
    'password',
    'refresh',
    'secret',
    'token',
}


def sanitize(value):
    if isinstance(value, Mapping):
        return {
            key: '***'
            if str(key).lower() in SENSITIVE_KEYS
            else sanitize(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    return value


def request_details(request):
    resolver = getattr(request, 'resolver_match', None)
    user = getattr(request, 'user', None)
    try:
        body = request.data
    except Exception:
        try:
            body = json.loads(request.body) if request.body else None
        except Exception:
            body = None
    return {
        'method': request.method,
        'endpoint': request.path,
        'route': getattr(resolver, 'route', None),
        'view': getattr(resolver, 'view_name', None),
        'query': sanitize(dict(request.GET.lists())),
        'body': sanitize(body),
        'user_id': getattr(user, 'pk', None),
        'user_phone': getattr(user, 'phone', None),
        'ip': request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR'),
        'content_type': request.content_type,
        'user_agent': request.META.get('HTTP_USER_AGENT'),
        'authorization': '***' if request.META.get('HTTP_AUTHORIZATION') else None,
    }


def exception_details(exc):
    frames = traceback.extract_tb(exc.__traceback__)
    locations = [
        {
            'file': frame.filename,
            'function': frame.name,
            'line': frame.lineno,
            'code': frame.line,
        }
        for frame in frames
    ]
    return {
        'type': type(exc).__name__,
        'message': str(exc),
        'location': locations[-1] if locations else None,
        'traceback': locations,
    }


def write_error(exc, request, status_code=None, response_data=None):
    if getattr(request, '_error_logged', False):
        return
    request._error_logged = True
    payload = {
        'status_code': status_code,
        'request': request_details(request),
        'error': exception_details(exc),
        'response': sanitize(response_data),
    }
    logger.error(
        json.dumps(payload, ensure_ascii=False, default=str),
        exc_info=(type(exc), exc, exc.__traceback__),
    )


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    request = context.get('request')
    if request is not None:
        write_error(
            exc,
            request,
            status_code=getattr(response, 'status_code', 500),
            response_data=getattr(response, 'data', None),
        )
    return response


class ErrorLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        write_error(exception, request, status_code=500)
        return None
