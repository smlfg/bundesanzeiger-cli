"""Lokaler Stand für ``neu`` (Datei 0600 unter XDG_STATE_HOME)."""

from __future__ import annotations

import json
import os
from pathlib import Path

STATE_VERSION = 1
MAX_KEYS = 1000


def state_path() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return Path(base) / "bundesanzeiger-cli" / "state.json"


def load_state() -> dict:
    path = state_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": STATE_VERSION, "eintraege": {}}
    if not isinstance(data, dict):
        return {"version": STATE_VERSION, "eintraege": {}}
    entries = data.get("eintraege")
    if not isinstance(entries, dict):
        data["eintraege"] = {}
    data["version"] = STATE_VERSION
    return data


def save_state(state: dict) -> None:
    path = state_path()
    directory = path.parent
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(directory, 0o700)
    payload = json.dumps(state, ensure_ascii=False, indent=2).encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
    os.chmod(path, 0o600)
