# Phase 2 BalanceOS: Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** BalanceOS (US01–US22) als lauffähige PySide6-Desktop-App implementieren und Portfolioteil 2 (Architekturdokument, überarbeitete Phase-1-Dokumente, Kurzzusammenfassung, Abgabe-PDF) bis 30.11.2026 abgabefertig machen.

**Architecture:** Vier Schichten mit Abhängigkeit nur nach unten: `praesentation` (PySide6-Widgets) → `anwendung` (Services, Transaktionsgrenze) → `domaene` (reines Python: Modell, Validierung, Bewertung, Regeln, Serien, WHO-5) → `persistenz` (sqlite3, Repositories, Stammdaten). Wochenbewertung und Hinweise werden bei jeder Anzeige neu berechnet und nicht gespeichert.

**Tech Stack:** Python 3.12, PySide6 6.x (LGPLv3), sqlite3 (Standardbibliothek), pytest, pytest-cov, pytest-qt, ruff, PyInstaller (nur Probebuild), LaTeX/TikZ über `tools/build_docs.py`.

**Spec:** `docs/superpowers/specs/2026-11-23-phase2-erarbeitung-design.md`. Fachliche Quelle aller Werte ist das Spezifikationsdokument in `docs/latex/03_Spezifikationsdokument/kapitel/` (abgekürzt **Spez**, Kapitel 1–5), dazu das Anforderungsdokument `docs/latex/02_Anforderungsdokument/kapitel/` (**Anf**).

## Global Constraints

- Python ≥ 3.12; einzige Laufzeitabhängigkeit `PySide6>=6.8,<7`; Dev-Abhängigkeiten nur unter `[project.optional-dependencies] dev`.
- Keine Netzwerkzugriffe, keine KI-Funktionen, keine Telemetrie (GR30, NFA05).
- Datenablage: `%APPDATA%\BalanceOS\balanceos.db`. Tests verwenden immer `":memory:"` oder `tmp_path` und nie den echten Pfad.
- Bezeichner deutsch ohne Umlaute, PEP 8 (snake_case im Code). Export-Schlüssel exakt wie im Datenmodell (camelCase, z. B. `sollStundenProWoche`). Aufzählungsliterale exakt wie Spez Tab. „Aufzählungstypen“ (`MINDESTZIEL`, `DURCHGEFUEHRT`, `AUSDAUER_MODERAT` …).
- UI-Texte deutsch mit Umlauten. Fehlermeldungen wörtlich aus Spez Tab. `tab:validierung`. Hinweistexte nach Spez Tab. `tab:hinweistexte`.
- Docstrings für jedes Modul und jede öffentliche Klasse/Methode. `ruff check` und `ruff format --check` ohne Befund (NFA08).
- Domäne importiert weder `PySide6` noch `sqlite3`. Ein Test prüft das (Task 1).
- Jede bestätigte Änderung wird sofort in einer Transaktion gespeichert (NFA04).
- Mindestfenstergröße 1280 × 720, Navigation über eine Seitenleiste mit sieben Seiten in dieser Reihenfolge: Dashboard, Woche, Aktivitäten, Statistik, Reflexion, Kompass, Einstellungen.
- Arbeitszweig `phase2`. Commits deutsch im Stil der bisherigen Historie, jede Nachricht endet mit `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Nach jedem Inkrement (I1–I5): `git push origin phase2`.
- Nie Dateien aus `Vorgaben/` committen. Nie `abgabe/Phase1_Konzeption/*_Abgabe.pdf` überschreiben.
- Prosa in LaTeX-Dokumenten und Kurzzusammenfassung: nach dem Schreiben mit Skill `humanizer:humanizer` überarbeiten, Fachbegriffe, Zahlen und Quellen unverändert lassen.
- Zeitachse: I1–I5 bis einschließlich 27.11., Code-Freeze 28.11., danach nur Doku und Bugfixes. Wird es knapp, wird zuerst I5 gekürzt (Rest als Technical Debt dokumentieren).
- Alle Befehle für Code laufen in `app/`: `cd app`.

## Review Focus

1. **Aktivität über Mitternacht am Sonntag** (z. B. Schlaf So 23:00–06:30): Sie zählt vollständig zur Woche des Beginns. Die Wochenansicht zeichnet nur den Teil bis 24:00 und markiert den Block mit „→ Folgetag“. Kein Absturz, kein doppeltes Zählen. Test: Task 2 (`test_dauer_ueber_mitternacht_sonntag_zaehlt_zur_kw_des_beginns`), Task 10 (`test_bewertung_ueber_mitternacht_nur_in_beginnwoche`).
2. **Jahreswechsel und KW 53** (2026 hat KW 53, 28.12.2026–03.01.2027): Blättern, „vorherige Wochen“ für R04/R07/R09 und die Statistik über acht Wochen müssen über den Jahreswechsel korrekt laufen. Test: Task 2 (`test_kw53_und_jahreswechsel`), Task 11 (`test_r04_ueber_jahreswechsel`).
3. **Umbenannter oder deaktivierter Standardbereich**: Regeln finden Bewegung, Schlaf, Erholung und Arbeit über `standard_schluessel`, nicht über den Namen. Ein deaktivierter Bereich lässt die Regel stillschweigend aus. Test: Task 11 (`test_regeln_finden_umbenannten_standardbereich`, `test_regel_bei_deaktiviertem_bereich_ausgelassen`).
4. **Leere Datenbank bzw. Zustand nach „Alle Daten löschen“**: Dashboard (leerer Zustand), Statistik ohne Daten, Export ohne Zeilen (nur Kopfzeile) und Hinweise funktionieren ohne Division durch null oder Ausnahme. Test: Task 10 (`test_bewertung_ohne_aktivitaeten`), Task 13 (`test_csv_export_ohne_zeilen_nur_kopfzeile`), Task 14 (`test_nach_alle_loeschen_wie_erster_start`), Task 16 (`test_alle_seiten_laden_mit_leerer_db`).
5. **Serie ändern oder löschen, nachdem einzelne Termine bearbeitet oder durchgeführt wurden** (GR19, GR20): Bearbeitete, durchgeführte, ausgefallene und vergangene Termine bleiben erhalten. Nur zukünftige, unbearbeitete GEPLANT-Termine werden ersetzt bzw. gelöscht. Test: Task 8 (`test_serie_aendern_schont_bearbeitete_termine`, `test_serie_loeschen_behaelt_vergangene_und_durchgefuehrte`).

---

## Dateistruktur

```
app/
├── pyproject.toml
├── README.md                                  (überarbeitet: Start, Tests, Build)
├── balanceos.spec                             PyInstaller-Probebuild (Task 15)
├── src/balanceos/
│   ├── __init__.py                            __version__ = "1.0.0"
│   ├── __main__.py                            ruft praesentation.app.starte()
│   ├── domaene/
│   │   ├── typen.py                           Aufzählungen
│   │   ├── modell.py                          Dataclasses der Geschäftsobjekte
│   │   ├── kalender.py                        KW (ISO-Woche), Dauer, Runden, Formatierung
│   │   ├── validierung.py                     Fehler, Prüffunktionen (GR, tab:validierung)
│   │   ├── bewertung.py                       GP03, GP05
│   │   ├── regeln.py                          GP04, R01–R10, Begründung
│   │   ├── serien.py                          GP02
│   │   └── who5.py                            GP06
│   ├── persistenz/
│   │   ├── datenbank.py                       Verbindung, Transaktion, Schema, Standardpfad
│   │   ├── stammdaten.py                      10 Standardbereiche, 6 Kompass-Modelle, R01–R10
│   │   ├── repo_bereiche.py                   Lebensbereich, Einstellungen
│   │   ├── repo_aktivitaeten.py               Aktivitaet, Wiederholungsserie, Ausnahme
│   │   └── repo_wissen.py                     Regel, KompassModell, Ausblendung, Who5, Reflexion
│   ├── anwendung/
│   │   ├── fehler.py                          ValidierungsFehler, RegelVerletzung
│   │   ├── kontext.py                         AppKontext: verdrahtet DB, Repos, Services
│   │   ├── stammdaten_service.py              Lebensbereiche, Wunschprofil, Einstellungen
│   │   ├── aktivitaet_service.py              Aktivitäten, Serien, Horizont
│   │   ├── auswertung_service.py              Bewertung, Hinweise, Verlauf, Regeln, Kompass
│   │   ├── export_service.py                  CSV, JSON
│   │   ├── demodaten.py                       Generator Persona Sarah Keller
│   │   ├── daten_service.py                   Demodaten laden/entfernen, alles löschen
│   │   └── reflexion_service.py               WHO-5, Wochenreflexion
│   └── praesentation/
│       ├── app.py                             starte(), QApplication, Fehlerdialog bei DB-Fehler
│       ├── stil.py                            QSS, Farben, Schrift
│       ├── zustand.py                         Zustand(QObject): Signale, gewählte KW
│       ├── hauptfenster.py                    Seitenleiste, Kopfzeile, QStackedWidget
│       ├── widgets/{feldfehler,soll_ist_balken,wochenkalender,liniendiagramm}.py
│       ├── seiten/{basis,dashboard,woche,aktivitaeten,statistik,reflexion,kompass,einstellungen}.py
│       └── dialoge/{aktivitaet,begruendung,lebensbereich,who5,export,loeschen,demodaten}.py
└── tests/
    ├── conftest.py                            Fixtures: kontext (":memory:"), heute
    ├── unit/test_*.py
    ├── integration/test_*.py
    └── gui/test_*.py                          pytest-qt, offscreen
docs/diagramme/04_Klassendiagramm_Architektur/{architektur_uebersicht,klassendiagramm}.tex
docs/diagramme/05_Sequenzdiagramm/sequenz.tex
docs/latex/04_Architekturdokument/kapitel/0[1-4]_*.tex       (ausfüllen)
docs/latex/01_Projektdokumentation/kapitel/0[1,3,4]_*.tex    (ergänzen)
docs/latex/02_Anforderungsdokument/kapitel/0[1,4]_*.tex      (Feedback)
docs/latex/03_Spezifikationsdokument/kapitel/01_Datenmodell.tex (Korrektur 500 → 1.000 Zeichen)
abgabe/Phase2_Erarbeitung/Kurzzusammenfassung.md
```

---

## Inkrement I1: Grundgerüst

### Task 1: Projektgerüst und Werkzeuge

**Files:**
- Create: `app/pyproject.toml`, `app/src/balanceos/__init__.py`, `app/src/balanceos/__main__.py`, leere `__init__.py` in `domaene/`, `persistenz/`, `anwendung/`, `praesentation/` (mit `widgets/`, `seiten/`, `dialoge/`), `app/tests/conftest.py`
- Test: `app/tests/unit/test_architektur.py`

**Interfaces:**
- Produces: Paket `balanceos`, Start mit `python -m balanceos`, Testaufruf `pytest` in `app/`.

- [ ] **Step 1: Zweig anlegen.** `git switch -c phase2`
- [ ] **Step 2: `pyproject.toml` schreiben.** Build-Backend setuptools, `name = "balanceos"`, `requires-python = ">=3.12"`, `dependencies = ["PySide6>=6.8,<7"]`, `dev = ["pytest>=8", "pytest-cov>=5", "pytest-qt>=4.4", "ruff>=0.6", "pyinstaller>=6.10"]`, `[project.gui-scripts] balanceos = "balanceos.praesentation.app:starte"`. `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `pythonpath = ["src"]`, `markers = ["leistung: Lasttests NFA03/NFA12", "gui: Oberflächentests"]`, `qt_api = "pyside6"`. `[tool.ruff]`: `line-length = 100`, `target-version = "py312"`, `lint.select = ["E","F","W","I","N","UP","B","D"]`, `lint.pydocstyle.convention = "google"`, `lint.per-file-ignores = {"tests/**" = ["D"]}`.
- [ ] **Step 3: Installieren.** `cd app && python -m pip install -e ".[dev]"`. Erwartet: Erfolg. Danach die installierte PySide6-Version notieren (`python -c "import PySide6; print(PySide6.__version__)"`), sie kommt in Task 16 in die Technologietabelle.
- [ ] **Step 4: Architekturtest schreiben.**

```python
def test_domaene_importiert_weder_qt_noch_sqlite():
    """Die Domäne bleibt frei von Oberfläche und Datenhaltung (NFA07)."""
    import ast, pathlib
    verboten = {"PySide6", "sqlite3", "balanceos.persistenz", "balanceos.anwendung", "balanceos.praesentation"}
    for datei in pathlib.Path("src/balanceos/domaene").rglob("*.py"):
        baum = ast.parse(datei.read_text(encoding="utf-8"))
        for knoten in ast.walk(baum):
            namen = [a.name for a in getattr(knoten, "names", [])] if isinstance(knoten, ast.Import) else \
                    [knoten.module or ""] if isinstance(knoten, ast.ImportFrom) else []
            for n in namen:
                assert not any(n == v or n.startswith(v + ".") for v in verboten), f"{datei}: {n}"
```

Ein zweiter Test `test_persistenz_importiert_kein_qt` prüft dasselbe für `persistenz/` und `anwendung/` mit dem verbotenen Namen `PySide6`.

- [ ] **Step 5: Ausführen.** `pytest tests/unit/test_architektur.py -v`. Erwartet: PASS (die Pakete sind leer).
- [ ] **Step 6: Ruff.** `ruff check . && ruff format --check .`. Erwartet: keine Befunde.
- [ ] **Step 7: Commit.** `git add app && git commit -m "I1: Projektgerüst, Werkzeugkonfiguration und Architekturtest"`

### Task 2: Domänenmodell, Aufzählungen und Kalender

**Files:**
- Create: `app/src/balanceos/domaene/typen.py`, `modell.py`, `kalender.py`
- Test: `app/tests/unit/test_kalender.py`, `app/tests/unit/test_modell.py`

**Interfaces:**
- Produces (`typen.py`), alle als `class X(StrEnum)` mit Wert = Literal:
  `Bereichstyp{MINDESTZIEL, OBERGRENZE}`, `Aktivitaetsstatus{GEPLANT, DURCHGEFUEHRT, AUSGEFALLEN}`, `Bewegungsart{AUSDAUER_MODERAT, AUSDAUER_INTENSIV, KRAFT}`, `Evidenzart{THEORIE, EMPFEHLUNG, VALIDIERTES_INSTRUMENT, PERSOENLICHE_REGEL, PROGRAMMEIGEN}`, `Hinweisart{WARNUNG, POSITIV, SYSTEM}`, `Wochentag{MO, DI, MI, DO, FR, SA, SO}` mit `Wochentag.aus_datum(d: date) -> Wochentag` und `.index -> int` (MO=0).
  Dazu `StandardSchluessel(StrEnum)`: `ARBEIT, SCHLAF, BEWEGUNG, FAMILIE, HOBBYS, SOZIALE_KONTAKTE, FREIZEIT, ERHOLUNG, PERSOENLICHE_ENTWICKLUNG, VERPFLICHTUNGEN`.
- Produces (`modell.py`), `@dataclass(slots=True)`. `id: int | None = None` steht immer als letztes Feld mit Default. Felder in dieser Reihenfolge:
  - `Lebensbereich(name: str, typ: Bereichstyp, farbe: str, soll_stunden: float, gewicht: int = 1, aktiv: bool = True, standard_schluessel: StandardSchluessel | None = None, id)`, Property `ist_standard -> bool` (= `standard_schluessel is not None`)
  - `Aktivitaet(titel: str, lebensbereich_id: int, datum: date, dauer_minuten: int, status: Aktivitaetsstatus, beginn: time | None = None, ende: time | None = None, zufriedenheit: int | None = None, belastung: int | None = None, erholung: int | None = None, bewegungsart: Bewegungsart | None = None, notiz: str | None = None, ist_demo: bool = False, serie_id: int | None = None, einzeln_bearbeitet: bool = False, id)`
  - `Wiederholungsserie(titel: str, lebensbereich_id: int, wochentage: frozenset[Wochentag], startdatum: date, dauer_minuten: int, enddatum: date | None = None, beginn: time | None = None, ausnahmen: set[date] = field(default_factory=set), generiert_bis: date | None = None, id)`
  - `Einstellungen(alpha: float = 0.6, gesamtscore_anzeigen: bool = False)`
  - `KompassModell(schluessel: str, name: str, kurzbeschreibung: str, evidenzart: Evidenzart, quelle: str, grenzen: str)`
  - `Regel(kennung: str, bezeichnung: str, modell_schluessel: str, schwelle: float, zeitraum: int, aktiv: bool = True)`
  - `Begruendung(regel: str, modell: str, datenbasis: str, zeitraum: str, schwelle: str, wert: str, quelle: str, evidenzart: str, grenzen: str)` mit `zeilen() -> list[tuple[str, str]]` in genau dieser Reihenfolge, Beschriftungen „Regel“, „Modell“, „Datenbasis“, „Zeitraum“, „Schwelle“, „Ihr Wert“, „Quelle“, „Evidenzart“, „Grenzen“
  - `Hinweis(regel: str, art: Hinweisart, text: str, begruendung: Begruendung, kw: KW, lebensbereich_id: int | None = None)`
  - `Bereichsbewertung(lebensbereich_id: int, ist_stunden: float, soll_stunden: float, zielerfuellung: float | None, zufriedenheitsanteil: float | None, score: int | None, abweichung: float)`, wobei `zielerfuellung is None` „kein Soll festgelegt“ bedeutet
  - `Wochenbewertung(kw: KW, vollstaendigkeit_tage: int, ausreichende_daten: bool, bereiche: list[Bereichsbewertung], gesamtscore: int | None)`
  - `Who5Erhebung(datum: date, antworten: tuple[int, int, int, int, int], id)` mit Properties `rohwert`, `prozentwert`
  - `Wochenreflexion(kw: KW, antworten: tuple[str, str, str], stimmung: int | None = None, id)`
- Produces (`kalender.py`):
  - `@dataclass(frozen=True, order=True) class KW: jahr: int; woche: int` mit `aus_datum(d) -> KW` (classmethod), `heute(heute: date) -> KW` (classmethod), `montag() -> date`, `sonntag() -> date`, `tage() -> list[date]`, `verschoben(n: int) -> KW`, `label() -> str` → `"KW 46/2026"`, `iso() -> str` → `"2026-W46"`, `zeitraum_text() -> str` → `"KW 46/2026 (09.11.–15.11.2026)"`
  - `berechne_dauer(beginn: time | None, ende: time | None, dauer_minuten: int | None) -> int` (GR10/GR11; wirft `ValueError` bei ungültiger Kombination)
  - `kaufmaennisch_runden(wert: float) -> int` (Halbe stets aufrunden; über `Decimal(repr(wert)).quantize(Decimal("1"), ROUND_HALF_UP)`)
  - `stunden_text(stunden: float) -> str` → `"6,5 h"`, `zahl_text(wert: float, stellen: int = 1) -> str` → `"4,2"`

- [ ] **Step 1: Tests schreiben** (`test_kalender.py`):

```python
def test_kw_montag_und_label():
    kw = KW(2026, 46)
    assert kw.montag() == date(2026, 11, 9) and kw.sonntag() == date(2026, 11, 15)
    assert kw.label() == "KW 46/2026" and kw.iso() == "2026-W46"
    assert kw.zeitraum_text() == "KW 46/2026 (09.11.–15.11.2026)"

def test_kw53_und_jahreswechsel():
    assert KW.aus_datum(date(2027, 1, 1)) == KW(2026, 53)
    assert KW(2026, 53).verschoben(1) == KW(2027, 1)
    assert KW(2027, 1).verschoben(-2) == KW(2026, 52)

def test_dauer_aus_beginn_und_ende():
    assert berechne_dauer(time(18, 0), time(18, 45), None) == 45

def test_dauer_ueber_mitternacht():
    assert berechne_dauer(time(23, 0), time(6, 30), None) == 450

def test_dauer_ueber_mitternacht_sonntag_zaehlt_zur_kw_des_beginns():
    assert KW.aus_datum(date(2026, 11, 15)) == KW(2026, 46)  # Sonntag; die Aktivität trägt das Datum des Beginns

@pytest.mark.parametrize("b,e,d", [(time(8, 0), time(8, 0), None), (None, time(8, 0), None), (None, None, 0), (None, None, 1441)])
def test_dauer_ungueltig(b, e, d):
    with pytest.raises(ValueError):
        berechne_dauer(b, e, d)

@pytest.mark.parametrize("x,erwartet", [(72.5, 73), (0.5, 1), (65.00000000000001, 65), (64.49, 64), (100.0, 100)])
def test_kaufmaennisch_runden(x, erwartet):
    assert kaufmaennisch_runden(x) == erwartet
```

`test_modell.py`: `test_who5_rohwert_prozentwert` (Antworten `(3, 4, 3, 2, 4)` → 16 und 64, wie im JSON-Beispiel der Spez), `test_begruendung_reihenfolge` (die Beschriftungen von `zeilen()` stehen genau in der Reihenfolge oben), `test_wochentag_aus_datum` (09.11.2026 → `MO`).

- [ ] **Step 2:** `pytest tests/unit -v`. Erwartet: FAIL (ImportError).
- [ ] **Step 3: `typen.py`, `modell.py`, `kalender.py` implementieren** mit den Signaturen oben.
- [ ] **Step 4:** `pytest tests/unit -v && ruff check .`. Erwartet: PASS, keine Befunde.
- [ ] **Step 5: Commit.** `"I1: Domänenmodell, Aufzählungen und ISO-Kalenderwoche"`

### Task 3: Persistenz, Schema und Stammdaten

**Files:**
- Create: `persistenz/datenbank.py`, `persistenz/stammdaten.py`, `persistenz/repo_bereiche.py`, `persistenz/repo_aktivitaeten.py`, `persistenz/repo_wissen.py`
- Test: `tests/integration/test_persistenz.py`

**Interfaces:**
- Produces (`datenbank.py`):
  - `standardpfad() -> Path`: `Path(os.environ["APPDATA"]) / "BalanceOS" / "balanceos.db"`. Legt den Ordner an.
  - `class Datenbank`: `__init__(self, pfad: Path | str)`. Öffnet die Verbindung mit `PRAGMA foreign_keys=ON`, `PRAGMA journal_mode=WAL` (außer bei `:memory:`) und `PRAGMA synchronous=FULL`, setzt `row_factory = sqlite3.Row` und legt das Schema an, falls es fehlt (Tabelle `meta` mit `schema_version = 1`).
  - `@contextmanager transaktion(self) -> Iterator[sqlite3.Connection]` mit Commit bzw. Rollback. Verschachtelte Aufrufe werden in die äußere Transaktion eingebunden (Zähler).
  - `schliessen(self) -> None`
  - Tabellen: `lebensbereich`, `aktivitaet` (Index auf `datum`, FK `serie_id` mit `ON DELETE SET NULL`), `wiederholungsserie`, `ausnahme` (FK mit `ON DELETE CASCADE`, UNIQUE(serie_id, datum)), `kompassmodell`, `regel`, `einstellungen` (genau eine Zeile, `id = 1`), `hinweis_ausblendung` (regel, jahr, woche, lebensbereich_id; UNIQUE), `who5_erhebung`, `wochenreflexion` (UNIQUE(jahr, woche)). Datum und Uhrzeit werden als ISO-Text gespeichert, Mengen und Tupel als JSON-Text.
- Produces (`stammdaten.py`):
  - `STANDARDBEREICHE: list[Lebensbereich]`: die zehn Bereiche aus Spez Tab. `tab:standardbereiche` mit Typ und Soll und je einem `standard_schluessel`. Farben: Arbeit `#4C6EF5`, Schlaf `#5C4B8A`, Bewegung `#3A7D44`, Familie `#E8590C`, Hobbys `#F08C00`, Soziale Kontakte `#D6336C`, Freizeit `#1098AD`, Erholung `#2B8A3E`, Persönliche Entwicklung `#7048E8`, Alltägliche Verpflichtungen `#868E96`.
  - `KOMPASSMODELLE: list[KompassModell]`: sechs Modelle mit den Schlüsseln `LBM` (Lifestyle Balance Model, THEORIE, matuska2008), `ERM` (Effort-Recovery-Modell, THEORIE, meijman1998), `JDR` (Job-Demands-Resources-Theorie, THEORIE, bakker2017), `WHO_BEWEGUNG` (WHO-Bewegungsleitlinie, EMPFEHLUNG, bull2020), `SCHLAF` (Schlafempfehlung, EMPFEHLUNG, watson2015), `SYSTEM` (BalanceOS-Systemregeln, PROGRAMMEIGEN). `quelle` ist die APA-7-Angabe aus `docs/latex/_gemeinsam/literatur.bib`. `kurzbeschreibung` (3–5 Sätze, allgemein verständlich) und `grenzen` (2–3 Sätze) schreibt der Implementierer nach den Aussagen in Spez Kap. 2.3 und Anf. Erfundene Inhalte sind nicht erlaubt.
  - `REGELN: list[Regel]`, `(kennung, bezeichnung, modell, schwelle, zeitraum)`: R01 „Ausdauerbewegung unter Richtwert“, WHO_BEWEGUNG, 150, 1 · R02 „Muskelkräftigung unter Richtwert“, WHO_BEWEGUNG, 2, 1 · R03 „Schlafdauer unter Empfehlung“, SCHLAF, 7, 1 · R04 „Bereich dauerhaft unter Wunsch“, LBM, 0.5, 3 · R05 „Hohe Belastung bei geringer Erholung“, ERM, 4, 1 · R06 „Wochenende ohne Erholung“, ERM, 6, 1 · R07 „Arbeit über Soll bei hoher Belastung“, JDR, 4, 3 · R08 „Wunsch erreicht“, LBM, 1, 1 · R09 „Zufriedenheit gestiegen“, LBM, 1, 2 · R10 „Zu wenig Daten“, SYSTEM, 4, 1.
  - `initialisiere(db: Datenbank) -> None`: idempotent. Fügt nur fehlende Stammdaten und die Einstellungszeile ein.
- Produces (Repositories, Konstruktor jeweils `(db: Datenbank)`):
  - `LebensbereichRepository`: `alle() -> list[Lebensbereich]` (Standardbereiche in Tabellenreihenfolge, dann eigene nach Name), `nach_id(id) -> Lebensbereich | None`, `nach_schluessel(s: StandardSchluessel) -> Lebensbereich | None`, `speichern(b) -> Lebensbereich` (Insert oder Update), `loeschen(id) -> None`, `hat_zuordnungen(id) -> bool`
  - `EinstellungenRepository`: `laden() -> Einstellungen`, `speichern(e) -> None`
  - `AktivitaetRepository`: `im_zeitraum(von: date, bis: date) -> list[Aktivitaet]` (sortiert nach Datum und Beginn, `None` zuletzt), `nach_id`, `speichern`, `loeschen(id)`, `alle() -> list[Aktivitaet]`, `loesche_demo() -> int`, `gibt_demo() -> bool`, `termine_der_serie(serie_id) -> list[Aktivitaet]`, `einfuegen_viele(list[Aktivitaet]) -> None`
  - `SerieRepository`: `alle()`, `nach_id`, `speichern(s)` (schreibt die Ausnahmen mit), `loeschen(id)`
  - `RegelRepository`: `alle() -> list[Regel]`, `aktiv_setzen(kennung, aktiv) -> None` · `KompassRepository`: `alle() -> list[KompassModell]`
  - `AusblendungRepository`: `ausblenden(regel, kw, lebensbereich_id) -> None`, `ausgeblendet(kw) -> set[tuple[str, int | None]]`
  - `Who5Repository`: `speichern`, `alle()` (neueste zuerst) · `ReflexionRepository`: `fuer_kw(kw) -> Wochenreflexion | None`, `speichern(r)` (Upsert je KW)
  - Gemeinsame Funktion `alle_nutzdaten_loeschen(db) -> None` in `datenbank.py`: leert alle Tabellen außer `meta` und ruft danach `stammdaten.initialisiere` auf, alles in einer Transaktion.

- [ ] **Step 1: Tests schreiben:** `test_initialisierung_legt_zehn_bereiche_sechs_modelle_zehn_regeln_an` (Anzahl 10/6/10, Summe der Soll-Werte 143), `test_initialisierung_idempotent` (zweimal aufrufen ergibt weiterhin 10 Bereiche), `test_aktivitaet_roundtrip` (alle Felder einschließlich `time` und Enums bleiben erhalten), `test_serie_mit_ausnahmen_roundtrip`, `test_transaktion_rollback_bei_fehler` (Ausnahme im `with` bedeutet, dass nichts gespeichert wird), `test_aenderung_nach_neuem_oeffnen_vorhanden` (mit `tmp_path`-Datei, für NFA04), `test_alle_nutzdaten_loeschen_stellt_erststart_her`.
- [ ] **Step 2:** `pytest tests/integration/test_persistenz.py -v`. Erwartet: FAIL.
- [ ] **Step 3: Implementieren.**
- [ ] **Step 4:** `pytest -v && ruff check .`. Erwartet: PASS.
- [ ] **Step 5: Commit.** `"I1: SQLite-Persistenz, Repositories und Stammdaten"`

### Task 4: Hauptfenster, Navigation und Anwendungskontext

**Files:**
- Create: `anwendung/fehler.py`, `anwendung/kontext.py`, `praesentation/app.py`, `praesentation/stil.py`, `praesentation/zustand.py`, `praesentation/hauptfenster.py`, `praesentation/seiten/basis.py` und für jede der sieben Seiten eine Datei mit vorläufiger Platzhalterbeschriftung, `praesentation/widgets/feldfehler.py`
- Test: `tests/gui/test_hauptfenster.py`, Fixture `kontext` in `tests/conftest.py`

**Interfaces:**
- Produces:
  - `anwendung/fehler.py`: `class ValidierungsFehler(Exception)` mit `fehler: list[Fehler]` (`Fehler` stammt aus Task 5 und liegt in `domaene/validierung.py`; in diesem Task schon als `@dataclass(frozen=True) Fehler(feld: str, meldung: str)` anlegen), `class RegelVerletzung(Exception)` mit Meldung (für nicht feldbezogene GR, z. B. GR03).
  - `AppKontext` (dataclass) mit den Feldern `db`, `stammdaten`, `aktivitaeten`, `auswertung`, `export`, `daten`, `reflexion` (die Services aus Tasks 7–10; in diesem Task nur `db`), `classmethod erstellen(pfad: Path | str, heute: Callable[[], date] = date.today) -> AppKontext`. `heute` wird in alle Services gereicht, damit Tests das Datum festlegen können.
  - `Zustand(QObject)`: Signale `daten_geaendert = Signal()`, `woche_geaendert = Signal(object)`, Property `kw: KW`, Methode `setze_kw(kw)`.
  - `class Seite(QWidget)` in `seiten/basis.py`: `__init__(self, kontext: AppKontext, zustand: Zustand)`, Klassenattribut `titel: str`, Methode `aktualisieren() -> None` (wird bei `daten_geaendert` und `woche_geaendert` aufgerufen, aber nur, wenn die Seite sichtbar ist; sonst beim Anzeigen).
  - `Hauptfenster(QMainWindow)`: Seitenleiste (`QListWidget`, Objektname `seitenleiste`) mit den sieben Einträgen, Kopfzeile (Titel, `◀`, KW-Label, `▶`, Schaltfläche „Heute“, „+ Aktivität“), `QStackedWidget`. Mindestgröße 1280 × 720. Methode `zeige_seite(index: int)`.
  - `starte(argv: list[str] | None = None) -> int`: Bei `OSError` oder `sqlite3.Error` beim Öffnen der DB erscheint eine `QMessageBox` mit „Die Datenbank konnte nicht geöffnet werden: …“, Rückgabe 1.
  - `widgets/feldfehler.py`: `markiere(feld: QWidget, label: QLabel, meldung: str | None) -> None` setzt einen roten Rahmen (Property `fehler="true"` und QSS-Regel in `stil.py`) und den roten Text darunter oder entfernt beides.

- [ ] **Step 1: GUI-Test schreiben** (`QT_QPA_PLATFORM=offscreen` in `conftest.py` setzen, bevor PySide6 importiert wird): `test_sieben_seiten_in_fester_reihenfolge` (Texte der Seitenleiste = `["Dashboard", "Woche", "Aktivitäten", "Statistik", "Reflexion", "Kompass", "Einstellungen"]`), `test_wochenblaettern_aendert_kw` (Klick auf `▶` erhöht `zustand.kw` um 1, „Heute“ setzt sie zurück), `test_mindestgroesse` (1280 × 720).
- [ ] **Step 2:** `pytest tests/gui -v`. Erwartet: FAIL.
- [ ] **Step 3: Implementieren.** `__main__.py` ruft `sys.exit(starte())` auf.
- [ ] **Step 4:** `pytest -v`. Erwartet: PASS. Manuell: `python -m balanceos` öffnet ein Fenster mit sieben Seiten.
- [ ] **Step 5: Commit und Push.** `"I1: Hauptfenster mit Seitenleiste, Wochenwahl und Anwendungskontext"`, danach `git push -u origin phase2`.

---

## Inkrement I2: Erfassen (US01–US03, US05–US09)

### Task 5: Validierung (Geschäftsregeln und Eingabefelder)

**Files:**
- Create/Modify: `domaene/validierung.py`
- Test: `tests/unit/test_validierung.py`

**Interfaces:**
- Produces:
  - `Fehler(feld: str, meldung: str)` (aus Task 4) und Konstanten mit den Meldungen, wörtlich aus Spez `tab:validierung`, z. B. `M_TITEL = "Bitte 1 bis 80 Zeichen eingeben."`, `M_ZUKUNFT = "Zukünftige Aktivitäten sind noch nicht durchgeführt."`, `M_ENDDATUM = "Enddatum darf nicht vor dem Datum liegen."`, `M_LOESCHEN = "Bitte LÖSCHEN eingeben."` usw. Für jede Zeile der Tabelle mit Meldung gibt es eine Konstante.
  - `pruefe_aktivitaet(a: Aktivitaet, bereich: Lebensbereich | None, heute: date) -> list[Fehler]` (GR05, GR09, GR10, GR12, GR13, GR15). Feldnamen: `"titel"`, `"lebensbereich"`, `"zeit"`, `"dauer"`, `"status"`, `"notiz"`, `"bewertung"`, `"bewegungsart"`.
  - `pruefe_serie(s: Wiederholungsserie) -> list[Fehler]` (GR16; Felder `"wochentage"`, `"enddatum"`, `"dauer"`)
  - `pruefe_lebensbereich(b: Lebensbereich, alle: list[Lebensbereich]) -> list[Fehler]` (GR01, GR02, GR06, GR07; `alle` ist der Bestand ohne die Änderung; Felder `"name"`, `"aktiv"`, `"soll"`, `"summe"`, `"gewicht"`). Soll-Werte nur in Schritten von 0,5.
  - `pruefe_alpha(alpha: float) -> list[Fehler]` (GR08), `pruefe_who5(datum: date, antworten: Sequence[int | None], heute: date) -> list[Fehler]` (GR26; Meldung `f"Noch offen: {n} Aussagen."`), `pruefe_reflexion(antworten: Sequence[str], stimmung: int | None) -> list[Fehler]` (je höchstens 1.000 Zeichen), `pruefe_zeitraum(von: date, bis: date) -> list[Fehler]`, `pruefe_loeschbestaetigung(text: str) -> list[Fehler]` (exakt „LÖSCHEN“, GR29).
  - Hinweis zu GR13 (Bewertungen nur bei DURCHGEFUEHRT): Das Entfernen beim Statuswechsel übernimmt der Service (Task 8). `pruefe_aktivitaet` meldet Bewertungen bei einem anderen Status als Fehler `"bewertung"`.

- [ ] **Step 1: Tests schreiben**, eine parametrisierte Tabelle je Prüffunktion, die alle Zeilen der Spez-Tabelle `tab:validierung` und GR01, GR02, GR05–GR13, GR15, GR16, GR26, GR29 abdeckt. Pflichtfälle: Titel `"  "` → `M_TITEL` · Titel mit 81 Zeichen → `M_TITEL` · Status DURCHGEFUEHRT am Datum `heute + 1` → `M_ZUKUNFT` · Bewegungsart im Bereich Arbeit → Fehler `"bewegungsart"` · inaktiver Bereich → „Bitte einen Lebensbereich wählen.“ · Name „bewegung“ neben „Bewegung“ → „Name existiert bereits.“ · Soll 2,3 → „0 bis 168 h in Schritten von 0,5 h.“ · Summe 168,5 → „Summe übersteigt 168 h pro Woche.“ · letzten aktiven Bereich mit Soll > 0 deaktivieren → „Mindestens ein aktiver Bereich braucht ein Soll.“ · Gewicht 11 → „Ganze Zahl von 0 bis 10.“ · WHO-5 mit zwei offenen Aussagen → „Noch offen: 2 Aussagen.“ · Bestätigung „löschen“ → `M_LOESCHEN`. Gültige Eingaben ergeben jeweils `[]`.
- [ ] **Step 2:** FAIL. **Step 3:** implementieren. **Step 4:** PASS.
- [ ] **Step 5: Commit.** `"I2: Validierung der Geschäftsregeln und Eingabefelder"`

### Task 6: Wiederholungsserien auflösen (GP02)

**Files:**
- Create: `domaene/serien.py`
- Test: `tests/unit/test_serien.py`

**Interfaces:**
- Produces: `HORIZONT_WOCHEN = 52`; `termindaten(serie: Wiederholungsserie, ab: date, bis: date) -> list[date]` (Tage im Bereich `[max(ab, startdatum), min(bis, enddatum)]` mit gewähltem Wochentag, ohne Ausnahmen, sortiert); `horizont(heute: date) -> date` (= `heute + 52 Wochen`); `ist_termindatum(serie, d: date) -> bool` (für GR18); `erzeuge_termin(serie, d: date) -> Aktivitaet` (Status GEPLANT, Titel, Bereich, Beginn und Dauer der Serie, `serie_id`; `ende` aus Beginn + Dauer, wenn ein Beginn gesetzt ist).

- [ ] **Step 1: Tests:** `test_termine_nur_an_gewaehlten_wochentagen` (DI/DO ab 03.11.2026 bis 19.11.2026 → 03., 05., 10., 12., 17., 19.11.) · `test_ausnahme_wird_uebersprungen` (Ausnahme 19.11. → fehlt) · `test_unbefristet_bis_horizont` (keine Termine nach `heute + 52 Wochen`) · `test_ist_termindatum_falscher_wochentag` (MI → False).
- [ ] **Step 2–4:** FAIL → implementieren → PASS.
- [ ] **Step 5: Commit.** `"I2: Auflösung wöchentlicher Wiederholungsserien"`

### Task 7: Stammdaten-Service (US01–US04)

**Files:**
- Create: `anwendung/stammdaten_service.py`
- Modify: `anwendung/kontext.py` (verdrahten)
- Test: `tests/integration/test_stammdaten_service.py`

**Interfaces:**
- Produces `StammdatenService(bereiche: LebensbereichRepository, einstellungen: EinstellungenRepository, db: Datenbank)`: `alle_bereiche() -> list[Lebensbereich]`, `aktive_bereiche() -> list[Lebensbereich]`, `speichern(b: Lebensbereich) -> Lebensbereich` (wirft `ValidierungsFehler`), `loeschen(id: int) -> None` (wirft `RegelVerletzung("Standardbereiche können nicht gelöscht, nur deaktiviert werden.")` (GR03) bzw. `RegelVerletzung("Dieser Bereich wird verwendet und kann nur deaktiviert werden.")` (GR04)), `verplante_stunden() -> float` (Summe Soll aktiver Bereiche), `einstellungen() -> Einstellungen`, `einstellungen_speichern(e: Einstellungen) -> None` (wirft `ValidierungsFehler`).

- [ ] **Step 1: Tests:** `test_erststart_zehn_standardbereiche` (US01) · `test_standardbereich_nicht_loeschbar` (GR03) · `test_genutzter_eigener_bereich_nicht_loeschbar` (GR04) · `test_eigener_ungenutzter_bereich_loeschbar` · `test_umbenennen_und_typ_aendern` (US02, US03) · `test_soll_summe_ueber_168_abgewiesen` (GR06) · `test_alpha_ausserhalb_abgewiesen` (GR08).
- [ ] **Step 2–4:** FAIL → implementieren → PASS.
- [ ] **Step 5: Commit.** `"I2: Service für Lebensbereiche, Wunschprofil und Einstellungen"`

### Task 8: Aktivitäten-Service mit Serien (US05–US08)

**Files:**
- Create: `anwendung/aktivitaet_service.py`
- Modify: `anwendung/kontext.py`
- Test: `tests/integration/test_aktivitaet_service.py`

**Interfaces:**
- Produces `AktivitaetService(aktivitaeten: AktivitaetRepository, serien: SerieRepository, bereiche: LebensbereichRepository, db: Datenbank, heute: Callable[[], date])`:
  - `fuer_woche(kw: KW) -> list[Aktivitaet]`
  - `vorbelegung(datum: date, beginn: time | None = None) -> Aktivitaet` (Status DURCHGEFUEHRT, wenn `datum <= heute`, sonst GEPLANT; Dauer 60)
  - `speichern(a: Aktivitaet) -> Aktivitaet`: berechnet die Dauer bei Beginn und Ende (GR10/GR11), entfernt Bewertungen bei einem Status ungleich DURCHGEFUEHRT (GR13), validiert (`ValidierungsFehler`), setzt `einzeln_bearbeitet = True`, wenn eine bestehende Aktivität mit `serie_id` geändert wird (GR19).
  - `loeschen(id: int) -> None`
  - `serie_anlegen(vorlage: Aktivitaet, wochentage: frozenset[Wochentag], enddatum: date | None) -> Wiederholungsserie`: validiert und erzeugt Termine von `vorlage.datum` bis `horizont(heute)`. Der Termin am Datum der Vorlage übernimmt Status und Bewertungen der Vorlage.
  - `serie_aendern(serie: Wiederholungsserie) -> None`: ersetzt zukünftige (`datum > heute`), unbearbeitete GEPLANT-Termine (GR19).
  - `serie_loeschen(serie_id: int) -> None`: entfernt zukünftige unbearbeitete GEPLANT-Termine und die Ausnahmen. Die übrigen Termine bleiben mit `serie_id = None` erhalten (GR20).
  - `termin_ueberspringen(aktivitaet_id: int) -> None`: legt eine Ausnahme an und löscht den Termin (US08, GR18). Ohne Serie: `RegelVerletzung`.
  - `horizont_fortschreiben() -> int`: erzeugt für jede Serie fehlende Termine bis `horizont(heute)` ab `generiert_bis + 1` und liefert die Anzahl. Wird in `AppKontext.erstellen` aufgerufen.

- [ ] **Step 1: Tests** (feste `heute = date(2026, 11, 18)`): `test_speichern_berechnet_dauer_ueber_mitternacht` (23:00–06:30 → 450) · `test_statuswechsel_entfernt_bewertungen` (GR13) · `test_durchgefuehrt_in_zukunft_abgewiesen` (GR12) · `test_serie_erzeugt_termine_bis_horizont` · `test_termin_ueberspringen_legt_ausnahme_an` (danach `horizont_fortschreiben` → der Termin entsteht nicht neu) · `test_serie_aendern_schont_bearbeitete_termine` · `test_serie_loeschen_behaelt_vergangene_und_durchgefuehrte` · `test_bearbeiteter_termin_wird_einzeln_markiert` · `test_neue_aktivitaet_nur_in_aktivem_bereich` (GR05).
- [ ] **Step 2–4:** FAIL → implementieren → PASS.
- [ ] **Step 5: Commit.** `"I2: Aktivitäten und Wiederholungsserien im Anwendungsservice"`

### Task 9: Aktivitätsdialog, Aktivitäten-Seite, Wochenansicht

**Files:**
- Create: `praesentation/dialoge/aktivitaet.py`, `praesentation/seiten/aktivitaeten.py`, `praesentation/seiten/woche.py`, `praesentation/widgets/wochenkalender.py`
- Modify: `praesentation/hauptfenster.py` („+ Aktivität“ öffnet den Dialog)
- Test: `tests/gui/test_aktivitaet_dialog.py`, `tests/gui/test_woche.py`

**Interfaces:**
- Consumes: `AktivitaetService`, `StammdatenService`, `validierung.*`, `feldfehler.markiere`.
- Produces:
  - `AktivitaetDialog(QDialog)`: `__init__(kontext, zustand, aktivitaet: Aktivitaet | None = None, datum: date | None = None, beginn: time | None = None, parent=None)`. Aufbau nach Mock-up `docs/diagramme/06_Mockups/mockup_aktivitaet.tex`: links Titel*, Lebensbereich* (nur aktive), Datum* (TT.MM.JJJJ), Optionsfeld „Beginn und Ende“/„Dauer“, Status; rechts Zufriedenheit, Belastung und Erholung (je fünf Schaltflächen 1–5 plus „keine Angabe“, nur bei Durchgeführt aktiv), Bewegungsart (nur bei Bereich Bewegung sichtbar), Notiz mit Zeichenzähler „n/500“; darunter „Wöchentlich wiederholen“ mit Wochentagen (Wochentag des Datums vorausgewählt) und Enddatum. Hinweis „endet am Folgetag“, wenn Ende < Beginn. Jedes Feld wird beim Verlassen geprüft (`pruefe_aktivitaet`). „Speichern“ ist nur bei gültigen Eingaben aktiv, der Tooltip nennt die offenen Felder. Im Bearbeitungsmodus heißt der Titel „Aktivität bearbeiten“, dazu „Löschen“ (Rückfrage) und bei Serienterminen „Termin überspringen“, „Serie löschen“ sowie ein Kontrollkästchen „Änderungen auf alle zukünftigen Termine der Serie anwenden“ (ruft `serie_aendern` auf). Diese Gestaltung des Serien-Bearbeitens ist eine Entscheidung des Assistenten. Nach dem Speichern: `zustand.daten_geaendert.emit()`. Enter speichert, Esc bricht ab.
  - `Wochenkalender(QWidget)`, gezeichnet mit `QPainter`: sieben Spalten MO–SO mit Datum, Zeitachse 0–24 Uhr, oben eine Zeile „ohne Uhrzeit“ für Aktivitäten ohne Beginn. Block in der Bereichsfarbe. GEPLANT wird umrandet mit heller Füllung gezeichnet, DURCHGEFUEHRT gefüllt, AUSGEFALLEN schraffiert und durchgestrichen. Aktivitäten über Mitternacht werden in der Spalte des Beginns bis 24:00 und, außer am Sonntag, in der Folgespalte ab 0:00 gezeichnet; am Sonntag steht „→ Folgetag“. Tooltip mit dem Titel. Signale `aktivitaet_doppelklick = Signal(int)` und `freie_flaeche_doppelklick = Signal(object, object)` (Datum, Uhrzeit auf 30 Minuten gerundet).
  - `AktivitaetenSeite`: `QTableWidget` mit den Spalten Datum, Zeit, Lebensbereich, Titel, Dauer, Status, Demo, Serie. Filter Bereich und Status (`QComboBox`). Schaltflächen „Bearbeiten“, „Löschen“, „Termin überspringen“ (nur bei Serientermin aktiv).

- [ ] **Step 1: GUI-Tests:** `test_speichern_gesperrt_bei_leerem_titel` · `test_enddatum_vor_datum_zeigt_meldung` (Feldtext genau „Enddatum darf nicht vor dem Datum liegen.“, Speichern gesperrt) · `test_bewertung_nur_bei_durchgefuehrt_aktiv` · `test_bewegungsart_nur_im_bereich_bewegung_sichtbar` · `test_speichern_legt_aktivitaet_an_und_signalisiert` (`qtbot.waitSignal(zustand.daten_geaendert)`) · `test_wochenkalender_zeigt_aktivitaeten_der_kw` (Anzahl der gezeichneten Blöcke = Anzahl der Aktivitäten der Woche; der Kalender stellt dafür `bloecke() -> list[tuple[int, QRectF]]` bereit).
- [ ] **Step 2–4:** FAIL → implementieren → PASS. Manuell: eine Aktivität erfassen, bearbeiten, löschen, eine Serie anlegen und einen Termin überspringen.
- [ ] **Step 5: Commit und Push.** `"I2: Aktivitätsdialog, Aktivitätenliste und Wochenansicht"`, `git push`

---

## Inkrement I3: Auswerten (US04, US10, US11, US19 Berechnung)

### Task 10: Wochenbewertung und Gesamt-Score (GP03, GP05)

**Files:**
- Create: `domaene/bewertung.py`
- Test: `tests/unit/test_bewertung.py`

**Interfaces:**
- Produces:
  - `MIN_TAGE = 4`
  - `zielerfuellung(typ: Bereichstyp, ist: float, soll: float) -> float` (Formel aus Spez Kap. 2.2, Schritt 3)
  - `bewerte_woche(kw: KW, bereiche: list[Lebensbereich], aktivitaeten: list[Aktivitaet], einstellungen: Einstellungen) -> Wochenbewertung`. Berücksichtigt nur DURCHGEFUEHRT in aktiven Bereichen und nur Daten innerhalb von `kw` (GR14). `bereiche` der Bewertung enthält jeden aktiven Bereich, auch solche mit Soll 0 (dann `zielerfuellung = None`, `score = None`). Bei `ausreichende_daten = False` ist jeder `score` und `gesamtscore` gleich `None`, Ist, Soll, Zielerfüllung und Abweichung bleiben gefüllt (GR21). `gesamtscore` nur bei `einstellungen.gesamtscore_anzeigen` und einer Gewichtssumme > 0 (GR22, GR23).

- [ ] **Step 1: Tests**, die Rechenbeispiele aus Spez Kap. 2.2.2 wörtlich:

```python
def test_beispiel1_mindestziel_mit_zufriedenheit():   # Bewegung, Soll 3 h, 2 × 45 min, Zufriedenheit 4 und 5
    assert bereich(bewertung, "Bewegung").score == 65
    assert bereich(bewertung, "Bewegung").zielerfuellung == pytest.approx(0.5)
    assert bereich(bewertung, "Bewegung").zufriedenheitsanteil == pytest.approx(0.875)

def test_beispiel2_obergrenze_ohne_zufriedenheit():   # Arbeit, Soll 40 h, 46 h ohne Zufriedenheit
    b = bereich(bewertung, "Arbeit")
    assert b.score == 85 and b.zielerfuellung == pytest.approx(0.85) and b.abweichung == pytest.approx(6.0)

def test_beispiel3_gesamtscore():                     # nur Bewegung und Arbeit aktiv, Gewicht 1, Anzeige an
    assert bewertung.gesamtscore == 75
```

Die Testdaten verteilen die Aktivitäten auf mindestens vier Tage, damit die Vollständigkeit erfüllt ist. Weitere Tests: `test_unter_vier_tagen_keine_scores` (3 Tage → `ausreichende_daten` False, alle Scores `None`, Ist-Werte vorhanden) · `test_geplant_und_ausgefallen_zaehlen_nicht` · `test_soll_null_nicht_bewertet` · `test_obergrenze_doppeltes_soll_ist_null` (80 von 40 h → 0) · `test_gesamtscore_aus_wenn_alle_gewichte_null` · `test_gesamtscore_nur_wenn_angezeigt` · `test_bewertung_ohne_aktivitaeten` (v = 0, keine Ausnahme) · `test_bewertung_ueber_mitternacht_nur_in_beginnwoche` (So 23:00–06:30 zählt in KW 46, nicht in KW 47) · `test_inaktiver_bereich_nicht_bewertet`.
- [ ] **Step 2–4:** FAIL → implementieren → PASS.
- [ ] **Step 5: Commit.** `"I3: Wochenbewertung nach Spezifikation mit Rechenbeispielen als Tests"`

### Task 11: Regelwerk R01–R10 mit Begründung (GP04)

**Files:**
- Create: `domaene/regeln.py`
- Test: `tests/unit/test_regeln.py`

**Interfaces:**
- Produces:
  - `@dataclass RegelKontext(kw: KW, bereiche: list[Lebensbereich], aktivitaeten: list[Aktivitaet], bewertungen: dict[KW, Wochenbewertung], regeln: dict[str, Regel], modelle: dict[str, KompassModell])`. `aktivitaeten` umfasst die aktuelle KW und die zwei vorherigen. `bewertungen` enthält `kw`, `kw-1` und `kw-2`.
  - `pruefe_regeln(k: RegelKontext) -> list[Hinweis]`: sortiert nach Hinweisart (WARNUNG, POSITIV, SYSTEM), dann nach Kennung, dann nach Bereichsreihenfolge. Inaktive Regeln werden übersprungen (GR25). Bei unzureichenden Daten entsteht nur R10 (sofern aktiv). R01–R09 nur bei ausreichenden Daten. Mehrwochenregeln nur, wenn jede betrachtete Woche ausreichende Daten hat. Standardbereiche werden über `standard_schluessel` gefunden; ist der Bereich inaktiv oder fehlt er, wird die Regel ausgelassen.
  - Je Regel eine private Funktion `_r01(k) -> list[Hinweis]` … `_r10(k)`. Bedingungen und Schwellen nach Spez Tab. `tab:regeln`, Schwelle aus `k.regeln[kennung].schwelle`. Festlegungen des Assistenten für Stellen, an denen die Spez Spielraum lässt: **R05** — ein Tag zählt, wenn er mindestens einen Belastungs- und einen Erholungswert hat und Ø Belastung ≥ 4 sowie Ø Erholung ≤ 2 gilt; die Schwelle 4 ist die Mindestanzahl Tage. **R06** — Erholung Sa + So = 0 h und die Summe aller OBERGRENZE-Bereiche Sa + So ≥ 6 h. **R07** — Ist > Soll in ≥ 2 der 3 Wochen, und der Mittelwert der Belastung aller Arbeitsaktivitäten der drei Wochen mit Belastungswert ist ≥ 4; ohne Belastungswerte kein Hinweis. **R09** — beide Wochen (kw, kw-1) brauchen ausreichende Daten und Zufriedenheitswerte im Bereich.
  - Texte nach Spez Tab. `tab:hinweistexte` mit eingesetzten Werten (Stunden und Mittelwerte mit einer Nachkommastelle und Komma, Gedankenstrich „–“). Begründung nach dem Muster in Spez Kap. 2.3 (Beispiel R01): `datenbasis`, `zeitraum` (`kw.zeitraum_text()` bzw. bei drei Wochen „KW 44–46/2026“, über den Jahreswechsel „KW 52/2026–KW 1/2027“), `schwelle` (mit Einheit), `wert`, `quelle` (APA-Kurzbeleg aus dem Modell), `evidenzart` (Text aus der Spalte „Evidenzkennzeichnung“ von `tab:hinweistexte`), `grenzen` (ab R01–R09 mindestens: „Nur erfasste Aktivitäten werden berücksichtigt; der Hinweis ersetzt keine ärztliche Beratung.“).

- [ ] **Step 1: Tests** (Hilfsfunktion `kontext_mit(...)` baut Wochen aus Aktivitätslisten auf): je Regel ein Test „löst aus“ und einer „löst nicht aus“ an der Schwelle, mit genau diesen Fällen:

```python
def test_r01_text_und_begruendung():  # KW 46/2026: 60 min moderat + 15 min intensiv
    h = einziger(hinweise, "R01")
    assert h.text == "Ausdauerbewegung in KW 46: 90 von 150 Minuten – unter dem WHO-Richtwert."
    assert h.begruendung.zeitraum == "KW 46/2026 (09.11.–15.11.2026)"
    assert h.begruendung.wert == "90 min" and h.begruendung.schwelle.startswith("150 min")

def test_r01_genau_150_kein_hinweis(): ...   # 150 min moderat
def test_r03_nur_ab_vier_tagen_mit_eintrag(): ...   # 3 Tage zu je 6 h → kein Hinweis
def test_r08_positiv_bei_erreichtem_wunsch(): ...   # Familie 12 von 10 h → "Wunsch im Bereich Familie in KW 46 erreicht: 12 von 10 h."
def test_r10_einziger_hinweis_bei_drei_tagen(): ...  # Text "Für KW 46 liegen Einträge an 3 von 7 Tagen vor – zu wenig Daten für eine Bewertung."
def test_sortierung_warnung_positiv_system(): ...
def test_deaktivierte_regel_erzeugt_nichts(): ...
def test_regeln_finden_umbenannten_standardbereich(): ...   # "Bewegung" → "Sport"; R01 löst weiter aus
def test_regel_bei_deaktiviertem_bereich_ausgelassen(): ...  # Schlaf inaktiv → kein R03, keine Ausnahme
def test_r04_ueber_jahreswechsel(): ...   # KW 52/2026, KW 53/2026, KW 1/2027
def test_jeder_hinweis_vollstaendig_begruendet(): ...   # NFA11: alle 9 Felder nicht leer, für R01–R10
```

Dazu R02, R04, R05, R06, R07 und R09 je mit Auslöse- und Nichtauslösefall.
- [ ] **Step 2–4:** FAIL → implementieren → PASS. Abdeckung: `pytest tests/unit --cov=balanceos.domaene.bewertung --cov=balanceos.domaene.regeln --cov-report=term-missing --cov-fail-under=80`. Erwartet: ≥ 80 % (NFA07).
- [ ] **Step 5: Commit.** `"I3: Regelwerk R01–R10 mit Begründung und Evidenzkennzeichnung"`

### Task 12: Auswertungs-Service und Dashboard (US10, US11, US13, US19)

**Files:**
- Create: `anwendung/auswertung_service.py`, `praesentation/seiten/dashboard.py`, `praesentation/widgets/soll_ist_balken.py`, `praesentation/dialoge/begruendung.py`
- Modify: `anwendung/kontext.py`
- Test: `tests/integration/test_auswertung_service.py`, `tests/gui/test_dashboard.py`

**Interfaces:**
- Produces `AuswertungService(aktivitaeten: AktivitaetRepository, bereiche: LebensbereichRepository, einstellungen: EinstellungenRepository, regeln: RegelRepository, kompass: KompassRepository, ausblendungen: AusblendungRepository, db: Datenbank)`:
  - `wochenbewertung(kw: KW) -> Wochenbewertung`
  - `hinweise(kw: KW, mit_ausgeblendeten: bool = False) -> list[Hinweis]` (lädt die Aktivitäten von `kw.verschoben(-2).montag()` bis `kw.sonntag()` mit einer einzigen Abfrage; GR24)
  - `hinweis_ausblenden(h: Hinweis) -> None`
  - `verlauf(bis_kw: KW, wochen: int = 8) -> list[Wochenbewertung]` (älteste zuerst, eine Abfrage)
  - `regeln() -> list[Regel]`, `regel_setzen(kennung: str, aktiv: bool) -> None`, `kompassmodelle() -> list[KompassModell]`, `modell(schluessel: str) -> KompassModell`
- Produces UI:
  - `SollIstBalken(QWidget)`: `setze(bewertung: Bereichsbewertung, typ: Bereichstyp, farbe: str)`. Skala bis 150 % des Solls, Marke beim Soll. Bei MINDESTZIEL ist der erreichte Teil grün `#2F9E44`; bei OBERGRENZE ist der Teil bis zum Soll neutral und der überschreitende Teil rot `#E03131`. Text „Ist / Soll h“.
  - `DashboardSeite`: Kachel „Datenvollständigkeit“ („6 von 7 Tagen“), Kachel „Gesamt-Score“ (nur, wenn eingeschaltet; Untertitel „programmeigener Score, nicht validiert“), Bereichsliste (Name, Typ, Balken, Ist und Soll, Score oder „–“ bzw. „kein Soll festgelegt“), Hinweisliste mit höchstens fünf Einträgen (Symbol je Art, Text, Kennung, „Warum?“, „Ausblenden“) und „Alle Hinweise (n)“, die eine Liste aller Hinweise öffnet. Leerer Zustand ohne Aktivitäten in der Datenbank: drei Schritte („Wunschprofil prüfen“, „Aktivitäten erfassen“, „Woche auswerten“) und die Schaltflächen „Erste Aktivität erfassen“ und „Demodaten laden“ (die zweite wird in Task 14 verdrahtet).
  - `BegruendungDialog(QDialog)`: `__init__(hinweis: Hinweis, kontext, zustand, parent=None)`. Zeigt die Zeilen von `begruendung.zeilen()` in fester Reihenfolge, darunter einen Kasten „Dieser Hinweis ist keine Diagnose. …“ und die Schaltfläche „Regel Rxx deaktivieren“ (`regel_setzen(..., False)` und `daten_geaendert`). Layout nach `mockup_begruendung.tex`.

- [ ] **Step 1: Tests:** `test_hinweise_ohne_ausgeblendete` · `test_verlauf_acht_wochen_aelteste_zuerst` · `test_regel_aus_erzeugt_keinen_hinweis` · GUI: `test_dashboard_leerer_zustand_bei_leerer_db` · `test_dashboard_zeigt_score_65_fuer_bewegung` (Daten aus Rechenbeispiel 1) · `test_hoechstens_fuenf_hinweise_sichtbar` · `test_begruendungsdialog_zeigt_neun_zeilen`.
- [ ] **Step 2–4:** FAIL → implementieren → PASS. Manuell prüfen, ob das Dashboard dem Mock-up `mockup_hauptfenster.tex` entspricht.
- [ ] **Step 5: Commit und Push.** `"I3: Auswertungsservice, Dashboard mit Soll-Ist-Balken und Begründungsdialog"`, `git push`

---

## Inkrement I4: Kompass und Daten (US12–US18)

### Task 13: Export CSV und JSON (US16, NFA10)

**Files:**
- Create: `anwendung/export_service.py`
- Modify: `anwendung/kontext.py`
- Test: `tests/integration/test_export.py`

**Interfaces:**
- Produces `ExportService(aktivitaeten, serien, bereiche, einstellungen, regeln, who5, reflexionen)` (Repositories):
  - `CSV_SPALTEN: tuple[str, ...]` = `("datum", "kalenderwoche", "lebensbereich", "bereichstyp", "titel", "beginn", "ende", "dauerMinuten", "status", "zufriedenheit", "belastung", "erholung", "bewegungsart", "notiz", "ausSerie", "istDemo")`
  - `dateiname_csv(von: date, bis: date) -> str` → `"BalanceOS_Aktivitaeten_2026-11-09_2026-11-15.csv"`; `dateiname_json(tag: date) -> str` → `"BalanceOS_Export_2026-11-16.json"`
  - `csv_exportieren(pfad: Path, von: date, bis: date) -> int` (Anzahl Zeilen; `encoding="utf-8-sig"`, `csv.writer(delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)`; „ja“/„nein“; leere optionale Werte bleiben leer)
  - `json_exportieren(pfad: Path, jetzt: datetime) -> None` (Struktur exakt wie das Beispiel in Spez Kap. 4.3.2; `ensure_ascii=False`, `indent=2`, UTF-8 ohne BOM; `exportiertAm` im Format `"2026-11-16T18:30:00"`; Serien mit laufender `nr` ab 1, Aktivitäten verweisen über `"serie": nr | null`)
  - Bei `OSError` beim Schreiben: `RegelVerletzung("Hier kann nicht gespeichert werden.")`

- [ ] **Step 1: Tests:** `test_csv_bom_semikolon_crlf_kopfzeile` (die ersten Bytes sind `b"\xef\xbb\xbfdatum;kalenderwoche;"`, die Zeilen enden mit `\r\n`) · `test_csv_quoting` (Notiz `a;b "c"` ergibt das Feld `"a;b ""c"""`) · `test_csv_zeitraum_und_sortierung` · `test_csv_export_ohne_zeilen_nur_kopfzeile` · `test_json_struktur_und_schluessel` (`format`, `version == 1`, Schlüssel der Lebensbereiche genau `{"name","typ","farbe","aktiv","istStandard","sollStundenProWoche","gewicht"}`, `json.loads` ohne Fehler) · `test_json_serienverweis_und_ausnahmen` · `test_export_nicht_beschreibbar` (Pfad ist ein Verzeichnis → `RegelVerletzung`).
- [ ] **Step 2–4:** FAIL → implementieren → PASS.
- [ ] **Step 5: Commit.** `"I4: CSV- und JSON-Export nach Spezifikation"`

### Task 14: Demodaten und Datenverwaltung (US17, US18)

**Files:**
- Create: `anwendung/demodaten.py`, `anwendung/daten_service.py`
- Modify: `anwendung/kontext.py`
- Test: `tests/integration/test_demodaten.py`, `tests/integration/test_daten_service.py`

**Interfaces:**
- Produces:
  - `erzeuge_demodaten(heute: date, bereiche: dict[StandardSchluessel, Lebensbereich]) -> list[Aktivitaet]`: deterministisch (`random.Random(46)`), acht Wochen `KW.heute(heute).verschoben(-7)` bis `KW.heute(heute)`. Alle Einträge mit `ist_demo = True` und nur in Standardbereichen. Tage nach `heute` nur GEPLANT ohne Bewertungen. Pflichtmuster: Die **Vorwoche** enthält im Bereich Bewegung genau zwei Aktivitäten AUSDAUER_MODERAT zu 45 min mit Zufriedenheit 4 und 5 (→ Score 65, R01 „90 von 150“). Die **älteste Woche** hat Einträge an genau drei Tagen (→ R10). Über die acht Wochen löst jede Regel R01–R10 mindestens einmal aus, mit dem Standard-Wunschprofil.
  - `DatenService(db, aktivitaeten: AktivitaetRepository, heute: Callable[[], date])`: `demodaten_vorhanden() -> bool`, `demodaten_laden() -> int` (wirft `RegelVerletzung`, wenn schon vorhanden; GR28), `demodaten_entfernen() -> int`, `alle_daten_loeschen(bestaetigung: str) -> None` (wirft `ValidierungsFehler` ohne exakt „LÖSCHEN“; danach `alle_nutzdaten_loeschen`, GR29).

- [ ] **Step 1: Tests:** `test_demodaten_decken_alle_regeln_ab` (für `heute = date(2026, 11, 22)` liefert `auswertung.hinweise(kw)` über die acht Wochen zusammen die Kennungen `{"R01",…,"R10"}`) · `test_demodaten_vorwoche_bewegung_65` · `test_demodaten_deterministisch` (zweimal erzeugt → gleiche Liste) · `test_demodaten_nicht_doppelt_ladbar` · `test_demodaten_entfernen_laesst_eigene_daten` (GR28) · `test_demodaten_aendern_wunschprofil_nicht` · `test_alle_loeschen_braucht_bestaetigung` · `test_nach_alle_loeschen_wie_erster_start` (10 Bereiche mit Standardwerten, Regeln aktiv, `alpha` 0,6, keine Aktivitäten).
- [ ] **Step 2–4:** FAIL → implementieren → PASS.
- [ ] **Step 5: Commit.** `"I4: Demodaten der Persona und Datenverwaltung"`

### Task 15: Einstellungen, Kompass, Datendialoge (US02–US04, US14, US15, US16–US18 UI)

**Files:**
- Create: `praesentation/seiten/einstellungen.py`, `praesentation/seiten/kompass.py`, `praesentation/dialoge/lebensbereich.py`, `praesentation/dialoge/export.py`, `praesentation/dialoge/loeschen.py`, `praesentation/dialoge/demodaten.py`
- Modify: `praesentation/seiten/dashboard.py` („Demodaten laden“ verdrahten)
- Test: `tests/gui/test_einstellungen.py`, `tests/gui/test_datendialoge.py`

**Interfaces:**
- Consumes: `StammdatenService`, `AuswertungService.regeln/regel_setzen/kompassmodelle`, `ExportService`, `DatenService`.
- Produces:
  - `EinstellungenSeite` mit vier Reitern: **Lebensbereiche** (Liste mit Farbpunkt, Typ, aktiv; „Neu“, „Bearbeiten“, „Deaktivieren“/„Aktivieren“, „Löschen“ mit den `RegelVerletzung`-Meldungen als Hinweisdialog) · **Wunschprofil** (Tabelle mit Soll-`QDoubleSpinBox`, Schritt 0,5, und Gewicht-`QSpinBox` 0–10, Summenzeile „x von 168 h verplant“, Kontrollkästchen „Gesamt-Score anzeigen“, Schieberegler α 0–1 in 0,1-Schritten mit Wertanzeige; jede gültige Änderung wird sofort gespeichert, eine ungültige wird am Feld markiert und nicht gespeichert) · **Regeln** (R01–R10 mit Bezeichnung, Modell, Evidenzart und Schalter) · **Daten** („Exportieren …“, „Demodaten …“, „Alle Daten löschen …“, dazu der Datenordner als Text).
  - `LebensbereichDialog(QDialog)`: Name*, Typ (zwei Optionsfelder mit Erklärung „mehr Zeit ist bis zum Soll besser“ bzw. „Überschreitung ist ungünstig“), Farbe aus einer Palette von zwölf Farben (die zehn Standardfarben plus `#C2255C` und `#0B7285`), aktiv, Soll, Gewicht, Anzeige „x von 168 h verplant“.
  - `ExportDialog`: Optionsfelder CSV/JSON, bei CSV Zeitraum von/bis (Vorbelegung: gewählte KW), „Exportieren …“ öffnet `QFileDialog.getSaveFileName` im Ordner „Dokumente“ mit Dateiname nach `dateiname_*`. Nach Erfolg erscheint eine Meldung mit Datei und Ordner.
  - `LoeschenDialog`: Warnung, Liste der betroffenen Daten, Hinweis „Bereits exportierte Dateien bleiben erhalten.“, Eingabefeld; „Endgültig löschen“ wird erst bei exakt „LÖSCHEN“ aktiv; der Fokus liegt anfangs auf „Abbrechen“. Danach zeigt das Hauptfenster das Dashboard.
  - `DemodatenDialog`: Optionsfelder „Laden“/„Entfernen“, nur die jeweils mögliche Option ist aktiv. Der Dashboard-Leerzustand lädt ohne Rückfrage (Spez Kap. 5.2) und meldet „Demodaten geladen. Entfernen unter Einstellungen → Daten.“ Nach dem Laden gilt (Entscheidung des Assistenten): Hat die aktuelle KW weniger als vier Tage mit Daten, wird die Vorwoche angezeigt, mit dem Hinweis „Die aktuelle Woche hat erst wenige Einträge. Angezeigt wird KW xx.“
  - `KompassSeite`: links die Liste der sechs Modelle, rechts Name, Evidenzart (als farbiges Etikett), Kurzbeschreibung, Quelle, Grenzen und zugehörige Regeln (Kennung, Bezeichnung, aktiv). Oben ein fester Kasten: „BalanceOS ist kein Medizinprodukt und stellt keine Diagnosen. Hinweise zeigen Zusammenhänge in Ihren Daten, keine Ursachen.“

- [ ] **Step 1: GUI-Tests:** `test_wunschprofil_ungueltige_summe_nicht_gespeichert` · `test_regel_schalter_deaktiviert_regel` · `test_loeschen_erst_bei_exakter_eingabe_aktiv` · `test_demodaten_dialog_nur_moegliche_option` · `test_kompass_zeigt_sechs_modelle`.
- [ ] **Step 2–4:** FAIL → implementieren → PASS.
- [ ] **Step 5: Commit und Push.** `"I4: Einstellungen, Kompass, Export-, Demodaten- und Löschdialog"`, `git push`

---

## Inkrement I5: Should-Funktionen (US19 UI, US20–US22)

### Task 16: WHO-5, Wochenreflexion, Statistik

**Files:**
- Create: `domaene/who5.py`, `anwendung/reflexion_service.py`, `praesentation/seiten/reflexion.py`, `praesentation/dialoge/who5.py`, `praesentation/seiten/statistik.py`, `praesentation/widgets/liniendiagramm.py`
- Modify: `anwendung/kontext.py`
- Test: `tests/unit/test_who5.py`, `tests/integration/test_reflexion_service.py`, `tests/gui/test_should_seiten.py`

**Interfaces:**
- Produces:
  - `who5.py`: `AUSSAGEN: tuple[str, ...]` (die fünf deutschen WHO-5-Aussagen „Ich war froh und guter Laune.“, „Ich habe mich ruhig und entspannt gefühlt.“, „Ich habe mich energisch und aktiv gefühlt.“, „Beim Aufwachen habe ich mich frisch und ausgeruht gefühlt.“, „Mein Alltag war voller Dinge, die mich interessieren.“), `SKALA: tuple[str, ...]` (Index 0–5: „Zu keinem Zeitpunkt“, „Ab und zu“, „Etwas weniger als die Hälfte der Zeit“, „Etwas mehr als die Hälfte der Zeit“, „Meistens“, „Die ganze Zeit“), `@dataclass Who5Ergebnis(rohwert: int, prozentwert: int, empfehlung: bool)`, `werte_aus(antworten: Sequence[int]) -> Who5Ergebnis` (`empfehlung` bei Prozentwert ≤ 50), `EMPFEHLUNGSTEXT` (Spez GP06: ärztliche oder psychotherapeutische Hilfe bei anhaltender Niedergeschlagenheit; „Das Ergebnis ist keine Diagnose.“).
  - `ReflexionService(who5: Who5Repository, reflexionen: ReflexionRepository, db, heute)`: `who5_speichern(datum: date, antworten: Sequence[int | None]) -> Who5Ergebnis` (`ValidierungsFehler`), `who5_verlauf() -> list[Who5Erhebung]`, `reflexion(kw: KW) -> Wochenreflexion | None`, `reflexion_speichern(kw: KW, antworten: tuple[str, str, str], stimmung: int | None) -> None` (Upsert, GR27).
  - `ReflexionSeite`: drei Leitfragen „Was ist diese Woche gut gelungen?“, „Was ist zu kurz gekommen?“, „Was nehme ich mir für die nächste Woche vor?“ (je `QPlainTextEdit`, Zähler „n/1000“), Stimmung 1–5 optional, „Speichern“. Daneben „WHO-5-Fragebogen ausfüllen“ und das letzte Ergebnis mit Etikett „validiertes Instrument“.
  - `Who5Dialog`: Datum, fünf Aussagen mit je sechs Optionsfeldern, „Auswerten“ erst bei vollständiger Beantwortung aktiv. Das Ergebnis zeigt Rohwert und Prozentwert, bei ≤ 50 % zusätzlich den Empfehlungstext.
  - `Liniendiagramm(QWidget)`, mit `QPainter` gezeichnet: `setze_reihen(beschriftungen: list[str], reihen: list[tuple[str, str, list[int | None]]])` (Name, Farbe, Werte). Y-Achse 0–100, Lücken bei `None`, Legende mit Kontrollkästchen zum Ein- und Ausblenden.
  - `StatistikSeite`: Verlauf der Bereichs-Scores über acht Wochen bis zur gewählten KW, optional eine Gesamt-Score-Reihe (gestrichelt, Etikett „programmeigen“). Darunter eine Tabelle Wochen × Bereiche. Ohne Daten erscheint der Text „Noch keine bewertbaren Wochen.“

- [ ] **Step 1: Tests:** `test_who5_beispiel` (`(3, 4, 3, 2, 4)` → 16/64, keine Empfehlung) · `test_who5_grenze_50` (Rohwert 12 → 48 % mit Empfehlung, Rohwert 13 → 52 % ohne) · `test_who5_unvollstaendig_abgewiesen` · `test_who5_datum_in_zukunft_abgewiesen` · `test_reflexion_upsert_eine_je_woche` · GUI: `test_statistik_ohne_daten` · `test_alle_seiten_laden_mit_leerer_db` (jede der sieben Seiten `aktualisieren()` ohne Ausnahme).
- [ ] **Step 2–4:** FAIL → implementieren → PASS.
- [ ] **Step 5: Commit und Push.** `"I5: WHO-5, Wochenreflexion und Statistik mit Liniendiagramm"`, `git push`

### Task 17: Qualität, Last, Probebuild, README

**Files:**
- Create: `tests/integration/test_leistung.py`, `app/balanceos.spec`
- Modify: `app/README.md`, `.gitignore` (Einträge `app/build/`, `app/dist/`)

- [ ] **Step 1: Lasttests** (`@pytest.mark.leistung`): `test_dashboard_3000_aktivitaeten_unter_1s` (NFA03: `wochenbewertung` + `hinweise` für eine KW in einer DB-Datei unter `tmp_path` mit 3.000 Aktivitäten über 52 Wochen, gemessen mit `time.perf_counter`, < 1,0 s) · `test_dashboard_30000_aktivitaeten_unter_2s` (NFA12, < 2,0 s) · `test_statistik_30000_unter_2s` (`verlauf`, < 2,0 s) · `test_db_groesse_30000_unter_50mb`. Die Lastdaten entstehen über `erzeuge_demodaten` mit verschobenem `heute`, bis die Anzahl erreicht ist.
- [ ] **Step 2:** `pytest -m leistung -v`. Erwartet: PASS. Messwerte notieren, sie kommen in Task 18 ins Architekturdokument.
- [ ] **Step 3: Vollständige Prüfung.** `pytest --cov=balanceos --cov-report=term && ruff check . && ruff format --check .`. Erwartet: alles grün, keine Befunde.
- [ ] **Step 4: Probebuild.** `pyinstaller balanceos.spec` (`--onedir`, windowed, Name `BalanceOS`, Einstieg `src/balanceos/__main__.py`). Danach `dist/BalanceOS/BalanceOS.exe` starten. Erwartet: Das Fenster öffnet sich, und die Startzeit liegt unter 5 s (NFA03); die Zeit notieren. `dist/` und `build/` werden nicht eingecheckt.
- [ ] **Step 5: README** mit diesen Abschnitten: Voraussetzungen, Installation (`pip install -e ".[dev]"`), Start (`python -m balanceos`), Tests (`pytest`, `pytest -m leistung`), Probebuild und Ordnerstruktur.
- [ ] **Step 6: Code-Freeze-Commit und Push.** `"Code-Freeze Phase 2: Lasttests, Probebuild und README"`, `git push`. Ab hier nur noch Bugfixes.

---

## Dokumentation (ab 28.11.; Task 19 kann ab I1 parallel laufen)

### Task 18: Architekturdokument

**Files:**
- Modify: `docs/latex/04_Architekturdokument/kapitel/01_Technologieuebersicht.tex`, `02_Architekturuebersicht.tex`, `03_Struktur.tex`, `04_Verhalten.tex`, ggf. `Architekturdokument.tex` (Abkürzungen), `docs/latex/_gemeinsam/literatur.bib` (PySide6, SQLite, pytest, PyInstaller als `@software`/`@online`, wenn sie zitiert werden)
- Create: `docs/diagramme/04_Klassendiagramm_Architektur/architektur_uebersicht.tex`, `docs/diagramme/04_Klassendiagramm_Architektur/klassendiagramm.tex`, `docs/diagramme/05_Sequenzdiagramm/sequenz.tex`

- [ ] **Step 1: Technologieübersicht.** Hinführung, Python 3.12 (Begründung), Tabelle `tab:bibliotheken` mit PySide6 (installierte Version aus Task 1, LGPLv3), pytest, pytest-cov, pytest-qt, ruff und PyInstaller jeweils mit Version, Lizenz, Zweck und Begründung, dazu `sqlite3` als Standardbibliothek. Abgewogene Alternativen: Tkinter, PyQt6 (GPL), Web/Electron, QtCharts, matplotlib. Entwicklungswerkzeuge mit VS Code, Git/GitHub, LaTeX/TikZ und **Claude Code (KI-Werkzeug, siehe Projektdokumentation)**. Alle `\TODO` entfernen.
- [ ] **Step 2: Architekturübersicht.** Schichtenarchitektur mit Fachliteratur begründen (`sommerville2016`, `swebok2026`), Alternativen MVVM/QML und hexagonal knapp abwägen (aus dem Design, Abschnitt 4). Grafik `architektur_uebersicht.tex` (vier Schichten mit Paketnamen, Abhängigkeitspfeile nach unten, SQLite-Datei und Exportdateien als Artefakte). Abschnitt „Änderungen gegenüber der Konzeptionsphase“: NFA12 neu, NFA-Prüfkriterien geschärft, Zeichengrenze der Wochenreflexion vereinheitlicht (1.000 Zeichen), Wochenansicht mit Zeile „ohne Uhrzeit“, Bearbeiten ganzer Serien über ein Kontrollkästchen, Sprung zur Vorwoche nach dem Laden der Demodaten. Dazu der Verweis auf die Änderungstabelle der Projektdokumentation. Gibt es Technical Debt (z. B. gekürzte I5-Funktionen), steht sie hier.
- [ ] **Step 3: Struktur.** Hauptklassen je Schicht mit Aufgabe, Attributen und Methoden. Das UML-Klassendiagramm `klassendiagramm.tex` mit `iu-diagramm.sty` wird **aus dem eingefrorenen Code** abgelesen: Pakete als UML-Pakete, wichtigste Klassen (Hauptfenster, Seite, DashboardSeite, AktivitaetDialog, AppKontext, die Services, Repositories, Datenbank, Domänenklassen und Funktionsmodule als `«module»`), Abhängigkeiten gestrichelt, Assoziationen mit Multiplizitäten. Sichtbarkeiten und Typen entsprechen dem Code. Prüfung: Jeder Name im Diagramm kommt im Code vor (`grep`).
- [ ] **Step 4: Verhalten.** Sequenzdiagramm `sequenz.tex` für „Aktivität speichern → Dashboard aktualisiert sich“: Nutzer:in → `AktivitaetDialog` → `AktivitaetService.speichern` → `validierung.pruefe_aktivitaet` → `Datenbank.transaktion` / `AktivitaetRepository.speichern` → Rückgabe → `Zustand.daten_geaendert` → `DashboardSeite.aktualisieren` → `AuswertungService.wochenbewertung`/`hinweise` → `bewertung.bewerte_woche` / `regeln.pruefe_regeln` → Anzeige. Dazu ein `alt`-Fragment für „Eingaben ungültig“ (`ValidierungsFehler` → Meldung am Feld). Die Notation folgt UML 2.5.1 (`omg2017uml`). Im Text werden Auslöser, beteiligte Objekte, Nachrichten und Ergebnis beschrieben.
- [ ] **Step 5: Humanizer** auf alle neuen Absätze anwenden.
- [ ] **Step 6: Bauen.** `python tools/build_docs.py --phase 2`. Erwartet: `[OK] Architekturdokument`, keine `\TODO`, keine fehlenden Grafiken, keine undefinierten Zitate. Die PNG-Ansicht der Diagramme auf Überlappungen prüfen (`pdftoppm -png -r 80 docs/diagramme/export/klassendiagramm.pdf <scratchpad>/kd` und das Bild ansehen).
- [ ] **Step 7: Commit.** `"Architekturdokument: Technologie, Architektur, Klassen- und Sequenzdiagramm"`

### Task 19: Feedback aus Phase 1 einarbeiten, Projektdokumentation ergänzen

**Files:**
- Modify: `docs/latex/01_Projektdokumentation/kapitel/01_Projektuebersicht.tex`, `03_Zeitplanung.tex`, `04_Versionsverwaltung.tex`, `docs/latex/02_Anforderungsdokument/kapitel/01_Einleitung.tex`, `04_NichtfunktionaleAnforderungen.tex`, `docs/latex/03_Spezifikationsdokument/kapitel/01_Datenmodell.tex` (und weitere Kapitel, falls dort Wiederholungen stehen), `CHECKLISTE.md` (Punkt „privat stellen“ entfällt)

- [ ] **Step 1: Projektfrage** in `01_Projektuebersicht.tex` als eigener, hervorgehobener Absatz nach der Zielsetzung: „Wie lässt sich eine Desktop-Anwendung gestalten, die die Wochenbalance über Lebensbereiche transparent und modellbasiert auswertet, ohne fehlende Einträge als schlechte Balance zu werten?“ Kurz zeigen, welche Teile der Arbeit welchen Teil der Frage beantworten. Das Anforderungsdokument verweist nur darauf.
- [ ] **Step 2: NFAs schärfen** in `04_NichtfunktionaleAnforderungen.tex`: NFA01 „mindestens 4 von 5 Testpersonen erfassen ohne Anleitung ihre erste Aktivität in höchstens 2 Minuten“ · NFA02 „100 % der Zeilen der Validierungstabelle sind durch Testfälle abgedeckt und bestanden“ · NFA04 „0 verlorene bestätigte Änderungen in 10 Abbruchversuchen“ · NFA08 „0 Befunde von `ruff check`, Docstrings für 100 % der öffentlichen Module, Klassen und Methoden“ · NFA10 „CSV öffnet in Excel ohne Umlautfehler mit 16 Spalten; JSON ist laut `json.loads` gültig“ · NFA11 „10 von 10 Regeln liefern alle neun Begründungsangaben“. Neue Zeile **NFA12 Skalierbarkeit**: „Die Anwendung bleibt bei wachsendem Datenbestand nutzbar“, Prüfkriterium „Bei 30.000 Aktivitäten (etwa zehn Jahre) dauern Dashboard und Statistik je höchstens 2 s; die Datenbankdatei bleibt unter 50 MB.“ Absatz unter der Tabelle ergänzen und Zählungen anpassen (die Kurzzusammenfassung von Phase 1 bleibt unverändert; im Text heißt es jetzt „12 nichtfunktionale Anforderungen“, mit `grep -rn "11 nichtfunktionale\|elf nichtfunktionale" docs/latex` suchen).
- [ ] **Step 3: Wiederholungen abbauen.** Projektübersicht, `02_Anforderungsdokument/kapitel/01_Einleitung.tex` und den Einleitungstext des Spezifikationsdokuments vergleichen. Die ausführliche Problemstellung bleibt nur in der Projektdokumentation, die anderen Dokumente bekommen höchstens drei Sätze mit Verweis. Das Ergebnis sind spürbar weniger Seiten in Anf und Spez; die Seitenzahlen vorher und nachher notieren.
- [ ] **Step 4: Theorie und Entscheidung trennen.** Wo ein Absatz ein Modell erklärt und daraus eine Projektentscheidung ableitet (vor allem Vorgehensmodell in `01_Projektuebersicht.tex`, Regelableitung in Spez Kap. 2.3), in zwei Teile gliedern: „Grundlagen“ (Theorie mit Quelle) und „Entscheidung für BalanceOS“ (als `\paragraph` oder als eigene Unterabschnitte).
- [ ] **Step 5: Datenmodell korrigieren:** Wochenreflexion `antworten` „höchstens 1.000 Zeichen“, in Übereinstimmung mit `tab:validierung` und dem Code.
- [ ] **Step 6: KI-Hinweis** als Unterabschnitt „Hinweis zum Einsatz von KI-Werkzeugen“ im Abschnitt Vorgehensmodell und Werkzeuge, etwa so: „Bei der Erstellung dieses Projekts wurde das KI-Werkzeug Claude Code (Anthropic) eingesetzt, und zwar für Quellcode und automatisierte Tests, TikZ-Diagramme sowie Entwürfe und sprachliche Überarbeitung der Dokumente. Der Einsatz von KI wurde vorab mit der Hochschule abgestimmt. Konzept, fachliche Entscheidungen, Prüfung und Freigabe aller Ergebnisse liegen beim Autor. KI-Ausgaben werden nicht als Quelle zitiert.“ Die Werkzeugliste um Claude Code ergänzen.
- [ ] **Step 7: Versionsverwaltung** in `04_Versionsverwaltung.tex`: Hinführung. Das Repository ist öffentlich und ohne Einladung für Tutor:innen erreichbar. Dazu die Ordnerstruktur (`app/`, `docs/`, `abgabe/`, `tools/`) und die Konventionen (Zweig `phase2` mit Zusammenführung in `main`, Tags `phase1-abgabe`/`phase2-abgabe`, deutsche Commit-Nachrichten je Inkrement, Kennzeichnung KI-gestützter Commits mit `Co-Authored-By`). Alle `\TODO` entfernen.
- [ ] **Step 8: Soll-Ist im Zeitplan:** kurzer Unterabschnitt „Fortschrittskontrolle zu M2“. Ein Satz gibt den Plan wieder: AP4 ab 13.11. und AP6 ab 16.11. Dann der Ist-Stand: Beginn am 23.11. nach dem Eingang des Feedbacks. Gegenmaßnahme laut RI02: Architektur und Implementierung wurden verdichtet und die Reserve genutzt; I1–I5 wurden in der Woche vom 23. bis 27.11. umgesetzt, M2 wurde gehalten bzw. nicht gehalten (nach Stand ausfüllen). Die ausführliche Reflexion folgt im Abstract.
- [ ] **Step 9: Änderungstabelle** „Änderungen gegenüber Portfolioteil 1“ als eigener Abschnitt am Ende der Projektdokumentation (vor dem Anhang) mit den Spalten Feedbackpunkt bzw. Anlass, Änderung, Dokument und Abschnitt. Sie enthält alle Punkte aus den Schritten 1–7 und die Änderungen aus Task 18, Step 2. Limitationen, kritische Bewertung und Fazit stehen dort als „folgt in Phase 3“.
- [ ] **Step 10: Humanizer** auf alle geänderten Absätze anwenden, lange Sätze straffen.
- [ ] **Step 11: Bauen.** `python tools/build_docs.py --phase 2`. Erwartet: alle vier Dokumente `[OK]`. Danach die Seiten mit dem neuen Inhalt als PNG ansehen.
- [ ] **Step 12: Commit.** `"Phase-1-Feedback eingearbeitet: Projektfrage, NFA12, geschärfte Prüfkriterien, gestrafft"`

### Task 20: Kurzzusammenfassung, Abgabe-PDF, Zusammenführung und Tag

**Files:**
- Modify: `abgabe/Phase2_Erarbeitung/Kurzzusammenfassung.md`

- [ ] **Step 1: Kurzzusammenfassung** unter „## Text“ schreiben, höchstens 200 Wörter. Inhalt: Architekturwahl und Grund, Technologien, drei wichtigste Implementierungsentscheidungen (Domäne ohne Qt, berechnete statt gespeicherte Bewertung, eigene Diagramme mit QPainter), Feedback aus Phase 1, Stand gegenüber dem Plan und Repo-Link. Danach Humanizer und eine Wortzählung (`python -c` mit `len(text.split())`). Erwartet: ≤ 200.
- [ ] **Step 2: Abschlussprüfung Code.** `cd app && pytest && ruff check .`. Erwartet: grün.
- [ ] **Step 3: Abgabe-PDF.** `python tools/build_docs.py --phase 2 --abgabe`. Erwartet: `abgabe/Phase2_Erarbeitung/Siebert-Can_IU14141164_PSE_P2_Abgabe.pdf` mit Projektdokumentation (Repo-Link und Quellcode-Anhang), Anforderungs-, Spezifikations- und Architekturdokument, alle `[OK]`. Deckblatt und Inhaltsverzeichnis als PNG prüfen.
- [ ] **Step 4: Commit.** `"Phase 2: Kurzzusammenfassung und Abgabe-PDF"`
- [ ] **Step 5: Zusammenführen, Tag, Push.** `git switch main && git merge --ff-only phase2 && git tag phase2-abgabe && git push origin main phase2 phase2-abgabe`. Erwartet: Der Push gelingt, und `git status` zeigt einen sauberen Stand.
- [ ] **Step 6: Übergabe an die Nutzerin bzw. den Nutzer:** den Pfad der PDF und den Kurzzusammenfassungstext für PebblePad nennen. Der Upload in PebblePad bleibt manuell.
