"""Unit-Tests dürfen nie echte Netze erreichen."""

from __future__ import annotations

import socket

import pytest


@pytest.fixture(autouse=True)
def block_non_loopback(monkeypatch):
    original = socket.socket.connect

    def guarded(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6) and isinstance(
            address, tuple
        ):
            host = str(address[0])
            if not host.startswith("127.") and host not in {"::1", "localhost"}:
                raise AssertionError(f"Netzwerkzugriff im Unit-Test blockiert: {host}")
        return original(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded)
