# UX-Spec: bundesanzeiger

Diese Datei beschreibt die wichtigsten Aufgaben eines Menschen mit dem
Bundesanzeiger (bundesanzeiger.de) als abtippbare Terminal-Sitzungen. Alle
Befehle sind so formuliert, wie sie im Terminal eingegeben werden. Das Tool ist
rein lesend: Es gibt keine Login-Pflicht, keine schreibende Aktion und daher
keine `ux-formsteps`; Jahresabschlüsse bleiben wegen des Captchas ein reiner
Index.

## Meta

```ux-meta
{"tool": "bundesanzeiger",
 "install": "pipx install git+https://github.com/smlfg/bundesanzeiger-cli",
 "base_url_env": "BUNDESANZEIGER_BASE_URL",
 "env": {"BUNDESANZEIGER_HEUTE": "2026-11-12"}}
```

`BUNDESANZEIGER_HEUTE` dient nur dazu, datumsabhängige Befehle wie `neu` in
Tests deterministisch zu machen; im Alltag wird das heutige Datum verwendet.

## Sitzungen

### Installation und erste Suche

Die Installation landet mit `pipx` im PATH. Der Suchbegriff ist positional; die
Ausgabe zeigt Datum, Bereich, Firma und Titel, damit ein Mensch ohne Nachschlagen
weiterarbeiten kann.

```ux-session
$ pipx install git+https://github.com/smlfg/bundesanzeiger-cli
< bundesanzeiger
$ bundesanzeiger suche "Deutsche Bahn AG"
< Suche „Deutsche Bahn AG“: 6200 Treffer, 3 angezeigt
< 1) 22.07.2026 · Gesellschaftsbekanntmachungen · Deutsche Bahn Aktiengesellschaft (Berlin)
<    Hinweisbekanntmachung (gemäß § 62 Abs. 4 Satz 3 i.V.m. Abs. 3 UmwG)
< 2) 22.05.2025 · Gesellschaftsbekanntmachungen · Deutsche Bahn Aktiengesellschaft (Berlin)
<    Hinweisbekanntmachung gemäß § 62 Abs. 4 Satz 3 i.V.m. Abs. 3 UmwG
< 3) 15.05.2025 · Gesellschaftsbekanntmachungen · Deutsche Bahn Aktiengesellschaft (Berlin)
<    Hinweisbekanntmachung gemäß § 62 Abs. 4 Satz 3 i.V.m. Abs. 3 UmwG
! exit 0
```

### Volltext einer Bekanntmachung lesen

Ohne Nummer wird der erste Treffer gelesen. Der Volltext wird in derselben
Session über eine frische Suche geholt, weil die Detail-Links ca. 30 Minuten
sessiongebunden sind.

```ux-session
$ bundesanzeiger lesen "Deutsche Bahn AG"
< Deutsche Bahn Aktiengesellschaft (Berlin)
< Hinweisbekanntmachung (gemäß § 62 Abs. 4 Satz 3 i.V.m. Abs. 3 UmwG) · 22.07.2026 · Gesellschaftsbekanntmachungen
< Die Deutsche Bahn Aktiengesellschaft mit Sitz in Berlin, eingetragen im Handelsregister
< des Amtsgerichts Charlottenburg unter HRB 50000 B, ist Alleingesellschafterin der
< Beyond1435 GmbH mit Sitz in Berlin, eingetragen im Handelsregister des Amtsgerichts
< Charlottenburg unter HRB 181864 B. Es ist beabsichtigt, die Beyond1435 GmbH nach §
< 2 UmwG auf die Deutsche Bahn Aktiengesellschaft im Wege der Aufnahme durch Übertragung
< ihres Vermögens als Ganzes zu verschmelzen.
! exit 0
```

### Jahresabschluss: Index und Captcha-Hinweis

Der Bereich `finanzberichte` zeigt weiterhin die Trefferliste (Index). Der
Volltext eines Jahresabschlusses ist auf bundesanzeiger.de durch ein Captcha
geschützt; das Tool löst oder umgeht es nicht, sondern nennt den nächsten Schritt.

```ux-session
$ bundesanzeiger suche "Deutsche Bahn AG" --bereich finanzberichte
< Suche „Deutsche Bahn AG“ (Rechnungslegung/Finanzberichte): 993 Treffer, 3 angezeigt
< 1) 13.05.2022 · Rechnungslegung/Finanzberichte · Deutsche Bahn Aktiengesellschaft (Berlin)
<    Jahresabschluss zum Geschäftsjahr vom 01.01.2021 bis zum 31.12.2021
< 2) 12.05.2022 · Rechnungslegung/Finanzberichte · Deutsche Bahn Aktiengesellschaft (Berlin)
<    Konzernabschluss zum Geschäftsjahr vom 01.01.2021 bis zum 31.12.2021
< 3) 14.07.2021 · Rechnungslegung/Finanzberichte · Deutsche Bahn Aktiengesellschaft (Berlin)
<    Jahresabschluss zum Geschäftsjahr vom 01.01.2020 bis zum 31.12.2020
$ bundesanzeiger lesen "Deutsche Bahn AG" --bereich finanzberichte
< Jahresabschluss ist auf bundesanzeiger.de durch ein Captcha geschützt – im Browser öffnen:
< https://www.bundesanzeiger.de/pub/de/start
! exit 0
```

### Neue Bekanntmachungen seit dem letzten Aufruf

`neu` merkt sich den Stand unter `~/.local/state/bundesanzeiger-cli` (Rechte
0600). Beim ersten Aufruf wird der Ausgangsstand gespeichert.

```ux-session
$ bundesanzeiger neu "Deutsche Bahn AG"
< Erster Aufruf – Ausgangsstand gespeichert.
< Neueste Bekanntmachung: 22.07.2026 · Hinweisbekanntmachung (gemäß § 62 Abs. 4 Satz 3 i.V.m. Abs. 3 UmwG)
< Beim nächsten Aufruf erscheinen nur neuere Bekanntmachungen.
! exit 0
```

### Keine Treffer

Ein Suchbegriff ohne Treffer endet mit Exit 0 und nennt den nächsten Schritt.

```ux-session
$ bundesanzeiger suche "zzzqqqxnichtvorhanden"
< Keine Treffer für „zzzqqqxnichtvorhanden“.
< Tipp: Schreibweise prüfen oder einen anderen Bereich wählen.
! exit 0
```

## Lesende Routen

Alle Requests der Sitzungen gegen den Fake-Server. Der versteckte Formularname
wird aus `start.html` gelesen; die Reihenfolge der Routen ist wichtig, weil die
Suche und die Startseite denselben Pfad `/pub/de/start` nutzen. Detail-Links aus
den Fixtures sind relativ und werden gegen die Basis-URL aufgelöst.

```ux-routes
[{"method":"GET","path":"/pub/de/start","query_contains":"zzzqqq","response":"tests/fixtures/ux/suche_leer.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/pub/de/start","query_contains":"area_select=22","response":"tests/fixtures/ux/suche_finanzberichte.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/pub/de/start","query_contains":"fulltext=","response":"tests/fixtures/ux/suche_deutsche_bahn.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/pub/de/start","response":"tests/fixtures/ux/start.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/pub/de/suchergebnis","query_contains":"captcha=","response":"tests/fixtures/ux/detail_captcha.html","status":200,"content_type":"text/html; charset=utf-8"},
 {"method":"GET","path":"/pub/de/suchergebnis","response":"tests/fixtures/ux/detail_bekanntmachung.html","status":200,"content_type":"text/html; charset=utf-8"}]
```

## Schreibende Aktion

Keine. Das Tool liest ausschließlich; es gibt keinen Login und keine
`ux-formsteps`. `UX09` entfällt daher (read-only). `UX07`/`UX08` sind mangels
schreibender Aktion ebenfalls nicht anwendbar.
