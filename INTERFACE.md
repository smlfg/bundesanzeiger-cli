# Interface: bundesanzeiger

Kommandozeilen-Werkzeug `bundesanzeiger` (Console-Script, Python >= 3.10).
Rein lesend, kein Login. Die Basis-URL ist über `BUNDESANZEIGER_BASE_URL`
überschreibbar (Fake-Server in Tests).

## Aufruf

```text
bundesanzeiger [--json] [--version] [--help] <unterkommando> ...
```

Globale Optionen:

| Option | Bedeutung |
|---|---|
| `--json` | Genau ein JSON-Objekt auf stdout; Prompts und Fehlertexte auf stderr. |
| `--version` | Version ausgeben, Exit 0. |
| `--help` | Hilfe ausgeben, Exit 0. Auch `<unterkommando> --help` endet mit Exit 0. |

Ohne `--json` gilt: Ist stdout ein Terminal, wird lesbarer Text ausgegeben; ist
stdout kein Terminal (Pipe/Agent), wird JSON ausgegeben. Mit `--json` immer
JSON.

## Unterkommandos

### `suche FIRMA`

Sucht Bekanntmachungen nach Firmenname oder Suchbegriff und zeigt die Treffer.

```text
bundesanzeiger suche FIRMA [--bereich BEREICH] [--seit JJJJ-MM-TT] [--limit N]
```

| Argument/Option | Pflicht | Bedeutung |
|---|---|---|
| `FIRMA` | ja | Suchbegriff, positional, z. B. `"Deutsche Bahn AG"`. |
| `--bereich BEREICH` | nein | Bereichsfilter, siehe Bereiche. Ohne Angabe alle Bereiche. |
| `--seit JJJJ-MM-TT` | nein | Nur Treffer mit Datum >= diesem Tag (clientseitig gefiltert). |
| `--limit N` | nein | Anzahl angezeigter Treffer, Default `3`, gültig `1..50`. |

Textausgabe (Beispiel):

```text
Suche „Deutsche Bahn AG“: 6200 Treffer, 3 angezeigt
1) 22.07.2026 · Gesellschaftsbekanntmachungen · Deutsche Bahn Aktiengesellschaft (Berlin)
   Hinweisbekanntmachung (gemäß § 62 Abs. 4 Satz 3 i.V.m. Abs. 3 UmwG)
```

Mit `--bereich` steht der Bereichsname in der Kopfzeile:
`Suche „…“ (Rechnungslegung/Finanzberichte): 993 Treffer, 3 angezeigt`.

Keine Treffer:

```text
Keine Treffer für „zzzqqqxnichtvorhanden“.
Tipp: Schreibweise prüfen oder einen anderen Bereich wählen.
```

Exit 0.

JSON-Schema `suche`:

```json
{
  "suchbegriff": "Deutsche Bahn AG",
  "bereich": "gesellschaft",
  "seit": null,
  "gesamt": 6200,
  "angezeigt": 3,
  "treffer": [
    {
      "nummer": 1,
      "datum": "2026-07-22",
      "bereich": "Gesellschaftsbekanntmachungen",
      "firma": "Deutsche Bahn Aktiengesellschaft",
      "sitz": "Berlin",
      "titel": "Hinweisbekanntmachung (gemäß § 62 Abs. 4 Satz 3 i.V.m. Abs. 3 UmwG)",
      "url": "https://www.bundesanzeiger.de/pub/de/suchergebnis?1"
    }
  ]
}
```

### `lesen FIRMA [NR]`

Öffnet den Volltext des N-ten Treffers (Default `1`). Der Volltext wird über
eine frische Suche in derselben Session geholt.

```text
bundesanzeiger lesen FIRMA [NR] [--bereich BEREICH] [--erster]
```

| Argument/Option | Pflicht | Bedeutung |
|---|---|---|
| `FIRMA` | ja | Suchbegriff, positional. |
| `NR` | nein | Treffernummer, Default `1`, gültig `1..--limit`. |
| `--bereich BEREICH` | nein | Bereichsfilter wie bei `suche`. |
| `--erster` | nein | Bei mehreren möglichen Firmen ohne TTY automatisch den ersten Treffer lesen (Agenten). |

Mehrere unterschiedliche Firmen in der Trefferliste:

- Im TTY: nummerierte Auswahl der Firmen; danach wird der gewählte Treffer
  gelesen.
- Ohne TTY und ohne `--erster`: Liste der Firmen auf stdout/stderr und **Exit 2**.
- Mit `--erster`: der erste Treffer wird gelesen.

Textausgabe (Beispiel):

```text
Deutsche Bahn Aktiengesellschaft (Berlin)
Hinweisbekanntmachung (gemäß § 62 Abs. 4 Satz 3 i.V.m. Abs. 3 UmwG) · 22.07.2026 · Gesellschaftsbekanntmachungen
Die Deutsche Bahn Aktiengesellschaft mit Sitz in Berlin, eingetragen im Handelsregister …
```

Captcha (Bereich `finanzberichte`):

```text
Jahresabschluss ist auf bundesanzeiger.de durch ein Captcha geschützt – im Browser öffnen:
https://www.bundesanzeiger.de/pub/de/suchen2?…
```

Exit 0; im JSON `captcha_erforderlich: true`.

JSON-Schema `lesen`:

```json
{
  "suchbegriff": "Deutsche Bahn AG",
  "nummer": 1,
  "datum": "2026-07-22",
  "bereich": "Gesellschaftsbekanntmachungen",
  "firma": "Deutsche Bahn Aktiengesellschaft",
  "sitz": "Berlin",
  "titel": "Hinweisbekanntmachung …",
  "url": "https://www.bundesanzeiger.de/pub/de/suchergebnis?1",
  "captcha_erforderlich": false,
  "text": "Die Deutsche Bahn Aktiengesellschaft …"
}
```

Bei Captcha enthält `text` die Captcha-Meldung, `captcha_erforderlich` ist
`true` und `url` verweist auf die Such-/Browser-URL.

### `neu FIRMA`

Zeigt Bekanntmachungen, die seit dem letzten erfolgreichen Aufruf für denselben
Suchbegriff und Bereich neu sind.

```text
bundesanzeiger neu FIRMA [--bereich BEREICH]
```

- Erster Aufruf: Ausgangsstand wird gespeichert; Text
  `Erster Aufruf – Ausgangsstand gespeichert.` plus neueste Bekanntmachung.
- Folgende Aufrufe: nur neuere Bekanntmachungen; ohne Neuerungen ein kurzer
  Hinweis.
- Datumsabhängig: `BUNDESANZEIGER_HEUTE` (nur Tests) setzt das „heute“.

JSON-Schema `neu`:

```json
{
  "suchbegriff": "Deutsche Bahn AG",
  "bereich": null,
  "erster_aufruf": true,
  "neue_treffer": [],
  "neueste": {"datum": "2026-07-22", "titel": "Hinweisbekanntmachung …"}
}
```

## Bereiche

| Wert | Anzeigename | `area_select` |
|---|---|---|
| `gesellschaft` | Gesellschaftsbekanntmachungen | `6` |
| `kapitalmarkt` | Kapitalmarkt | `7` |
| `gericht` | Gerichtlicher Teil | `5` |
| `finanzberichte` | Rechnungslegung/Finanzberichte | `22` |
| `amtlich` | Amtlicher Teil | `1` |
| `verschiedenes` | Verschiedene Bekanntmachungen | `8` |
| `nichtamtlich` | Nichtamtlicher Teil | `2` |

Ohne `--bereich` wird `area_select=""` (alle Bereiche) gesendet. Ein unbekannter
Bereich ist ein Usage-Fehler (Exit 2) mit Liste der gültigen Werte.

## Exit-Codes

| Code | Bedeutung |
|---|---|
| `0` | Erfolg, auch bei „keine Treffer“ und bei Captcha-Hinweis. |
| `1` | Allgemeiner Fehler (z. B. unerwartete Antwort, Parsing-Fehler, IO). |
| `2` | Usage-Fehler: unbekanntes Kommando/Argument, ungültiger Bereich, ungültiges Datum/`--limit`, mehrdeutige Firma ohne TTY und ohne `--erster`. |
| `3` | Netzwerk- oder Quellenfehler (DNS, Timeout, HTTP >= 400, Session abgelaufen, unerwartete Weiterleitung). |
| `4` | Login nötig. Für dieses Tool reserviert; aktuell nie verwendet, da rein lesend. |
| `130` | Abbruch durch Strg+C. Kein Traceback. |

Fehler nennen den nächsten Schritt, z. B.
`Netzwerkfehler – Verbindung prüfen oder später erneut versuchen.` oder
`Keine gültige Session – erneut suchen.`

## Umgebungsvariablen

| Variable | Bedeutung |
|---|---|
| `BUNDESANZEIGER_BASE_URL` | Basis-URL, Default `https://www.bundesanzeiger.de`. Für Fake-Server/Tests. |
| `BUNDESANZEIGER_HEUTE` | Datum `JJJJ-MM-TT` für deterministische `neu`-Tests. Nur Test/CI. |
| `NO_COLOR` | Farbausgabe aus, sofern Farben verwendet werden. |
| `XDG_CACHE_HOME` | Basis für den Cache, Default `~/.cache`. |
| `XDG_STATE_HOME` | Basis für den Zustand, Default `~/.local/state`. |

Ungültige Werte (z. B. unparsebares Datum, kaputte URL, `--limit 0`) führen zu
einem sauberen Fehler ohne Traceback.

## Config- und Cache-Pfade

| Pfad | Inhalt | Rechte |
|---|---|---|
| `$XDG_CACHE_HOME/bundesanzeiger-cli/` | HTTP-Cache, TTL 10 Minuten | Verzeichnis 0700, Dateien 0600 |
| `$XDG_STATE_HOME/bundesanzeiger-cli/state.json` | Stand für `neu` je Suchbegriff/Bereich | Datei 0600 |

Die Cookies der Bundesanzeiger-Session bleiben im Speicher des jeweiligen
Aufrufs und werden nicht dauerhaft gespeichert. Es werden keine Zugangsdaten
gespeichert.

## Netzwerkverhalten

- Pro Aufruf wenige GET-Requests: Startseite (Formularfeld lesen), Suche,
  optional Detail.
- User-Agent mit Repo-URL:
  `bundesanzeiger-cli/0.1 (+https://github.com/smlfg/bundesanzeiger-cli)`.
- Detail-Links werden nur in derselben Session geöffnet; abgelaufene Sessions
  führen zu Exit 3 mit Hinweis auf eine erneute Suche.
- Bereich 22: Detailseite wird nicht automatisiert gelöst; Captcha-Meldung und
  Exit 0.
- Keine Requests an andere Hosts als die Basis-URL.
