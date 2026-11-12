"""Fehlerklassen mit festen Exit-Codes."""

from __future__ import annotations


class BundesanzeigerError(Exception):
    """Basisfehler des Tools."""

    exit_code = 1


class ParseError(BundesanzeigerError):
    """Antwort der Quelle konnte nicht gelesen werden."""

    exit_code = 1


class UsageError(BundesanzeigerError):
    """Ungültige Eingabe oder mehrdeutige Auswahl."""

    exit_code = 2


class NetworkError(BundesanzeigerError):
    """Netzwerk- oder Quellenfehler."""

    exit_code = 3
