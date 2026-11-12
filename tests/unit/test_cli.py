from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def run_cli(*args: str, env: dict[str, str] | None = None):
    merged = dict(os.environ)
    merged["PYTHONPATH"] = str(REPO / "src")
    merged["NO_COLOR"] = "1"
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, "-m", "bundesanzeiger", *args],
        capture_output=True,
        text=True,
        env=merged,
        timeout=30,
        check=False,
    )


def test_version_and_help_exit_zero():
    version = run_cli("--version")
    assert version.returncode == 0
    assert "bundesanzeiger" in version.stdout

    help_result = run_cli("--help")
    assert help_result.returncode == 0
    assert "suche" in help_result.stdout

    for command in ("suche", "lesen", "neu"):
        sub = run_cli(command, "--help")
        assert sub.returncode == 0, sub.stderr
        assert "Traceback" not in sub.stderr


def test_unbekannter_bereich_ist_usage_fehler_ohne_traceback():
    result = run_cli("suche", "Deutsche Bahn AG", "--bereich", "quatsch")
    assert result.returncode == 2
    assert "Traceback" not in result.stdout + result.stderr
    data = json.loads(result.stdout.strip())
    assert "Nächster Schritt" in data["fehler"]


def test_usage_fehler_mit_json_ist_genau_ein_objekt():
    result = run_cli("suche", "x", "--limit", "0", "--json")
    assert result.returncode == 2
    data = json.loads(result.stdout.strip())
    assert data["exit_code"] == 2
    assert "fehler" in data


def test_ungueltiges_datum_ist_usage_fehler():
    result = run_cli("suche", "x", "--seit", "2026-13-99")
    assert result.returncode == 2
    assert "Traceback" not in result.stdout + result.stderr
    data = json.loads(result.stdout.strip())
    assert "JJJJ-MM-TT" in data["fehler"]


def test_unbekanntes_unterkommando_ohne_traceback():
    result = run_cli("gibtsnicht")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
