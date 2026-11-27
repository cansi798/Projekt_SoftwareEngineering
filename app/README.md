# BalanceOS

BalanceOS ist eine Windows-Desktopanwendung zur Work-Life-Balance. Sie vergleicht die erfasste Zeit je Lebensbereich mit einem persönlichen Wunschprofil, bewertet jede Kalenderwoche mit einem Score und gibt regelbasierte Hinweise mit Quelle und Evidenzart. Alle Daten bleiben lokal in einer SQLite-Datei; die Anwendung baut keine Netzwerkverbindung auf.

Das Projekt entstand im Kurs DLMCSPSE01_D (Projekt: Software Engineering) der IU Internationale Hochschule. Anforderungen, Spezifikation und Architektur stehen im Ordner `docs/` des Repositorys.

## Voraussetzungen

- Windows 10 oder 11
- Python 3.12 oder neuer (getestet mit 3.12.10)
- PySide6 ab 6.8 (wird bei der Installation mitinstalliert)

## Installation

Im Ordner `app/`:

```
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

Ohne Entwicklungswerkzeuge genügt `pip install -e .`.

## Start

```
python -m balanceos
```

Nach der Installation startet auch der Befehl `balanceos` die Anwendung. Die Datenbank liegt unter `%APPDATA%\BalanceOS\balanceos.db` und wird beim ersten Start angelegt. Wer die Anwendung ausprobieren möchte, lädt auf dem Dashboard oder unter Einstellungen → Daten die Demodaten: acht Wochen aus dem Alltag der Persona Sarah Keller, in denen jede Regel R01 bis R10 mindestens einmal auslöst. Die Demodaten lassen sich dort auch wieder entfernen, ohne eigene Einträge zu berühren.

## Tests

```
pytest                          # Unit-, Integrations-, Oberflächen- und Systemtests
pytest -m leistung -v -s        # Lasttests (NFA03, NFA12) mit Messwerten
pytest --cov=balanceos          # mit Zeilenabdeckung
ruff check . && ruff format --check .
```

Die Oberflächentests laufen mit pytest-qt ohne sichtbare Fenster (`tests/conftest.py` setzt `QT_QPA_PLATFORM=offscreen`). Die Lasttests sind vom normalen Lauf ausgenommen und füllen eine Datenbank mit 3.000 bzw. 30.000 Aktivitäten.

## Ausführbare Datei (ohne Python)

`release/BalanceOS.exe` ist eine einzelne ausführbare Datei für Windows 10/11 (64 Bit). Sie enthält Python, PySide6 und die Anwendung; eine Installation ist nicht nötig. Doppelklick startet BalanceOS. Die exe ist nicht digital signiert, deshalb kann Windows SmartScreen beim ersten Start warnen („Weitere Informationen“ → „Trotzdem ausführen“). Lässt Windows den Start nicht zu, startet BalanceOS wie oben beschrieben mit `python -m balanceos`.

Neu bauen (im Ordner `app/`, mit installierten Entwicklungswerkzeugen):

```
pyinstaller balanceos.spec --distpath release --workpath build --noconfirm
```

Die Spezifikation lässt Qt-Teile weg, die BalanceOS nicht nutzt (Quick/QML, PDF, Netzwerk/TLS, Software-OpenGL). `build/` wird nicht eingecheckt.

## Ordnerstruktur

```
app/
├── src/balanceos/
│   ├── domaene/         Fachlogik ohne Qt und SQLite: Modell, Bewertung, Regeln, Validierung
│   ├── anwendung/       Services, Demodaten, Export und AppKontext (Verdrahtung)
│   ├── persistenz/      SQLite-Datenbank, Schema, Stammdaten und Repositories
│   └── praesentation/   PySide6-Oberfläche: Hauptfenster, Seiten, Dialoge, Widgets
├── tests/
│   ├── unit/            Domänenlogik, darunter die Rechenbeispiele der Spezifikation
│   ├── integration/     Services mit echter Datenbank, Export, Lasttests
│   ├── gui/             Seiten und Dialoge mit pytest-qt
│   └── system/          Systemtests: komplette Abläufe über die Oberfläche
├── release/           BalanceOS.exe (ausgelieferte Anwendung)
├── balanceos.spec       PyInstaller-Konfiguration für die exe
└── pyproject.toml       Abhängigkeiten, pytest- und ruff-Konfiguration
```

Die Schichten hängen nur in eine Richtung voneinander ab: Präsentation → Anwendung → Persistenz → Domäne, und die Anwendung nutzt zusätzlich die Domäne direkt. Ein Architekturtest prüft, dass die Domäne weder Qt noch SQLite importiert.

## Hinweis

BalanceOS ist kein Medizinprodukt und stellt keine Diagnosen. Scores und Schwellenwerte sind programmeigen und nicht validiert; das WHO-5-Ergebnis wird getrennt davon angezeigt.

Bei der Entwicklung wurde KI-Unterstützung (Claude, Anthropic) für Code, Tests und Textentwürfe genutzt. Alle Ergebnisse wurden geprüft und verantwortet.
