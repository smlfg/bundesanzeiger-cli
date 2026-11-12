# Anforderungen: bundesanzeiger

## Zweck

`bundesanzeiger` macht die öffentlichen Bekanntmachungen auf
[bundesanzeiger.de](https://www.bundesanzeiger.de) im Terminal durchsuchbar.
Menschen finden Firmen-Bekanntmachungen über den Firmennamen, filtern nach
Bereich und Datum und lesen den Volltext nicht-finanzieller Bekanntmachungen.
Jahresabschlüsse (Rechnungslegung/Finanzberichte) bleiben ein durchsuchbarer
Index; ihr Captcha wird weder gelöst noch umgangen.

Das Tool ist rein lesend, braucht keinen Login und führt keine schreibenden
Web-Aktionen aus.

## Nutzer-Aufgaben

1. **Bekanntmachungen einer Firma finden.** `bundesanzeiger suche "Deutsche Bahn AG"`
   zeigt Gesamtzahl, Datum, Bereich, Firma mit Sitz und Titel der Treffer.
2. **Volltext lesen.** `bundesanzeiger lesen "Deutsche Bahn AG"` öffnet den
   Volltext des ersten Treffers in derselben HTTP-Session; eine Nummer wählt
   einen anderen Treffer.
3. **Nach Bereich und Datum filtern.** `--bereich finanzberichte` grenzt die
   Suche auf Rechnungslegung/Finanzberichte ein, `--seit JJJJ-MM-TT` blendet
   ältere Bekanntmachungen clientseitig aus.
4. **Jahresabschluss-Index nutzen.** Der Index ist sichtbar; beim Volltext nennt
   das Tool den Captcha-Schutz und die URL zum Öffnen im Browser, ohne das
   Captcha zu lösen.
5. **Neue Bekanntmachungen seit dem letzten Aufruf sehen.**
   `bundesanzeiger neu "Deutsche Bahn AG"` speichert den Stand lokal (0600) und
   zeigt beim nächsten Aufruf nur neuere Bekanntmachungen.
6. **Keine Treffer verständlich behandeln.** Exit 0 mit Hinweis auf Schreibweise
   oder anderen Bereich, kein Traceback.

## Nachfrage

Quelle und Datum aus dem Tool-Brief (Demand-Gate, `NEXT20.md` Platz 8, bedingt
„Captcha bei Dokumentabruf prüfen“), geprüft am **12.11.2026**:

- Suche und Volltext nicht-finanzieller Bekanntmachungen funktionieren ohne
  Captcha; nur Rechnungslegung/Finanzberichte (Bereich 22) zeigt beim
  Dokumentabruf ein Captcha.
- `bundesAPI/deutschland` Issues **#145/#75** belegen den kaputten
  Captcha-Code bestehender Ansätze.
- Für denselben Zweck existiert ein bezahlter Apify-Actor
  `studio-amba/bundesanzeiger-scraper`.
- Der Bundesanzeiger-MCP (★1) ist seit **2025-07** ohne Aktivität.

Daraus folgt: Der Bedarf ist belegt, die Captcha-Grenze ist akzeptiert, und ein
kostenloses, lesendes CLI mit klarer Captcha-Meldung ist die sinnvolle
Abgrenzung.

## Datenquelle

- Website: `https://www.bundesanzeiger.de`, Wicket-Anwendung mit
  sessiongebundenen Cookies.
- Startseite `GET /pub/de/start?0` liefert das Suchformular. Der Name des
  versteckten Formularfelds wechselt (Muster
  `\d+-\d+\.-top~content~panel-left~card-form`) und wird bei jedem Aufruf frisch
  aus der Startseite gelesen, nie hart kodiert.
- Suche `GET /pub/de/start?fulltext=…&area_select=…&search_button=Suchen` leitet
  auf `/pub/de/suchen2?N` weiter.
- Trefferzeilen: `div.first` (Firma + Sitz), `div.part` (Bereich), `div.info a`
  (Titel + Detail-Link), `div.date` (TT.MM.JJJJ). Gesamtzahl aus
  `div#piwik_info.result_info[data-count]`.
- Detail `GET` des Treffer-Links in derselben Session, Weiterleitung auf
  `/pub/de/suchergebnis?M`; Volltext in `div.publication_container`.
- Bereichswerte: `""` alle, `1` Amtlicher Teil, `5` Gerichtlicher Teil,
  `6` Gesellschaftsbekanntmachungen, `8` Verschiedene Bekanntmachungen,
  `22` Rechnungslegung/Finanzberichte, `2` Nichtamtlicher Teil,
  `7` Kapitalmarkt.
- Basis-URL für Tests und Fake-Server: `BUNDESANZEIGER_BASE_URL`.

## Grenzen

- **Inoffiziell.** Es gibt keine dokumentierte API und keine Zusage des
  Betreibers. HTML-Struktur und Formularfelder können sich jederzeit ändern.
- **Nur lesend live getestet.** Alle Live-Aufrufe am 12.11.2026 waren GETs auf
  öffentliche Seiten; es gibt keinen Login und keine schreibende Aktion.
- **Jahresabschlüsse nur als Index.** Der Volltext ist durch ein Captcha
  geschützt. Das Tool löst, umgeht oder automatisiert es nicht; es nennt die
  Such-URL für den Browser und endet mit Exit 0.
- **Sessiongebundene Detail-Links.** Links verfallen nach ca. 30 Minuten.
  `lesen` holt den Volltext deshalb immer über eine frische Suche in derselben
  Session.
- **Höflichkeit.** Wenige GETs pro Aufruf, User-Agent mit Repo-URL, Cache für
  10 Minuten. Kein Massen-Scraping, keine Parallel-Hammering.
- **Keine Vollständigkeitsgarantie.** Angezeigt werden die ersten Treffer der
  Website; `--limit` begrenzt die Ausgabe, `--seit` filtert clientseitig.
- **Keine Personendaten.** Fixtures und Tests enthalten keine echten
  Personendaten (Namen/Mails ggf. `example.invalid`).

## Nicht-Ziele

- Kein Captcha-Lösen und kein Umgehen von Schutzmechanismen.
- Kein Download oder Parsen von Jahresabschluss-Dokumenten.
- Kein Login, keine Watchlists, keine schreibenden Aktionen.
- Kein Ersatz für die rechtlich verbindliche Bekanntmachung im Browser.

## Akzeptanzkriterien

- Jede Sitzung aus `docs/UX.md` hat mindestens einen Akzeptanztest unter
  `tests/acceptance/`.
- Der README-Schnellstart enthält wörtlich die `$`-Befehle der UX-Sitzungen und
  beginnt mit der `pipx`-Installationszeile aus `ux-meta`.
- `python3 tests/harness/ux_check.py . --spec-only` endet mit Exit 0.
- `--help` und `--version` enden mit Exit 0; Fehler nennen den nächsten Schritt
  und erzeugen keinen Traceback (auch nicht bei Strg+C/EOF).
- Ausgabe im Terminal ist lesbar; JSON nur mit `--json` oder wenn stdout kein
  TTY ist.
