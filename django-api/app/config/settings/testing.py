import os

os.environ.setdefault("SECRET_KEY", "_test_secret_key")
os.environ.setdefault("DB_USER", "_test_user")
os.environ.setdefault("DB_PASSWORD", "_test_password")

from .base import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Keep throttle classes active so APIView.throttle_classes is set at import time.
# Use a very high rate so normal tests are never throttled.
# Throttle-specific tests override DEFAULT_THROTTLE_RATES via @override_settings.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        "anon": "10000/min",
        "user": "10000/min",
    },
}
