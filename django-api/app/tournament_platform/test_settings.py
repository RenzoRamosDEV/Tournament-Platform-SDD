import os

os.environ.setdefault("SECRET_KEY", "_test_secret_key")
os.environ.setdefault("DB_USER", "_test_user")
os.environ.setdefault("DB_PASSWORD", "_test_password")

from tournament_platform.settings import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
