# Diagramme und Mock-ups

Werkzeug: **draw.io** (diagrams.net, Desktop-App oder VS-Code-Erweiterung). Die IU empfiehlt es.
Die Quelldateien (`.drawio`) liegen im jeweiligen Unterordner. Exportiert wird als
**PDF (Vektorgrafik)** nach `export/`, unter genau dem Dateinamen, den das LaTeX-Dokument
erwartet. Fehlt eine Datei, zeigt das PDF einen gerahmten Platzhalter und das Build-Skript
meldet ihn.

| Ordner | Diagramm | Exportname | Verwendet in |
|---|---|---|---|
| `01_UseCase/` | UML-Use-Case-Diagramm | `export/usecase.pdf` | Anforderungsdokument 3.2 |
| `02_Klassendiagramm_Datenmodell/` | UML-Klassendiagramm (fachlich) | `export/datenmodell.pdf` | Spezifikation 1.2 |
| `03_Aktivitaetsdiagramm/` | UML-Aktivitätsdiagramm (Kernprozess) | `export/aktivitaet.pdf` | Spezifikation 2.2 |
| `04_Klassendiagramm_Architektur/` | UML-Klassendiagramm (technisch) | `export/klassendiagramm.pdf` | Architektur 3.2 |
| `04_Klassendiagramm_Architektur/` | Architekturübersicht | `export/architektur_uebersicht.pdf` | Architektur 2.2 |
| `05_Sequenzdiagramm/` | UML-Sequenzdiagramm | `export/sequenz.pdf` | Architektur 4.2 |
| `06_Mockups/` | Mock-up Hauptfenster | `export/mockup_hauptfenster.pdf` | Spezifikation 5.1 |
| `06_Mockups/` | Dialogfluss | `export/dialogfluss.pdf` | Spezifikation 5.2 |
| (frei) | Risikomatrix | `export/risikomatrix.pdf` | Projektdokumentation 2.3 |
| (frei) | Zeitplan (Gantt) | `export/zeitplan.pdf` | Projektdokumentation 3.4 |

## Regeln

- Die UML-Notation muss korrekt sein (UML 2.5.1), denn die Bewertung fragt: „Sind die erstellten
  UML-Diagramme korrekt und fehlerfrei?“
- Diagramm und Text müssen dieselben IDs und Begriffe verwenden, also User Stories, Klassennamen
  und Glossar.
- Unter jedem Diagramm steht `Quelle: Eigene Darstellung.`. Für nachgebaute Diagramme gilt
  `Eigene Darstellung in Anlehnung an …` (Zitierleitfaden Kap. 2.2.5).
- Statt Screenshots fremder Abbildungen solltest du die Abbildung nachbauen.
- Screenshots der eigenen App gehören nach `docs/bilder/`.
