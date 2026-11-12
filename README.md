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
```

Die Installation landet mit `pipx` im PATH. Ein Login ist nicht nötig.

## Befehle

```bash
bundesanzeiger suche FIRMA [--bereich gesellschaft|kapitalmarkt|gericht|finanzberichte|amtlich|verschiedenes|nichtamtlich] [--seit JJJJ-MM-TT] [--limit N]
bundesanzeiger lesen FIRMA [NR] [--bereich ...]
bundesanzeiger neu FIRMA [--bereich ...]
```

- `suche` zeigt Datum, Bereich, Firma und Titel der Treffer.
- `lesen` öffnet den Volltext des N-ten Treffers (Standard: 1). Bei mehreren
  möglichen Firmen fragt das Tool im Terminal nach einer Nummer; ohne TTY gibt
  es die Liste aus und endet mit Exit 2.
- `neu` zeigt Bekanntmachungen seit dem letzten Aufruf. Der Stand liegt unter
  `~/.local/state/bundesanzeiger-cli` (Rechte 0600).
- `--json` liefert maschinenlesbares JSON; ohne TTY ist JSON der Standard.

## Bereiche

`gesellschaft` (Gesellschaftsbekanntmachungen), `kapitalmarkt`,
`gericht` (Gerichtlicher Teil), `finanzberichte`
(Rechnungslegung/Finanzberichte), `amtlich` (Amtlicher Teil),
`verschiedenes` (Verschiedene Bekanntmachungen), `nichtamtlich`
(Nichtamtlicher Teil).

## Jahresabschlüsse und Captcha

Der Bereich `finanzberichte` bleibt als Index durchsuchbar. Der Volltext eines
Jahresabschlusses ist auf bundesanzeiger.de durch ein Captcha geschützt. Das
Tool löst es nicht, sondern nennt die Such-URL zum Öffnen im Browser und endet
mit Exit 0; im JSON steht `captcha_erforderlich=true`.

## Technik

- Python >= 3.10, `argparse` + `httpx`/`requests`, `beautifulsoup4` bei Bedarf.
- Höflich: wenige GET-Requests pro Aufruf, User-Agent mit Repo-URL, Cache für
  10 Minuten unter `~/.cache/bundesanzeiger-cli`.
- Basis-URL für Tests über `BUNDESANZEIGER_BASE_URL` überschreibbar.
- Rein lesend, keine schreibenden Web-Aktionen und kein Login.

## Entwicklung

```bash
python3 tests/harness/ux_check.py . --spec-only
python3 tests/harness/ux_check.py .
python3 tests/harness/ux_session.py .
```

Lizenz: MIT (Copyright smlfg).
