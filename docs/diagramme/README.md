# Diagramme und Mock-ups

Werkzeug: **TikZ** (LaTeX). Die Aufgabenstellung empfiehlt „ein geeignetes Modellierungstool,
z. B. Visio, draw.io oder Dia“; TikZ erfüllt diesen Zweck und hat zwei Vorteile: Die Diagramme
sind versionierbarer Quelltext und verwenden dieselbe Schrift wie die Dokumente.

- Quelldatei: `<Unterordner>/<name>.tex` (Gerüst: `\documentclass[tikz,border=4pt]{standalone}`
  und `\usepackage{iu-diagramm}`).
- Gemeinsame UML-Stile: `_vorlage/iu-diagramm.sty` (Use Case, Klasse, Aktivität, Zustand, Mock-up).
- `python tools/build_docs.py` übersetzt geänderte Diagramme automatisch nach `export/<name>.pdf`
  (Vektorgrafik); `--diagramme` erzwingt eine Neuübersetzung aller Diagramme.
- Fehlt eine Grafik, zeigt das PDF einen gerahmten Platzhalter und das Build-Skript meldet ihn.
- draw.io bleibt möglich: Export als PDF unter dem erwarteten Namen nach `export/` legen.

| Ordner | Diagramm | Exportname | Verwendet in |
|---|---|---|---|
| `01_UseCase/` | UML-Use-Case-Diagramm | `export/usecase.pdf` | Anforderungsdokument 3.2 |
| `02_Klassendiagramm_Datenmodell/` | UML-Klassendiagramm (fachlich) | `export/datenmodell.pdf` | Spezifikation 1.2 |
| `03_Aktivitaetsdiagramm/` | UML-Aktivitätsdiagramm (Kernprozess) | `export/aktivitaet.pdf` | Spezifikation 2.2 |
| `04_Klassendiagramm_Architektur/` | UML-Klassendiagramm (technisch) | `export/klassendiagramm.pdf` | Architektur 3.2 |
| `04_Klassendiagramm_Architektur/` | Architekturübersicht | `export/architektur_uebersicht.pdf` | Architektur 2.2 |
| `05_Sequenzdiagramm/` | UML-Sequenzdiagramm | `export/sequenz.pdf` | Architektur 4.2 |
| `06_Mockups/` | Mock-up Hauptfenster | `export/mockup_hauptfenster.pdf` | Spezifikation 5.1 |
| `06_Mockups/` | Mock-up Dialog „Aktivität erfassen“ | `export/mockup_aktivitaet.pdf` | Spezifikation 5.3.1 |
| `06_Mockups/` | Mock-up Begründungsdialog | `export/mockup_begruendung.pdf` | Spezifikation 5.3.2 |
| `06_Mockups/` | Mock-up Wochenansicht | `export/mockup_woche.pdf` | Spezifikation 5.3.3 |
| `06_Mockups/` | Dialogfluss (UML-Zustandsdiagramm) | `export/dialogfluss.pdf` | Spezifikation 5.4 |
| `07_Projektmanagement/` | Risikomatrix | `export/risikomatrix.pdf` | Projektdokumentation 2.3 |
| `07_Projektmanagement/` | Zeitplan (Gantt) | `export/zeitplan.pdf` | Projektdokumentation 3.4 |

## Regeln

- Die UML-Notation muss korrekt sein (UML 2.5.1), denn die Bewertung fragt: „Sind die erstellten
  UML-Diagramme korrekt und fehlerfrei?“
- Diagramm und Text müssen dieselben IDs und Begriffe verwenden, also User Stories, Klassennamen
  und Glossar.
- Unter jedem Diagramm steht `Quelle: Eigene Darstellung.`. Für nachgebaute Diagramme gilt
  `Eigene Darstellung in Anlehnung an …` (Zitierleitfaden Kap. 2.2.5).
- Statt Screenshots fremder Abbildungen solltest du die Abbildung nachbauen.
- Screenshots der eigenen App gehören nach `docs/bilder/`.
