# bundesanzeiger-cli

Bekanntmachungen im Bundesanzeiger live durchsuchen und lesen – Firmen-
Bekanntmachungen nach Name finden, nach Bereich filtern und den Volltext im
Terminal lesen. Jahresabschlüsse bleiben ein Index; ihr Captcha wird nie
umgangen.

## Schnellstart

```bash
pipx install git+https://github.com/smlfg/bundesanzeiger-cli
bundesanzeiger suche "Deutsche Bahn AG"
bundesanzeiger lesen "Deutsche Bahn AG"
bundesanzeiger suche "Deutsche Bahn AG" --bereich finanzberichte
bundesanzeiger lesen "Deutsche Bahn AG" --bereich finanzberichte
bundesanzeiger neu "Deutsche Bahn AG"
bundesanzeiger suche "zzzqqqxnichtvorhanden"
```

Die Installation landet mit `pipx` im PATH. Ein Login ist nicht nötig; das Tool
liest ausschließlich.

## Befehle

```bash
bundesanzeiger suche FIRMA [--bereich BEREICH] [--seit JJJJ-MM-TT] [--limit N]
bundesanzeiger lesen FIRMA [NR] [--bereich BEREICH] [--erster]
bundesanzeiger neu FIRMA [--bereich BEREICH]
```

- `suche` zeigt Datum, Bereich, Firma mit Sitz und Titel der Treffer sowie die
  Gesamtzahl. `--limit` begrenzt die angezeigten Treffer (Default 3),
  `--seit` filtert ältere Bekanntmachungen clientseitig aus.
- `lesen` öffnet den Volltext des N-ten Treffers (Default 1). Bei mehreren
  möglichen Firmen fragt das Tool im Terminal nach einer Nummer; ohne TTY gibt
  es die Liste aus und endet mit Exit 2. Mit `--erster` liest es den ersten
  Treffer ohne Rückfrage.
- `neu` zeigt Bekanntmachungen seit dem letzten Aufruf. Der Stand liegt unter
  `$XDG_STATE_HOME/bundesanzeiger-cli/state.json` (Default
  `~/.local/state/bundesanzeiger-cli`, Rechte 0600).
- `--json` liefert maschinenlesbares JSON; ohne TTY ist JSON der Standard.

## Beispiele

```bash
bundesanzeiger suche "Deutsche Bahn AG" --seit 2025-01-01
bundesanzeiger suche "Deutsche Bahn AG" --bereich kapitalmarkt --limit 5
bundesanzeiger lesen "Deutsche Bahn AG" 2
bundesanzeiger suche "Deutsche Bahn AG" --json
```

Bereiche: `gesellschaft` (Gesellschaftsbekanntmachungen), `kapitalmarkt`,
`gericht` (Gerichtlicher Teil), `finanzberichte`
(Rechnungslegung/Finanzberichte), `amtlich` (Amtlicher Teil),
`verschiedenes` (Verschiedene Bekanntmachungen), `nichtamtlich`
(Nichtamtlicher Teil). Ohne `--bereich` wird in allen Bereichen gesucht.

## Jahresabschlüsse und Captcha

Der Bereich `finanzberichte` bleibt als Index durchsuchbar. Der Volltext eines
Jahresabschlusses ist auf bundesanzeiger.de durch ein Captcha geschützt. Das
Tool löst es nicht, sondern nennt die Such-URL zum Öffnen im Browser und endet
mit Exit 0; im JSON steht `captcha_erforderlich=true`.

## Konfiguration

| Variable | Bedeutung |
|---|---|
| `BUNDESANZEIGER_BASE_URL` | Basis-URL, Default `https://www.bundesanzeiger.de` (Fake-Server in Tests). |
| `BUNDESANZEIGER_HEUTE` | Datum `JJJJ-MM-TT` für deterministische `neu`-Tests. |
| `XDG_CACHE_HOME` | Basis für den HTTP-Cache, Default `~/.cache`. |
| `XDG_STATE_HOME` | Basis für den `neu`-Stand, Default `~/.local/state`. |

Der Cache liegt unter `$XDG_CACHE_HOME/bundesanzeiger-cli/` (TTL 10 Minuten).
Cookies der Bundesanzeiger-Session bleiben im Speicher und werden nicht
dauerhaft gespeichert.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| `0` | Erfolg, auch bei „keine Treffer“ und Captcha-Hinweis. |
| `1` | Allgemeiner Fehler. |
| `2` | Usage-Fehler (unbekanntes Argument, ungültiger Bereich, mehrdeutige Firma ohne TTY). |
| `3` | Netzwerk- oder Quellenfehler. |
| `4` | Login nötig (für dieses rein lesende Tool reserviert). |
| `130` | Abbruch durch Strg+C, ohne Traceback. |

## Hinweis

Dieses Tool ist **inoffiziell** und nicht mit der Bundesanzeiger
Verlagsgesellschaft mbH verbunden. Es nutzt die öffentliche Website, nicht eine
dokumentierte API. HTML-Struktur und Formularfelder können sich ändern. Alle
Live-Aufrufe sind lesend; es gibt keinen Login und keine schreibenden Aktionen.
Jahresabschluss-Dokumente werden nicht heruntergeladen und Captchas nicht
gelöst.

## Entwicklung

```bash
python3 tests/harness/ux_check.py . --spec-only
python3 tests/harness/ux_check.py .
python3 tests/harness/ux_session.py .
pytest -q tests/acceptance
```

Lizenz: MIT (Copyright smlfg).
