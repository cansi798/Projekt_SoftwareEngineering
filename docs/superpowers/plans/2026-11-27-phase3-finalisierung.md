# Phase 3 Finalisierung – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** BalanceOS-Portfolioteil 3 abgabefertig: exe, Systemtests, Testdokument, Benutzeranleitung, Anforderungserfüllung, Fazit, Abstract, Feedback Phase 2.

**Architecture:** Keine Änderungen an der App-Architektur. Neue Systemtests unter `app/tests/system/`, Release-Build per PyInstaller onefile nach `app/release/`, Dokumente in `docs/latex/`.

**Tech Stack:** Python 3.12, PySide6 6.12.0, pytest/pytest-qt, PyInstaller 6.22.3, LuaLaTeX (iu-pse), `tools/build_docs.py`.

**Spec:** `docs/superpowers/specs/2026-11-27-phase3-finalisierung-design.md`

## Global Constraints
- Abgabedatum Phase 3: 04.12.2026 (`\AbgabePhaseDrei`).
- Tatsächliche Testergebnisse nur aus echten Läufen; nichts vorwegnehmen.
- Kein „ich/wir/man“ außer im Abstract; Gendern mit Doppelpunkt; keine Gedankenstriche als Verbinder; Humanizer-Stil.
- Neue Quellen nur frei zugänglich, Kurzbelege mit Seitenangabe.
- Jeder Unterabschnitt ≥ ½ Seite, Unterteilung nur mit ≥ 2 Unterpunkten, Hinführung 2–3 Sätze.
- Abstract: genau 2 Seiten Textteil (Build-Skript prüft).
- exe < 100 MB (GitHub-Grenze); `Vorgaben/` nie committen; Phase-1/2-PDFs unverändert.
- Smart App Control nicht umgehen; exe-Starttest bleibt Aufgabe des Nutzers.

## Review Focus
- Systemtests laufen auf frischer Datei-Datenbank (nicht `:memory:`), sonst prüfen sie NFA04/NFA05 nicht.
- Zwangsbeenden direkt nach dem Speichern: Änderung muss nach Neustart vorhanden sein (NFA04).
- Netzwerkzugriff während eines kompletten Ablaufs muss einen Test scheitern lassen (NFA05).
- CSV mit UTF-8-BOM, Semikolon und 16 Spalten; JSON per `json.loads` gültig (NFA10).
- Testprotokoll-IDs müssen eindeutig auf existierende pytest-Funktionen zeigen.

---

### Task 1: Abgabedatum und Release-exe
**Files:** `docs/latex/_gemeinsam/meta.tex`, `app/balanceos.spec`, `app/README.md`, `.gitignore`, neu `app/release/BalanceOS.exe`
- [ ] `\AbgabePhaseDrei` auf `04.12.2026`.
- [ ] Spec auf onefile umstellen (EXE mit `a.binaries`, `a.datas`, ohne COLLECT), nicht benötigte Qt-Module ausschließen (alles außer QtCore/QtGui/QtWidgets). Bauen: `pyinstaller balanceos.spec --distpath release --workpath build`. Expected: `release/BalanceOS.exe` < 100 MB.
- [ ] README: Abschnitt Release (Datei, Größe, Smart-App-Control-Hinweis, Ausweichweg `python -m balanceos`).
- [ ] Commit.

### Task 2: Systemtests
**Files:** neu `app/tests/system/test_systemablauf.py`, `app/pyproject.toml` (Marker `system`)
Fixture `app_auf_datei(tmp_path, qtbot)`: `AppKontext.erstellen(tmp_path/"balanceos.db", heute=lambda: HEUTE)`, Hauptfenster anzeigen.
- [ ] `test_ts01_erster_start_mit_demodaten`: leere DB → Dashboard zeigt Startzustand; Demodaten über die Oberfläche laden → Dashboard zeigt Balken und mindestens einen Hinweis.
- [ ] `test_ts02_aktivitaet_erfassen_und_auswerten`: Dialog öffnen, gültig ausfüllen, speichern → Aktivität in DB und in der Aktivitätenliste.
- [ ] `test_ts03_ungueltige_eingabe_wird_abgewiesen` (NFA02): leerer Titel/Dauer 0 → Speichern bleibt wirkungslos, Fehlermeldung sichtbar, DB unverändert.
- [ ] `test_ts04_export_csv_und_json` (NFA10): CSV beginnt mit BOM, Semikolon, 16 Spalten je Zeile; JSON `json.loads` ok.
- [ ] `test_ts05_alle_daten_loeschen` (NFA05): nach Bestätigung „LÖSCHEN“ keine Nutzdaten.
- [ ] `test_ts06_kein_netzwerkzugriff` (NFA05): `socket.socket.connect`/`create_connection` per monkeypatch auf Fehler; kompletter Ablauf läuft.
- [ ] `test_ts07_zwangsbeenden_nach_speichern` (NFA04): 10 Unterprozesse speichern je eine Aktivität und enden mit `os._exit(1)`; danach 10 Aktivitäten in der DB.
- [ ] `test_ts08_startzeit` (NFA03): Unterprozess bis `Hauptfenster.show()` ≤ 5 s.
- [ ] `test_ts09_oberflaeche_deutsch_und_beschriftet` (NFA01): alle Seiten, Knöpfe und Felder mit nichtleerem deutschem Text bzw. Beschriftung; Erfassungsdialog von jeder Seite mit einem Klick erreichbar.
- [ ] Volle Suite + ruff grün. Commit.

### Task 3: NFA schärfen
**Files:** `02_Anforderungsdokument/kapitel/04_NichtfunktionaleAnforderungen.tex`
- [ ] Prüfkriterien NFA01, NFA03, NFA04, NFA05, NFA09, NFA10 so formulieren, dass jedes einen Messwert, Grenzwert und Prüfverfahren nennt und auf einen Testfall des Testdokuments passt. Commit.

### Task 4: Testdokument
**Files:** `05_Testdokument/kapitel/01_Teststrategie.tex`, `02_Testprotokoll.tex`, `03_Testergebnisse.tex`, `05_Testdokument/Testdokument.tex`
- [ ] Lauf mit `pytest -m "not leistung or leistung" --junitxml` und Coverage; Ergebnisse als Datengrundlage im Scratchpad.
- [ ] Teststrategie: Teststufen (frei zugängliche Quelle: SWEBOK v4 Kap. Testing), Umgebung, Nachverfolgbarkeit (Tabelle US/NFA → Testfall).
- [ ] Testprotokoll: TC-U, TC-I, TC-S je mit \testfall, jeweils Verweis auf pytest-Funktion; TC-S-10 exe-Start als vom Nutzer auszuführen markiert.
- [ ] Testergebnisse: Zahlen, Abdeckung, während der Entwicklung gefundene Fehler (GR18/GR20, R05/R07), offene Punkte. Commit.

### Task 5: Projektdokumentation Phase 3
**Files:** `01_Projektdokumentation/kapitel/05_Benutzeranleitung.tex`, `06_Anforderungserfuellung.tex`, `03_Zeitplanung.tex`, `04_Versionsverwaltung.tex`, `07_Aenderungen.tex`, neu `08_Fazit.tex`, `Projektdokumentation.tex`, Screenshots in `docs/bilder/`
- [ ] Benutzeranleitung (Installation exe/Python, Start, erste Schritte mit echten Screenshots).
- [ ] Anforderungserfüllung (Umsetzungsstand US01–US22, NFA01–NFA12 mit Testfall) und technische Schulden.
- [ ] Zeitplan: Fortschrittskontrolle M3/M4 mit Ist-Daten.
- [ ] Änderungen: Zeilen zum Feedback Phase 2.
- [ ] Neues Kapitel „Kritische Bewertung und Fazit“: Beantwortung der Projektfrage, Limitationen a posteriori, Fazit. Commit.

### Task 6: Redundanzen und Prägnanz (Feedback Phase 2)
- [ ] Wiederholungen zwischen Projektdokumentation, Anforderungs-, Spezifikations- und Architekturdokument suchen; Doppeltes durch Verweise ersetzen.
- [ ] Prägnanz: Füllwörter und umständliche Formulierungen kürzen (Feedback „Prägnanz einzelner Formulierungen“); Invariantenprüfung (Zahlen, IDs, Zitate unverändert). Commit.

### Task 7: Abstract
**Files:** `06_Abstract/Abstract.tex`
- [ ] Making-of und Reflexion in fünf Abschnitten, „ich“ erlaubt, genau 2 Seiten. Commit.

### Task 8: Endkontrolle und Abgabe vorbereiten
- [ ] Lektorat neuer Texte, Humanizer, Build `--phase 3`, Logs, Sichtprüfung, `--phase 3 --abgabe`.
- [ ] README/CHECKLISTE/abgabe-README aktualisieren; Commit, nach main, push.
- [ ] ZIP erst am Abgabetag nach den Tests des Nutzers (`--phase 3 --zip`).
