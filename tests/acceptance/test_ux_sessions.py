"""Akzeptanztests für die Sitzungen aus docs/UX.md.

Jeder Test startet das Tool als Subprozess gegen den Fake-Server aus
tests/harness/fake_server.py. Die Tests sind absichtlich schon vor dem
Tool-Code vorhanden und dürfen bis zum Bau rot sein.
"""

from __future__ import annotations

import json
import os
import pty
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
HARNESS = REPO / "tests" / "harness"
sys.path.insert(0, str(HARNESS))

from fake_server import FakeServer  # noqa: E402
from ux_spec import parse  # noqa: E402

SPEC = parse(REPO / "docs" / "UX.md")
TOOL_MODULE = "bundesanzeiger"
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def _run_tool(
    args: list[str],
    server: FakeServer,
    home: Path,
    *,
    json_mode: bool = False,
    timeout: float = 30.0,
) -> tuple[int, str]:
    """Startet ``python -m bundesanzeiger`` mit einem Pseudo-TTY als stdout."""
    for relative in (".config", ".local/share", ".local/state", ".cache"):
        (home / relative).mkdir(parents=True, exist_ok=True)

    env = {
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local" / "share"),
        "XDG_STATE_HOME": str(home / ".local" / "state"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "BUNDESANZEIGER_BASE_URL": server.base_url,
        "BUNDESANZEIGER_HEUTE": "2026-11-12",
        "NO_COLOR": "1",
        "PYTHONPATH": os.pathsep.join([str(REPO / "src"), str(HARNESS)]),
        "PYTHONUNBUFFERED": "1",
        "ACCEPTANCE_SANDBOX": "1",
        "ACCEPTANCE_NET_LOG": str(home / "net.log"),
        "TERM": "xterm",
        "LANG": "C.UTF-8",
    }
    for key in ("PATH", "TMPDIR"):
        if key in os.environ:
            env[key] = os.environ[key]

    command = [sys.executable, "-m", TOOL_MODULE]
    if json_mode:
        command.append("--json")
    command.extend(args)

    master, slave = pty.openpty()
    try:
        completed = subprocess.run(
            command,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            cwd=str(REPO),
            env=env,
            timeout=timeout,
            check=False,
        )
    finally:
        os.close(slave)

    chunks: list[bytes] = []
    while True:
        try:
            data = os.read(master, 65536)
        except OSError:
            break
        if not data:
            break
        chunks.append(data)
    os.close(master)

    output = _strip_ansi(b"".join(chunks).decode("utf-8", "replace"))
    return completed.returncode, output


def _assert_no_foreign_requests(home: Path) -> None:
    log = home / "net.log"
    assert not log.exists() or not log.read_text(encoding="utf-8").strip(), (
        "Testserver-Sandbox: unerlaubter Netzwerkzugriff protokolliert"
    )


@pytest.fixture()
def spec_ok():
    assert not SPEC.errors, f"docs/UX.md ist ungültig: {SPEC.errors}"
    assert SPEC.meta.get("tool") == "bundesanzeiger"


def test_suche_deutsche_bahn(tmp_path, spec_ok):
    with FakeServer(SPEC, REPO) as server:
        code, output = _run_tool(["suche", "Deutsche Bahn AG"], server, tmp_path)

    assert code == 0, output
    assert "6200" in output
    assert "22.07.2026" in output
    assert "Gesellschafts" in output
    assert "Deutsche Bahn Aktiengesellschaft" in output
    assert "Traceback" not in output
    searches = [
        request
        for request in server.requests
        if request.path == "/pub/de/start" and "fulltext" in request.fields
    ]
    assert searches, "Suche wurde nicht an den Fake-Server gesendet"
    assert any(
        "Deutsche Bahn AG" in request.values.get("fulltext", [])
        for request in searches
    )
    _assert_no_foreign_requests(tmp_path)


def test_lesen_volltext(tmp_path, spec_ok):
    with FakeServer(SPEC, REPO) as server:
        code, output = _run_tool(["lesen", "Deutsche Bahn AG"], server, tmp_path)

    assert code == 0, output
    assert "Deutsche Bahn Aktiengesellschaft" in output
    assert "Hinweisbekanntmachung" in output
    assert "Beyond1435" in output
    assert "Traceback" not in output
    details = [
        request
        for request in server.requests
        if request.path == "/pub/de/suchergebnis"
    ]
    assert details, "Detailseite wurde nicht an den Fake-Server angefragt"
    _assert_no_foreign_requests(tmp_path)


def test_suche_finanzberichte(tmp_path, spec_ok):
    with FakeServer(SPEC, REPO) as server:
        code, output = _run_tool(
            ["suche", "Deutsche Bahn AG", "--bereich", "finanzberichte"],
            server,
            tmp_path,
        )

    assert code == 0, output
    assert "993" in output
    assert "Rechnungslegung" in output
    assert "Jahresabschluss" in output
    searches = [
        request
        for request in server.requests
        if request.path == "/pub/de/start" and "area_select" in request.fields
    ]
    assert searches, "Bereichsfilter wurde nicht gesendet"
    assert any("22" in request.values.get("area_select", []) for request in searches)
    _assert_no_foreign_requests(tmp_path)


def test_lesen_jahresabschluss_captcha(tmp_path, spec_ok):
    with FakeServer(SPEC, REPO) as server:
        code, output = _run_tool(
            ["lesen", "Deutsche Bahn AG", "--bereich", "finanzberichte"],
            server,
            tmp_path,
        )

    assert code == 0, output
    assert "Captcha" in output
    assert re.search(r"https?://\S+", output), output
    assert "Traceback" not in output
    _assert_no_foreign_requests(tmp_path)


def test_lesen_captcha_json(tmp_path, spec_ok):
    with FakeServer(SPEC, REPO) as server:
        code, output = _run_tool(
            ["lesen", "Deutsche Bahn AG", "--bereich", "finanzberichte"],
            server,
            tmp_path,
            json_mode=True,
        )

    assert code == 0, output
    data = json.loads(output.strip())
    assert data["captcha_erforderlich"] is True
    assert data["firma"] == "Deutsche Bahn Aktiengesellschaft"
    _assert_no_foreign_requests(tmp_path)


def test_neu_erster_aufruf(tmp_path, spec_ok):
    with FakeServer(SPEC, REPO) as server:
        code, output = _run_tool(["neu", "Deutsche Bahn AG"], server, tmp_path)

    assert code == 0, output
    assert "Erster Aufruf" in output
    assert "Ausgangsstand" in output
    assert "22.07.2026" in output
    assert "Traceback" not in output

    state_file = tmp_path / ".local" / "state" / "bundesanzeiger-cli" / "state.json"
    assert state_file.is_file(), "neu speichert keinen Zustand unter XDG_STATE_HOME"
    assert state_file.stat().st_mode & 0o777 == 0o600
    _assert_no_foreign_requests(tmp_path)


def test_suche_keine_treffer(tmp_path, spec_ok):
    with FakeServer(SPEC, REPO) as server:
        code, output = _run_tool(
            ["suche", "zzzqqqxnichtvorhanden"], server, tmp_path
        )

    assert code == 0, output
    assert "Keine Treffer" in output
    assert "Tipp" in output
    assert "Traceback" not in output
    _assert_no_foreign_requests(tmp_path)


def test_suche_json(tmp_path, spec_ok):
    with FakeServer(SPEC, REPO) as server:
        code, output = _run_tool(
            ["suche", "Deutsche Bahn AG"], server, tmp_path, json_mode=True
        )

    assert code == 0, output
    data = json.loads(output.strip())
    assert data["gesamt"] == 6200
    assert data["angezeigt"] == 3
    assert data["treffer"][0]["datum"] == "2026-07-22"
    assert data["treffer"][0]["firma"] == "Deutsche Bahn Aktiengesellschaft"
    _assert_no_foreign_requests(tmp_path)
