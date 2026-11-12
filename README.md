# BalanceOS: Work-Life-Balance-App für Windows

Portfolio im Kurs **Projekt: Software Engineering (DLMCSPSE01_D)**, IU Internationale Hochschule.
BalanceOS ist eine lokal laufende Windows-Desktopanwendung in Python. Sie vergleicht den eigenen
Alltag über Lebensbereiche hinweg mit persönlichen Wünschen und wissenschaftlich begründeten
Richtwerten. Daraus entstehen transparente, regelbasierte Hinweise, ganz ohne KI.

> Projektstand: **Phase 1 (Konzeptionsphase)**. Die Implementierung beginnt erst nach Einreichung
> von Portfolioteil 1 (siehe [`CHECKLISTE.md`](CHECKLISTE.md)).

## Ordnerstruktur

```
├── app/                         Anwendung (ab Phase 2): Quellcode, Tests, Testdaten, release/ (.exe)
├── docs/
│   ├── konzept/                 Ideenskizze und überarbeitetes Konzept (Arbeitsgrundlage, keine Abgabe)
│   ├── latex/                   Quellen der sechs Portfolio-Dokumente (LaTeX)
│   │   ├── _gemeinsam/          iu-pse.cls (IU-Formalia), meta.tex (Name, Daten), literatur.bib
│   │   ├── 01_Projektdokumentation/
│   │   ├── 02_Anforderungsdokument/
│   │   ├── 03_Spezifikationsdokument/
│   │   ├── 04_Architekturdokument/
│   │   ├── 05_Testdokument/
│   │   └── 06_Abstract/
│   ├── diagramme/               draw.io-Quellen (UML, Mock-ups) und export/ (PDF für LaTeX)
│   ├── bilder/                  Screenshots der Anwendung
│   └── pdf/                     aktuell gebaute Einzeldokumente
├── abgabe/                      eingereichte Fassungen je Phase (PebblePad) und Kurzzusammenfassungen
├── tools/build_docs.py          baut alle Dokumente, prüft Formalia, erzeugt Abgabe-PDFs und ZIP
├── CHECKLISTE.md                alle Vorgaben der IU mit Ort der Umsetzung
└── Vorgaben/                    IU-PDFs (lokal, per .gitignore ausgeschlossen, Urheberrecht der IU)
```

## Dokumente bauen

Voraussetzungen: MiKTeX (LuaLaTeX, Biber, latexmk), Python 3.12 oder neuer, Git. Die Schrift Arial
ist unter Windows vorhanden.

```powershell
python tools/build_docs.py                        # Phase 1: Projekt-, Anforderungs-, Spezifikationsdokument
python tools/build_docs.py --phase 2              # zusätzlich Architekturdokument, GitHub-Link, Quellcode-Anhang
python tools/build_docs.py --phase 3              # alle sechs Dokumente inkl. Testdokument und Abstract
python tools/build_docs.py --doc Abstract --phase 3   # nur ein Dokument
python tools/build_docs.py --phase 1 --abgabe     # Abgabe-PDF mit IU-Dateinamen nach abgabe/
```

Das Skript meldet je Dokument:
- offene `\TODO`
- fehlende Diagramme (Platzhalter)
- LaTeX-Fehler
- ob ein Abbildungs- oder Tabellenverzeichnis nötig ist (Pflicht ab drei Einträgen)
- beim Abstract, ob der Textteil genau zwei Seiten hat

In VS Code mit *LaTeX Workshop* baut jedes Dokument beim Speichern (Konfiguration in `.vscode/`).

## Schreiben in LaTeX: die wichtigsten Befehle

| Zweck | Befehl |
|---|---|
| Zitat (immer mit Seite, IU-Regel) | `\parencite[S.~12]{matuska2008}` → (Matuska & Christiansen, 2008, S. 12) |
| Autor:in im Satz | `\textcite[S.~12]{matuska2008}` |
| Abbildung | `\begin{figure}[H] \caption{Titel} \grafik{usecase} \quelle{Eigene Darstellung.} \end{figure}` |
| Tabelle | `longtable` mit `\caption{…}` oben, danach `\quelle{…}` (Vorlagen in den Kapiteln) |
| Abkürzung | in `abkuerzungen` definieren, im Text `\ac{GUI}` |
| Anhang | `\anhang` und danach `\anhangsteil{Titel}` → „Anhang A: Titel“ |
| offene Stelle | `\TODO{…}` (das Skript zählt sie) |

## Repository

https://github.com/cansi798/Projekt_SoftwareEngineering
