"""
Tests for env-config capability.
These tests reload settings with patched os.environ to verify decouple behavior.
"""
import importlib
import os
from pathlib import Path

import pytest
from decouple import UndefinedValueError


class _SettingsSnapshot:
    """Immutable snapshot of settings attributes captured before env is restored."""
    def __init__(self, module):
        self.__dict__.update({k: v for k, v in vars(module).items() if not k.startswith("__")})


def _reload_settings(env_overrides: dict):
    """Temporarily patch os.environ, reload settings, capture a snapshot, then restore."""
    original = {k: os.environ.get(k) for k in env_overrides}
    for k, v in env_overrides.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    try:
        import config.settings.base as s
        importlib.reload(s)
        return _SettingsSnapshot(s)
    finally:
        for k, orig_v in original.items():
            if orig_v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = orig_v
        importlib.reload(importlib.import_module("config.settings.base"))


class EnvConfigRequiredVarsTest:
    """DB_USER, DB_PASSWORD, and SECRET_KEY are required — absence must raise UndefinedValueError."""

    def test_db_user_missing_raises_undefined_value_error(self):
        with pytest.raises(UndefinedValueError):
            _reload_settings({"DB_USER": None, "DB_PASSWORD": "pw"})

    def test_db_password_missing_raises_undefined_value_error(self):
        with pytest.raises(UndefinedValueError):
            _reload_settings({"DB_USER": "user", "DB_PASSWORD": None})

    def test_secret_key_missing_raises_undefined_value_error(self):
        with pytest.raises(UndefinedValueError):
            _reload_settings({"SECRET_KEY": None, "DB_USER": "user", "DB_PASSWORD": "pw"})


class EnvConfigOptionalVarsTest:
    """Optional vars default to expected values when absent."""

    def test_optional_vars_use_defaults(self):
        s = _reload_settings({
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "DB_NAME": None,
            "DB_HOST": None,
            "DB_PORT": None,
        })
        db = s.DATABASES["default"]
        assert db["NAME"] == "tournament_platform"
        assert db["HOST"] == "localhost"
        assert db["PORT"] == 5432

    def test_cors_origins_default(self):
        s = _reload_settings({
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "CORS_ALLOWED_ORIGINS": None,
        })
        assert "http://localhost:3000" in s.CORS_ALLOWED_ORIGINS
        assert "http://localhost:5073" in s.CORS_ALLOWED_ORIGINS

    def test_page_size_default(self):
        s = _reload_settings({
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "PAGE_SIZE": None,
        })
        assert s.REST_FRAMEWORK["PAGE_SIZE"] == 20

    def test_page_size_override(self):
        s = _reload_settings({
            "DB_USER": "testuser",
            "DB_PASSWORD": "testpass",
            "PAGE_SIZE": "50",
        })
        assert s.REST_FRAMEWORK["PAGE_SIZE"] == 50


class EnvExampleFileTest:
    """`.env.example` must contain exactly all required keys."""

    ENV_EXAMPLE = Path(__file__).parent.parent / ".env.example"
    REQUIRED_KEYS = {
        "SECRET_KEY", "DEBUG",
        "DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT",
        "CORS_ALLOWED_ORIGINS", "PAGE_SIZE",
    }

    def test_env_example_exists(self):
        assert self.ENV_EXAMPLE.exists(), ".env.example not found at project root"

    def test_env_example_contains_all_required_keys(self):
        content = self.ENV_EXAMPLE.read_text()
        defined_keys = {
            line.split("=")[0].strip()
            for line in content.splitlines()
            if line.strip() and not line.startswith("#") and "=" in line
        }
        assert self.REQUIRED_KEYS == defined_keys, (
            f"Missing keys: {self.REQUIRED_KEYS - defined_keys}, "
            f"Extra keys: {defined_keys - self.REQUIRED_KEYS}"
        )


class PgSettingsTest:
    """config.pg_settings must import cleanly and not override DATABASES."""

    def test_pg_settings_imports_without_error(self):
        os.environ.setdefault("DB_USER", "testuser")
        os.environ.setdefault("DB_PASSWORD", "testpass")
        import config.pg_settings as pg  # noqa: F401
        assert pg is not None

    def test_pg_settings_does_not_override_databases(self):
        os.environ.setdefault("DB_USER", "testuser")
        os.environ.setdefault("DB_PASSWORD", "testpass")
        import config.pg_settings as pg
        import config.settings.base as s
        assert not hasattr(pg, "DATABASES") or pg.DATABASES is s.DATABASES
