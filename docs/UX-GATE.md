# UX-Gate-Bericht: bundesanzeiger

- Datum: 12.11.2026
- Repo: `smlfg/bundesanzeiger-cli`
- Tool: `bundesanzeiger`

## Ergebnis

| Gate | Befehl | Exit |
|---|---|---|
| UX-Check | `python3 tests/harness/ux_check.py . --report scratch/ux_check.md` | 0 |
| UX-Session | `python3 tests/harness/ux_session.py . --report scratch/ux_session.md` | 0 |

Beide Gates: **PASS** (kein FAIL).

## ux_check.py

- Modus: voll
- Ergebnis: PASS

| ID | Ergebnis | Befund |
|---|---|---|
| UX00 | PASS | 20 Request(s) am Fake-Server, keine Fremdverbindung |
| UX01 | PASS | docs/UX.md: 5 Sitzungen, 0 formsteps |
| UX02 | PASS | keine Credential-Env-Variablen gefunden |
| UX03 | PASS | --help, --version und 3 Unterkommandos mit Exit 0 |
| UX04 | PASS | 3 Unterkommandos ohne Pflicht-Option statt positional |
| UX05 | PASS | 5 Sitzungen ohne JSON/Traceback im TTY |
| UX06 | PASS | Schnellstart: 6 Tool-Befehle, Installation passt |
| UX07 | PASS | keine ux-formsteps, keine schreibende Aktion |
| UX08 | PASS | keine ux-formsteps, keine schreibende Aktion |
| UX09 | SKIP | keine schreibende Sitzung |

## ux_session.py

- Ergebnis: PASS

| Sitzung | Lauf | Ergebnis | Befund |
|---|---|---|---|
| Installation und erste Suche | 1 | PASS | OK |
| Volltext einer Bekanntmachung lesen | 1 | PASS | OK |
| Jahresabschluss: Index und Captcha-Hinweis | 1 | PASS | OK |
| Neue Bekanntmachungen seit dem letzten Aufruf | 1 | PASS | OK |
| Keine Treffer | 1 | PASS | OK |

## Unit-Tests

```text
$ scratch/venv/bin/pytest -q
52 passed
```
