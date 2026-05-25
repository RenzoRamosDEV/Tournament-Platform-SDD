import math

from rest_framework.exceptions import Throttled
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    if isinstance(exc, Throttled):
        wait = exc.wait or 0
        response = exception_handler(exc, context).__class__(
            data={
                "error": "rate_limit_exceeded",
                "message": "Has superado el límite de solicitudes. Intenta de nuevo más tarde.",
                "retry_after_seconds": math.ceil(wait),
            },
            status=429,
        )
        if exc.wait is not None:
            response["Retry-After"] = "%d" % math.ceil(exc.wait)
        return response
    return exception_handler(exc, context)
