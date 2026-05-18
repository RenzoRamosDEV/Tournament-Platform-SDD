"""
Tests for scripts/setup_db.sh.
These tests verify script existence and version-check logic without
requiring a live PostgreSQL instance.
"""
import os
import subprocess
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).parent.parent / "scripts"
SETUP_SCRIPT = SCRIPTS_DIR / "setup_db.sh"


class SetupScriptExistsTest:
    def test_script_file_exists(self):
        assert SETUP_SCRIPT.exists(), f"setup_db.sh not found at {SETUP_SCRIPT}"

    def test_script_is_executable(self):
        assert os.access(SETUP_SCRIPT, os.X_OK), "setup_db.sh is not executable"


class SetupScriptVersionCheckTest:
    """
    Version-check logic: script must abort with exit code 1 when PostgreSQL < 15.
    We mock psql by prepending a fake psql to PATH.
    """

    def _run_with_fake_psql(self, fake_version_output: str, tmp_path: Path) -> subprocess.CompletedProcess:
        fake_psql = tmp_path / "psql"
        fake_psql.write_text(f'#!/bin/sh\necho "{fake_version_output}"\n')
        fake_psql.chmod(0o755)
        env = os.environ.copy()
        env["PATH"] = f"{tmp_path}:{env['PATH']}"
        # Provide required env vars so script doesn't fail on them
        env.setdefault("DB_USER", "testuser")
        env.setdefault("DB_PASSWORD", "testpass")
        env.setdefault("DB_NAME", "tournament_platform")
        return subprocess.run(
            [str(SETUP_SCRIPT), "--check-version-only"],
            env=env,
            capture_output=True,
            text=True,
        )

    def test_version_15_passes(self, tmp_path):
        result = self._run_with_fake_psql("psql (PostgreSQL) 15.3", tmp_path)
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}\nstderr: {result.stderr}"

    def test_version_16_passes(self, tmp_path):
        result = self._run_with_fake_psql("psql (PostgreSQL) 16.1", tmp_path)
        assert result.returncode == 0

    def test_version_14_fails(self, tmp_path):
        result = self._run_with_fake_psql("psql (PostgreSQL) 14.9", tmp_path)
        assert result.returncode == 1, f"Expected exit 1 for PG 14, got {result.returncode}"
        assert "15" in result.stderr or "15" in result.stdout

    def test_version_13_fails(self, tmp_path):
        result = self._run_with_fake_psql("psql (PostgreSQL) 13.0", tmp_path)
        assert result.returncode == 1
