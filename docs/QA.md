# Pflicht-QA: bundesanzeiger-cli

- Datum: 2026-11-12
- Version: `bundesanzeiger 0.1.0`
- Commit: `8dda94d` (frisch per `pipx install git+https://github.com/smlfg/bundesanzeiger-cli`)
- Nachprüfung: Fixes `1a180b8` und `7280703`, Live-Aufrufe vom 2026-11-12
- Prüfer: unabhängige QA-Iteration (nicht Entwickler), nur lesende Live-Aufrufe
- Umgebung: `PATH=./scratch/pipx/bin`, isoliertes `HOME`/`XDG_*` unter `./scratch/qa`, Pseudo-Terminal über `script -qc`, Fake-Server `tests/harness/fake_server.py` mit den `ux-routes` aus `docs/UX.md`
- Belege: Protokolle unter `./scratch/qa/` (nicht versioniert). Auszüge stehen in der Tabelle.

## Ergebnis

**50 von 50 Prüfungen OK.** Beide vorherigen FAILs wurden behoben und live nachgeprüft; Details unter „Behobene FAILs“.

## Prüftabelle

| Prüfung | Befehl | Erwartet | Ergebnis | Beleg (gekürzt) |
|---|---|---|---|---|
| Frische pipx-Installation | `pipx install git+https://github.com/smlfg/bundesanzeiger-cli` (Orchestrator) | Erfolg, 0.1.0, `bundesanzeiger` im PATH | OK | `scratch/qa/pipx-install.log`: `installed package bundesanzeiger-cli 0.1.0`; `direct_url.json` nennt Commit `8dda94d` |
| Aufruf nur über pipx-PATH | `PATH=$PWD/scratch/pipx/bin:$PATH bundesanzeiger --version` | 0.1.0, nicht aus `scratch/venv` | OK | `bundesanzeiger 0.1.0`; `which` zeigt `scratch/pipx/bin/bundesanzeiger` |
| Globale Hilfe | `bundesanzeiger --help` | Exit 0, Befehle erklärt | OK | `scratch/qa/help.txt`, Exit 0 |
| Unterkommando-Hilfen | `bundesanzeiger suche\|lesen\|neu --help` | Jeweils Exit 0 | OK | `scratch/qa/help-*.err` leer, Exit 0 |
| Versionsausgabe | `bundesanzeiger --version` | Exit 0 | OK | `bundesanzeiger 0.1.0`, Exit 0 |
| README: Suche im TTY | `bundesanzeiger suche "Deutsche Bahn AG"` | Lesbarer Text, 6200 Treffer | OK | `scratch/qa/01-suche.log`: `Suche „Deutsche Bahn AG“: 6200 Treffer, 3 angezeigt` |
| README: Volltext im TTY | `bundesanzeiger lesen "Deutsche Bahn AG"` | Firma, Titel/Zeile, dann Volltext gemäß `INTERFACE.md` | OK (nach Fix `1a180b8`) | `scratch/qa/s6-lesen.log`: Kopfzeile, danach direkt `Die Deutsche Bahn Aktiengesellschaft mit Sitz in Berlin …`; keine doppelten Kopfdaten |
| README: Finanzindex | `bundesanzeiger suche "Deutsche Bahn AG" --bereich finanzberichte` | 993 Treffer, Bereich korrekt | OK | `scratch/qa/03-suche-finanz.log` |
| README: Captcha-Hinweis | `bundesanzeiger lesen "Deutsche Bahn AG" --bereich finanzberichte` | Exit 0, kein Lösen, Such-URL | OK | `scratch/qa/04-lesen-finanz.log`, Exit 0 |
| README: `neu` erster Aufruf | `bundesanzeiger neu "Deutsche Bahn AG"` | Ausgangsstand gespeichert | OK | `scratch/qa/05-neu.log` |
| README: `neu` Folgelauf | `bundesanzeiger neu "Deutsche Bahn AG"` | Keine neuen Bekanntmachungen | OK | `scratch/qa/24-neu2-live.log` |
| README: leere Suche | `bundesanzeiger suche "zzzqqqxnichtvorhanden"` | Exit 0, Tipp | OK | `scratch/qa/06-leer.log` |
| Kompletter Ablauf gegen Fake-Server | Alle README-Befehle gegen `fake_server.py` mit `ux-routes`, im Pseudo-Terminal | Textausgabe, 200er, keine Fremdhosts | OK | `scratch/qa/17`–`23-fake-*-tty.log`; 25 Requests, alle `127.0.0.1` |
| JSON bei Pipe | `bundesanzeiger suche "Deutsche Bahn AG" \| cat` | Genau ein JSON-Objekt | OK | `scratch/qa/35-fake-json.log`: 8/8 JSON-Zeilen parsebar |
| Text im TTY, JSON bei Pipe | `script -qc ...` vs. Pipe | TTY Text, Pipe JSON | OK | `scratch/qa/01-suche.log` vs. `29-suche.json` |
| Bereich `gesellschaft` | `suche "Deutsche Bahn AG" --bereich gesellschaft --limit 5 --json` | Alle Treffer Gesellschaftsbekanntmachungen | OK | `scratch/qa/08-live-semantik.log` |
| Bereich `kapitalmarkt` | dito mit `kapitalmarkt` | Alle Treffer Kapitalmarkt | OK | `scratch/qa/08-live-semantik.log` |
| Bereich `gericht` | dito mit `gericht` | Alle Treffer Gerichtlicher Teil | OK | `scratch/qa/08-live-semantik.log` |
| Bereich `finanzberichte` | dito mit `finanzberichte` | Alle Treffer Rechnungslegung/Finanzberichte | OK | `scratch/qa/08-live-semantik.log` |
| Bereich `amtlich` | dito mit `amtlich` | Alle Treffer Amtlicher Teil | OK | `scratch/qa/08-live-semantik.log` |
| Bereich `verschiedenes` | dito mit `verschiedenes` | Alle Treffer Verschiedene Bekanntmachungen | OK | `scratch/qa/08-live-semantik.log` |
| Bereich `nichtamtlich` | dito mit `nichtamtlich` | Alle Treffer Nichtamtlicher Teil | OK | `scratch/qa/08-live-semantik.log` |
| Datumsfilter über alle Treffer | `suche "Deutsche Bahn AG" --seit 2025-01-01 --limit 50 --json` | Kein Treffer vor 2025-01-01 | OK | `scratch/qa/08-live-semantik.log`: 4 Treffer, 0 Verstöße |
| Tippvariante klein | `suche "deutsche bahn ag"` | Gleiches Ergebnis wie Großschreibung | OK | 6200 Treffer, erster Treffer Deutsche Bahn AG |
| Tippvariante kurz | `suche "Deutsche Bahn"` | Treffer, sinnvolle Reihenfolge | OK | 7104 Treffer |
| Tippvariante lang | `suche "Deutsche Bahn Aktiengesellschaft"` | Treffer | OK | 6200 Treffer |
| Umlaut `Köln` | `suche "Köln" --limit 3 --json` | Treffer, Umlaut unverfälscht | OK | `Amtsgericht Köln`, 318330 Treffer |
| Umlaut `Müller` | `suche "Müller" --limit 3 --json` | Treffer, Umlaut unverfälscht | OK | `Müller adress GmbH`, 70410 Treffer |
| Mehrdeutige Firma ohne TTY | `bundesanzeiger lesen "Müller" --json` (Pipe) | Exit 2, Liste, `--erster`-Hinweis, JSON valide | OK | `scratch/qa/11-mehrdeutig.json`, Exit 2 |
| Mehrdeutige Firma im TTY | `printf '1\n' \| script -qc 'bundesanzeiger lesen "Müller"'` | Nummerierte Auswahl, gewählter Treffer wird gelesen | OK | `scratch/qa/12-auswahl-tty.log` |
| Agenten-Auswahl | `bundesanzeiger lesen "Müller" --erster --json` | Erster Treffer ohne Rückfrage | OK | `scratch/qa/13-erster.json`, Exit 0 |
| Treffernummer außerhalb | `bundesanzeiger lesen "Deutsche Bahn AG" 99 --json` | Exit 2 mit nächstem Schritt | OK | `scratch/qa/26-nr99.json` |
| Lesen ohne Treffer | `bundesanzeiger lesen "zzzqqqxnichtvorhanden" --json` | Exit 2 mit nächstem Schritt | OK | `scratch/qa/32-lesen-leer.json` |
| Ungültige Eingaben | `--limit 0/51`, `--seit 2025-13-01`, `--bereich quatsch`, unbekanntes Kommando | Exit 2, JSON-Objekt, kein Traceback | OK | `scratch/qa/08-live-semantik.log`, `34-ohne-kommando.out` |
| Kaputte Basis-URL | `BUNDESANZEIGER_BASE_URL='nicht-http://x' ...` | Exit 2, klare Meldung, kein Traceback | OK | `scratch/qa/10-url.json` |
| Netzwerkfehler | `BUNDESANZEIGER_BASE_URL=http://127.0.0.1:1 ...` | Exit 3, nächster Schritt, kein Traceback | OK | `scratch/qa/09-netz-tty.log`, `09-netz.json` |
| Strg+C | Suche gegen verzögernden Server, danach `SIGINT` | Exit 130, `Abgebrochen.`, kein Traceback | OK | `scratch/qa/16-strgc.log` |
| Dateiende am Auswahlprompt | `printf '' \| script -qc 'bundesanzeiger lesen "Müller"'` | Exit 2, Meldung, kein Traceback | OK | `scratch/qa/14-eof.log` |
| Falsche Auswahl | `printf 'abc\n' \| script -qc ...` | Exit 2, Meldung, kein Traceback | OK | `scratch/qa/15-falscheingabe.log` |
| Zustandsdatei | `bundesanzeiger neu "Deutsche Bahn AG"` | `state.json` 0600, Verzeichnis 0700 | OK | `find`: `600 .../state.json`, `700 .../bundesanzeiger-cli` |
| Cache-Dateien | `bundesanzeiger suche ...` | Cache-Dateien 0600, Verzeichnis 0700 | OK | `find`: `600 .../*.json`, `700 .../bundesanzeiger-cli` |
| Keine dauerhaften Cookies | Mehrere Live-Aufrufe | Keine Cookie-/Session-Datei im HOME | OK | `find scratch/qa/home -type f` = 0 |
| Keine schreibenden Requests | Fake-Server-Protokoll | Nur GET | OK | `scratch/qa/07-fake.log`: 25× GET |
| Captcha wird nicht gelöst | `lesen ... --bereich finanzberichte --json` | `captcha_erforderlich=true`, Exit 0, kein POST | OK | `scratch/qa/31-captcha.json` |
| Captcha-URL im Browser nutzbar | Ohne Session: GET der ausgegebenen URL | Zeigt die Trefferliste/das Dokument im Browser | OK (nach Fix `7280703`) | `https://www.bundesanzeiger.de/pub/de/suchen2?0` liefert ohne Session HTTP 200, bleibt auf der URL, `data-count=17439465`, 22 Trefferzeilen im Suchergebnis-Index (`scratch/qa/s6-captcha-browser.json`, `s6-captcha-browser.html`) |
| JSON-Schemata | `suche`, `lesen`, `neu`, Captcha, Fehler | Erwartete Schlüssel, valides JSON | OK | `scratch/qa/25-neu.json`, `29-suche.json`, `30-lesen.json`, `31-captcha.json`, `35-fake-json.log` |
| Unit-/Akzeptanztests | `scratch/venv/bin/pytest -q` | Grün | OK | `53 passed in 69.12s` (`scratch/qa/s6-pytest.log`) |
| UX-Gate voll | `python3 tests/harness/ux_check.py .` | Kein FAIL | OK | `PASS`, UX00–UX08 PASS, UX09 SKIP (`scratch/qa/s6-ux-check.log`) |
| UX-Sitzungen | `python3 tests/harness/ux_session.py .` | Alle Sitzungen PASS | OK | 5/5 PASS (`scratch/qa/s6-ux-session.log`) |

## Behobene FAILs

1. **Volltextausgabe enthielt doppelte Kopfdaten (behoben in `1a180b8`).**
   `parse_publication` überspringt die Titel-Elemente (`z_titel`), sodass nach der
   CLI-Kopfzeile direkt der Fließtext beginnt. Live nachgeprüft:
   `scratch/qa/s6-lesen.log`.
2. **Captcha-Hinweis nannte eine sitzungsgebundene URL (behoben in `7280703`).**
   Der Hinweis verweist jetzt auf den sessionfreien Suchergebnis-Index
   `https://www.bundesanzeiger.de/pub/de/suchen2?0`; die gefilterte Trefferliste
   bleibt in der CLI-Session. Gegenprobe ohne Session: HTTP 200, `data-count=17439465`,
   Trefferzeilen sichtbar (`scratch/qa/s6-captcha-browser.json`).
