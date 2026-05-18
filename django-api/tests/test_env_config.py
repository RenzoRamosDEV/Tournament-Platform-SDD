"""
Tests for env-config capability.
These tests import settings directly (not via DJANGO_SETTINGS_MODULE)
so they can manipulate os.environ before the module loads.
"""
import importlib
import os
from pathlib import Path

import pytest


def _reload_settings(env_overrides: dict):
    """Temporarily patch os.environ and reload settings, then restore."""
    original = {k: os.environ.get(k) for k in env_overrides}
    for k, v in env_overrides.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    try:
        import tournament_platform.settings as s
        importlib.reload(s)
        return s
    finally:
        for k, orig_v in original.items():
            if orig_v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = orig_v
        importlib.reload(importlib.import_module("tournament_platform.settings"))


class EnvConfigRequiredVarsTest:
    """DB_USER and DB_PASSWORD are required — absence must raise KeyError."""

    def test_db_user_missing_raises_key_error(self):
        with pytest.raises(KeyError, match="DB_USER"):
            _reload_settings({"DB_USER": None, "DB_PASSWORD": "pw"})

    def test_db_password_missing_raises_key_error(self):
        with pytest.raises(KeyError, match="DB_PASSWORD"):
            _reload_settings({"DB_USER": "user", "DB_PASSWORD": None})


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
        assert db["PORT"] == "5432"


class EnvExampleFileTest:
    """`.env.example` must contain exactly the five required keys."""

    ENV_EXAMPLE = Path(__file__).parent.parent / ".env.example"
    REQUIRED_KEYS = {"DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT"}

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
    """pg_settings must import cleanly and not override DATABASES."""

    def test_pg_settings_imports_without_error(self):
        os.environ.setdefault("DB_USER", "testuser")
        os.environ.setdefault("DB_PASSWORD", "testpass")
        import tournament_platform.pg_settings as pg  # noqa: F401
        assert pg is not None

    def test_pg_settings_does_not_override_databases(self):
        os.environ.setdefault("DB_USER", "testuser")
        os.environ.setdefault("DB_PASSWORD", "testpass")
        import tournament_platform.pg_settings as pg
        import tournament_platform.settings as s
        # pg_settings must not define its own DATABASES
        assert not hasattr(pg, "DATABASES") or pg.DATABASES is s.DATABASES
