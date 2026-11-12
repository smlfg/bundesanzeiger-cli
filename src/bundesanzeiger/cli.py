"""Kommandozeile für bundesanzeiger."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

from . import __version__
from .client import AREA_CODES, AREA_NAMES, BundesanzeigerClient
from .errors import BundesanzeigerError, UsageError
from .parser import Entry, german_date


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(
            f"{message}\nNächster Schritt: `bundesanzeiger --help` zeigt die "
            "gültigen Befehle und Optionen."
        )


def _add_json_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        action="store_true",
        default=argparse.SUPPRESS,
        help="JSON auf stdout ausgeben (bei Fehlern ein JSON-Objekt).",
    )


def _add_area_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--bereich",
        metavar="BEREICH",
        choices=list(AREA_CODES),
        help="Bereichsfilter: " + ", ".join(AREA_CODES) + ".",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="bundesanzeiger",
        description=(
            "Bekanntmachungen im Bundesanzeiger durchsuchen und lesen. "
            "Rein lesend, ohne Login; Jahresabschlüsse bleiben ein Index."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON auf stdout ausgeben (bei Fehlern ein JSON-Objekt).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="kommando", metavar="UNTERKOMMANDO")
    subparsers.required = True

    suche = subparsers.add_parser(
        "suche",
        help="Bekanntmachungen nach Firmenname oder Suchbegriff suchen.",
        description="Bekanntmachungen nach Firmenname oder Suchbegriff suchen.",
    )
    suche.add_argument("suchbegriff", metavar="FIRMA", help="Suchbegriff.")
    _add_area_option(suche)
    suche.add_argument(
        "--seit",
        metavar="JJJJ-MM-TT",
        help="Nur Treffer mit Datum ab diesem Tag (clientseitig gefiltert).",
    )
    suche.add_argument(
        "--limit",
        metavar="N",
        type=int,
        default=3,
        help="Anzahl angezeigter Treffer, 1..50 (Default 3).",
    )
    _add_json_option(suche)
    suche.set_defaults(handler=_cmd_suche)

    return parser


def _json_mode(args: argparse.Namespace, argv: list[str]) -> bool:
    if getattr(args, "json", False) or "--json" in argv:
        return True
    return not sys.stdout.isatty()


def _validate_date(value: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise UsageError(
            "Ungültiges Datum für --seit – erwartet JJJJ-MM-TT."
        )
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise UsageError(
            "Ungültiges Datum für --seit – erwartet JJJJ-MM-TT."
        ) from exc
    return value


def _validate_limit(value: int) -> int:
    if value < 1 or value > 50:
        raise UsageError("--limit muss zwischen 1 und 50 liegen.")
    return value


def _print_error(message: str, exit_code: int, json_output: bool) -> None:
    if json_output:
        print(
            json.dumps(
                {"fehler": message, "exit_code": exit_code},
                ensure_ascii=False,
            )
        )
    else:
        print(message, file=sys.stderr)


def _entry_line(number: int, entry: Entry) -> str:
    location = entry.firma
    if entry.sitz:
        location += f" ({entry.sitz})"
    return (
        f"{number}) {german_date(entry.datum)} · {entry.bereich} · {location}"
        f"\n   {entry.titel}"
    )


def _print_search(term: str, bereich: str | None, page, shown: list[Entry]) -> None:
    label = f"„{term}“"
    if bereich:
        label += f" ({AREA_NAMES[bereich]})"
    print(f"Suche {label}: {page.gesamt} Treffer, {len(shown)} angezeigt")
    for index, entry in enumerate(shown, start=1):
        print(_entry_line(index, entry))


def _cmd_suche(args: argparse.Namespace, argv: list[str]) -> int:
    limit = _validate_limit(args.limit)
    since = _validate_date(args.seit) if args.seit else None

    client = BundesanzeigerClient()
    result = client.search(args.suchbegriff, args.bereich, use_cache=True)
    entries = result.page.treffer
    if since:
        entries = [
            entry for entry in entries if not entry.datum or entry.datum >= since
        ]
    shown = entries[:limit]

    if not shown:
        if result.page.gesamt == 0:
            message = (
                f"Keine Treffer für „{args.suchbegriff}“.\n"
                "Tipp: Schreibweise prüfen oder einen anderen Bereich wählen."
            )
        else:
            message = (
                f"Keine Treffer für „{args.suchbegriff}“"
                + (f" seit {since}" if since else "")
                + ".\nTipp: Zeitraum verkleinern oder anderen Bereich wählen."
            )
        if _json_mode(args, argv):
            print(
                json.dumps(
                    {
                        "suchbegriff": args.suchbegriff,
                        "bereich": args.bereich,
                        "seit": since,
                        "gesamt": result.page.gesamt,
                        "angezeigt": 0,
                        "treffer": [],
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(message)
        return 0

    if _json_mode(args, argv):
        payload = {
            "suchbegriff": args.suchbegriff,
            "bereich": args.bereich,
            "seit": since,
            "gesamt": result.page.gesamt,
            "angezeigt": len(shown),
            "treffer": [
                dict(entry.as_json(), nummer=index)
                for index, entry in enumerate(shown, start=1)
            ],
        }
        print(json.dumps(payload, ensure_ascii=False))
    else:
        _print_search(args.suchbegriff, args.bereich, result.page, shown)
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    json_output = "--json" in arguments or not sys.stdout.isatty()
    try:
        parser = build_parser()
        args = parser.parse_args(arguments)
        return int(args.handler(args, arguments))
    except BundesanzeigerError as exc:
        _print_error(str(exc), exc.exit_code, json_output)
        return exc.exit_code
    except KeyboardInterrupt:
        print("Abgebrochen.", file=sys.stderr)
        return 130
    except BrokenPipeError:
        return 130
    except EOFError:
        _print_error("Keine Eingabe erhalten – erneut starten.", 2, json_output)
        return 2
    except Exception as exc:  # noqa: BLE001 - nie Tracebacks im Terminal
        _print_error(
            f"Unerwarteter Fehler ({exc.__class__.__name__}) – "
            "erneut versuchen oder `bundesanzeiger --help` lesen.",
            1,
            json_output,
        )
        return 1
