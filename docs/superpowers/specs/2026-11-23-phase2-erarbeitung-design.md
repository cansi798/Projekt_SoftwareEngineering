# Design: Phase 2 (Erarbeitung und Reflexion) für BalanceOS

Stand: 23.11.2026 · Abgabe Portfolioteil 2 (Meilenstein M2): 30.11.2026

## 1 Absicht und Warum

Portfolioteil 2 des IU-Kurses DLMCSPSE01_D soll abgabefertig werden. Die Tutorin oder der Tutor bewertet in dieser Phase Architektur, Implementierung und die eingearbeitete Rückmeldung zu Phase 1. Die App BalanceOS ist bisher nur spezifiziert (Phase 1, Tag `phase1-abgabe`). Code gibt es noch nicht.

Die Nutzerin bzw. der Nutzer hat entschieden:
- **Umfang A:** Alle 22 User Stories (US01–US22, Must und Should) werden bis M2 umgesetzt, also die Inkremente I1–I5 wie im Zeitplan geplant.
- **Architektur Variante 1:** Schichtenarchitektur mit PySide6-Widgets (siehe Abschnitt 4).

Erfolg bedeutet: Am 30.11.2026 liegen in PebblePad (1) die Kurzzusammenfassung und (2) ein PDF mit Projektdokumentation (inklusive Repo-Link), Anforderungs-, Spezifikations- und Architekturdokument. Auf GitHub liegt eine lauffähige App, die alle Must- und Should-Funktionen der Spezifikation erfüllt.

## 2 Ziele, Nicht-Ziele, Anti-Ziele

**Ziele**
1. Lauffähige Windows-Desktop-App in Python 3.12 mit PySide6 und SQLite, die US01–US22 nach Spezifikation umsetzt (Geschäftsregeln GR01–GR30, Prozesse GP01–GP09, Regeln R01–R10, Validierungstabelle, Dialogfluss).
2. Architekturdokument vollständig: Technologieübersicht, Architekturübersicht, Struktur (UML-Klassendiagramm), Verhalten (UML-Sequenzdiagramm).
3. Phase-1-Feedback einarbeiten (Abschnitt 6) und die Änderungen nachvollziehbar dokumentieren.
4. Projektdokumentation mit Repo-Link, Repository-Kapitel und ehrlichem Soll-Ist-Stand des Zeitplans.
5. Kurzzusammenfassung Phase 2 (etwa eine halbe DIN-A4-Seite) und Abgabe-PDF über `python tools/build_docs.py --phase 2 --abgabe`.

**Nicht-Ziele (Phase 3)**
- Testdokument (Teststrategie, Testprotokoll), Benutzeranleitung, Abstract, Limitationen, kritische Bewertung, Fazit. Der Tutor hat Limitationen und Fazit ausdrücklich für die Finalisierung vorgesehen.
- Finale Auslieferung der `.exe` (AP9). In Phase 2 wird nur ein Probebuild gemacht (siehe 5.6).
- Could- und Won't-Funktionen aus dem Anforderungsdokument.

**Anti-Ziele (wäre ein Fehlschlag, selbst wenn es technisch läuft)**
- Code, der von der Spezifikation abweicht, ohne dass die Abweichung im Architekturdokument (Abschnitt „Änderungen gegenüber der Konzeptionsphase“) begründet ist.
- Rückdatierte Commits oder geschönte Zeitangaben. Die Verzögerung (AP4/AP6 sollten am 13. bzw. 16.11. beginnen, Start ist der 23.11.) wird offen dokumentiert, weil die Einhaltung des Zeitplans bewertet und in Phase 3 reflektiert wird.
- Ein Klassendiagramm oder Sequenzdiagramm, das nicht zum tatsächlichen Code passt.
- Fremder Quellcode in der App (verboten laut Aufgabenstellung).
- Dateien aus `Vorgaben/` im Repository (Urheberrecht der IU).
- KI-Funktionen, Netzwerkzugriffe oder Telemetrie (Won't, GR30, NFA05).
- Phase-1-Abgabe-PDF überschreiben. `build_docs.py` schützt das bereits über den Tag `phase1-abgabe`.

## 3 Rahmenbedingungen

- Aufgabenstellung IU, Abschnitt 1.2: Architekturdokument mit den vier Punkten, Code-Qualität und Kommentare, GitHub-Repo mit Link in der Projektdokumentation. Änderungen an Anforderungen und Spezifikation sind erlaubt, müssen aber begründet und dokumentiert werden.
- Formalia: `CHECKLISTE.md`, LaTeX-Klasse `docs/latex/_gemeinsam/iu-pse.cls`, APA 7 über biblatex, Diagramme in TikZ mit `iu-diagramm.sty`.
- Third-Party-Bibliotheken nur mit Version, Lizenz, Zweck und Begründung in Tabelle `tab:bibliotheken`. Alles außer dem Python-Interpreter wird in Phase 3 mitgeliefert.
- Bereits in Phase 1 festgelegt: Python 3.12, PySide6, VS Code, LaTeX/TikZ, GitHub, Datenablage in `%APPDATA%\BalanceOS`, deutschsprachige Oberfläche, Mindestfenstergröße 1.280 × 720, Navigation über eine Seitenleiste mit sieben Seiten.
- Python 3.12.10 ist installiert, PySide6 noch nicht.
- Prosa in den Dokumenten wird mit dem Skill `humanizer:humanizer` überarbeitet (Vorgabe der Nutzerin bzw. des Nutzers). Fachbegriffe, Zahlen und Quellen bleiben dabei unverändert.
- GitHub-Push funktioniert seit 23.11.2026 (neuer Token im gh-Keyring). Das Repo ist derzeit öffentlich.

## 4 Ansätze (Architektur)

| Ansatz | Vorteile | Nachteile |
|---|---|---|
| **1. Schichtenarchitektur mit Qt Widgets (gewählt)** | Fachlogik ohne Qt testbar (NFA06, NFA07); Muster in der Literatur gut belegt; passt eins zu eins zu den Mock-ups; Standard-Widgets mindern RI04 | etwas mehr Klassen und Durchreichen |
| 2. MVVM mit QML | moderne, deklarative Oberfläche | zweite Sprache, höheres Risiko RI04, Mock-ups neu denken, aufwendigere Paketierung |
| 3. Hexagonal (Ports und Adapter) | maximale Entkopplung | für eine Offline-App mit einem Speicher überdimensioniert, schwerer zu begründen |

Gewählt wurde Ansatz 1 von der Nutzerin bzw. dem Nutzer, weil er zur Phase-1-Planung passt und die Tests in Phase 3 am einfachsten macht.

## 5 Entscheidungen zum Wie

Entscheidungen der Nutzerin bzw. des Nutzers: Umfang A, Ansatz 1. Alle übrigen Punkte in diesem Abschnitt sind **Vorschläge des Assistenten** und als solche gekennzeichnet.

### 5.1 Schichten (Ansatz 1, Zuschnitt: Assistent)

Abhängigkeiten zeigen nur nach unten. Die Domäne kennt weder Qt noch SQLite.

```
praesentation/   PySide6: Hauptfenster, Seitenleiste, 7 Seiten, Dialoge, eigene Diagramm-Widgets
anwendung/       Services (Anwendungsfälle), Transaktionsgrenze, DTOs für die Oberfläche
domaene/         Entitäten, Aufzählungen, Validierung (GR01–GR30), Bewertung (GP03, GP05),
                 Regelwerk (R01–R10), Serienauflösung (GP02), WHO-5 (GP06), ISO-Woche
persistenz/      sqlite3 aus der Standardbibliothek, Schema und Migration, Repositories, Seed-Daten
```

- Bezeichner sind deutsch und ohne Umlaute, passend zum Datenmodell der Spezifikation (`Lebensbereich`, `Aktivitaet`, `Wiederholungsserie` …). *(Assistent: Das Datenmodell definiert diese Namen bereits für Export und Doku.)*
- Repository-Muster mit einer Klasse pro Aggregat. Die Services erhalten die Repositories per Konstruktor (Dependency Injection von Hand, ohne Framework), damit Integrationstests mit einer In-Memory-Datenbank laufen.
- Die Wochenbewertung wird nicht gespeichert, sondern bei jeder Anzeige neu berechnet (so steht es im Datenmodell). Ausgeblendete Hinweise werden gespeichert (GR24).
- Die Oberfläche spricht nur mit Services. Nach jeder Änderung meldet ein zentrales Qt-Signal `daten_geaendert`, dass die sichtbaren Seiten neu laden.

### 5.2 Technologien (Assistent)

| Komponente | Wahl | Grund |
|---|---|---|
| GUI | PySide6 (aktuelle 6.x, LGPLv3) | in Phase 1 festgelegt; offizielle Qt-Bindung; LGPL erlaubt die Auslieferung |
| Datenhaltung | `sqlite3` (Standardbibliothek) | transaktional (NFA04), keine Zusatzinstallation, eine Datei im Benutzerprofil |
| Diagramme | eigene Widgets mit `QPainter` | Soll-Ist-Balken und Liniendiagramm sind einfach; spart QtCharts bzw. matplotlib als Abhängigkeit und hält die `.exe` klein |
| Tests | pytest, pytest-cov, pytest-qt (nur für wenige GUI-Rauchtests) | Standard in Python; Abdeckung für NFA07 messbar |
| Statische Prüfung | ruff (Lint und Format nach PEP 8) | ein Werkzeug für NFA08 |
| Paketierung | PyInstaller (Probebuild in Phase 2) | verbreitet, erzeugt eine Windows-`.exe` ohne Python-Installation (NFA09) |

Laufzeitabhängigkeit ist **nur PySide6**. Alles andere wird nur für die Entwicklung gebraucht und steht in `pyproject.toml` unter `[project.optional-dependencies] dev`.

### 5.3 Repository-Struktur (Assistent, baut auf `app/README.md` auf)

```
app/
├── src/balanceos/{domaene,anwendung,persistenz,praesentation}/
├── src/balanceos/__main__.py     Start mit: python -m balanceos
├── src/balanceos/ressourcen/     Kompass-Texte, Demodaten-Generator, Symbole
├── tests/{unit,integration,gui}/
├── pyproject.toml
└── README.md                     Start, Tests, Build
```

### 5.4 Inkremente und Reihenfolge

Wie in der Projektdokumentation (Abschnitt `sec:vorgehen`) geplant:
I1 Grundgerüst → I2 Erfassen → I3 Auswerten → I4 Kompass/Daten → I5 Should.

**Rückfallplan (aus der Phase-1-Planung, RI01/RI02):** Wird es knapp, wird zuerst der Umfang von I5 gekürzt, nicht die Qualität der Must-Funktionen und nicht die Dokumente. Was aus I5 fehlt, wird im Architekturdokument als Technical Debt mit Plan für Phase 3 dokumentiert.

**Zeitachse (Assistent):** I1–I5 bis einschließlich 27.11., Code-Freeze am 28.11. Danach entstehen Klassen- und Sequenzdiagramm aus dem eingefrorenen Code. Am 28. und 29.11. werden Architekturdokument, Feedback-Überarbeitung, Projektdokumentation und Kurzzusammenfassung fertiggestellt, am 30.11. folgen Abgabe-PDF, Push und Tag `phase2-abgabe`. Die Feedback-Überarbeitung der Phase-1-Dokumente (Abschnitt 6) hängt nicht vom Code ab und kann parallel ab I1 laufen.

Jedes Inkrement endet mit grünen Tests, einem Commit und, sobald der Push wieder funktioniert, einem Push. Die Fachlogik (Bewertung, Regeln, Serien, Validierung) wird testgetrieben entwickelt. Die Rechenbeispiele 1–3 der Spezifikation sind die ersten Unit-Tests (NFA06). *(Assistent: Unit-Tests während der Implementierung sind Teil von AP6. Das formale Testdokument bleibt in Phase 3.)*

### 5.5 Demodaten (Assistent)

Ein deterministischer Generator (fester Zufallswert) erzeugt acht Wochen für die Persona Sarah Keller, die mit der aktuellen Woche enden. Die Daten sind so gewählt, dass jede Regel R01–R10 mindestens einmal auslöst und das Rechenbeispiel „Bewegung 65“ in einer Woche sichtbar wird. Alle Einträge haben `istDemo = wahr` (GR28).

### 5.6 Probebuild (Assistent)

Ein PyInstaller-Probebuild (`--onedir`, nicht eingecheckt) als Gegenmaßnahme zu RI05 aus Phase 1. So zeigt sich früh, ob PySide6 sauber paketiert wird. Die finale `.exe` und `release/` kommen in Phase 3.

### 5.7 Architekturdokument (Assistent)

- **Technologieübersicht:** Tabelle 5.2 mit Versionen und Lizenzen, abgewogene Alternativen (Tkinter, PyQt6, Electron/Web, QtCharts, matplotlib). Wenig bekannte Bibliotheken kommen ins Literaturverzeichnis.
- **Architekturübersicht:** Schichtenstil mit Fachliteratur begründet (zum Beispiel SWEBOK V4 oder Standardwerke zu Architekturmustern, die schon in `literatur.bib` stehen oder frei abrufbar sind), dazu eine TikZ-Übersichtsgrafik `architektur_uebersicht` und der Abschnitt „Änderungen gegenüber der Konzeptionsphase“.
- **Struktur:** UML-Klassendiagramm `klassendiagramm` mit den wichtigsten Klassen je Schicht, Attributen und Methoden. Es wird **nach** dem Code gezeichnet und mit ihm abgeglichen.
- **Verhalten:** UML-Sequenzdiagramm `sequenz` für „Aktivität speichern → Dashboard aktualisiert sich“ (Dialog → Service → Validierung → Repository/Transaktion → Signal → BewertungService → Regelwerk → Dashboard). Der Ablauf verbindet die zentralen Teile und ergänzt das Aktivitätsdiagramm aus Phase 1.

### 5.8 Projektdokumentation (Assistent)

- Kapitel „Versionsverwaltung und Repository“ ausfüllen: Link, Ordnerstruktur, Commit- und Tag-Konventionen, Zugang für die Tutorin oder den Tutor (siehe offene Punkte).
- In der Zeitplanung einen kurzen Soll-Ist-Vergleich ergänzen: Start von AP4/AP6 am 23.11. statt am 13./16.11. Dazu die Gegenmaßnahme laut Risikoplan (RI02), also Inkremente straffen und Reserve nutzen. Die ausführliche Reflexion folgt im Abstract (Phase 3).
- Eine Tabelle „Änderungen gegenüber Portfolioteil 1“ mit Feedbackpunkt, Änderung und Ort im Dokument. *(Assistent: Sie steht als eigener Abschnitt in der Projektdokumentation, denn Kapitel 6 „Anforderungserfüllung“ erscheint erst ab Phase 3. Abschnitt 2.3 des Architekturdokuments verweist darauf und begründet die technischen Änderungen.)*

### 5.9 Offenlegung des KI-Einsatzes (Entscheidung der Nutzerin bzw. des Nutzers)

Laut Nutzerin bzw. Nutzer hat die IU auf Nachfrage bestätigt, dass KI verwendet werden darf. Gewünscht ist ein Hinweis, dass KI verwendet wurde.
- In der Projektdokumentation steht ein kurzer Abschnitt „Hinweis zum Einsatz von KI-Werkzeugen“ beim Vorgehensmodell und den Werkzeugen. *(Platzierung: Assistent)* Er nennt das Werkzeug (Claude Code von Anthropic) und die Einsatzbereiche: Quellcode und Tests, TikZ-Diagramme, Entwürfe und sprachliche Überarbeitung der Dokumente. Außerdem hält er fest, dass Konzept, Entscheidungen, Prüfung und Freigabe bei der Autorin bzw. dem Autor liegen und dass KI-Ausgaben nicht als Quelle zitiert werden (Zitierleitfaden).
- Die Tabelle der Entwicklungswerkzeuge im Architekturdokument führt das Werkzeug ebenfalls auf.
- Die Commits tragen weiterhin die Zeile `Co-Authored-By` und sind damit im Repository nachvollziehbar.
- KI-generierter Code gilt nicht als „fremder Quellcode aus fremden Anwendungen“. Es wird trotzdem kein Code aus anderen Projekten übernommen.

## 6 Feedback aus Phase 1: Umsetzung jetzt

| Feedbackpunkt | Umsetzung (Assistent) |
|---|---|
| Explizite Forschungs- bzw. Projektfrage fehlt | In der Projektübersicht der Projektdokumentation eine Projektfrage formulieren. Sinngemäß: Wie lässt sich eine Desktop-Anwendung gestalten, die die Wochenbalance über Lebensbereiche transparent und modellbasiert auswertet, ohne fehlende Einträge als schlechte Balance zu werten? Das Anforderungsdokument verweist nur darauf. |
| NFAs quantifizierbarer machen | Jede NFA bekommt ein messbares Prüfkriterium: NFA01 mit Erfolgsquote/Zeit, NFA02 mit „100 % der Validierungsregeln getestet“, NFA08 mit „0 ruff-Befunde, Docstrings für alle öffentlichen Klassen und Methoden“, NFA10 mit konkreten Prüfschritten, NFA11 mit „10/10 Regeln vollständig“. |
| Ausdrückliche Skalierbarkeitsanforderung | Neue **NFA12 Skalierbarkeit**: Mit 10 Jahren Daten (etwa 30.000 Aktivitäten) braucht das Dashboard höchstens 2 s, die Statistik über acht Wochen höchstens 2 s, und die Datenbank bleibt unter 50 MB. Prüfung mit einem Lastdatensatz aus dem Demodaten-Generator. NFA03 bleibt für den Normalfall. |
| Wiederholungen zwischen den Dokumenten | Problemstellung, Vorgehen und Zielgruppe stehen ausführlich nur noch an einer Stelle (Projektdokumentation bzw. Anforderungsdokument). Die anderen Dokumente bekommen Kurzfassungen mit Verweis. |
| Theorie und Projektentscheidungen stärker trennen | Wo Modelle erklärt und gleich Entscheidungen abgeleitet werden, kommt eine sichtbare Gliederung: erst „Grundlagen“ (Theorie mit Quelle), dann „Entscheidung für BalanceOS“. Gilt vor allem für Vorgehensmodell, Kompass-Modelle und Regelableitung. |
| Längere Formulierungen straffen | Beim Überarbeiten mit Humanizer kürzen, ohne Inhalt, Zahlen und Quellen zu ändern. |
| Limitationen, kritische Bewertung, Fazit | **Phase 3**, so vom Tutor vorgesehen. |

Die NFA-Änderungen und NFA12 gelten als signifikante Änderung und werden in der Änderungstabelle (5.8) und im Architekturdokument begründet.

## 7 Kurzzusammenfassung Phase 2

`abgabe/Phase2_Erarbeitung/Kurzzusammenfassung.md`, höchstens 200 Wörter (PebblePad-Limit wie in Phase 1). Inhalt: Architekturwahl und Grund, Technologien, wichtigste Implementierungsentscheidungen (Domäne ohne Qt, berechnete statt gespeicherte Bewertung, QPainter-Diagramme), umgesetztes Feedback, Stand gegenüber dem Plan. Mit Humanizer überarbeitet.

## 8 Offen für die Nutzerin bzw. den Nutzer

1. ~~GitHub-Schreibrechte~~: erledigt am 23.11.2026. Neuer Token, Phase-1-Commits und Tag `phase1-abgabe` sind gepusht.
2. **Zugang (entschieden am 23.11.2026):** Das Repo bleibt öffentlich, damit die Tutorin oder der Tutor direkt über den Link zugreifen kann. Das Kapitel Versionsverwaltung beschreibt das so. Der Punkt der Checkliste „privat stellen“ entfällt. **Tutor-Name:** Kommt bis zum Bauen der PDF keine Angabe, entfällt die Zeile wie in Phase 1.

## 9 Dem Builder überlassen

- Genauer Klassenzuschnitt innerhalb der Schichten, Namen von Hilfsklassen, SQL-Schema im Detail (Tabellen müssen das Datenmodell abbilden).
- Aufteilung der Seiten in Widgets und Layout im Rahmen der Mock-ups.
- Formulierungen der Dokumente im Rahmen der Abschnitte 5.7, 5.8 und 6.
- Commit-Granularität innerhalb der Inkremente.

## 10 Referenzen im Repository

- Anforderungen: `docs/latex/02_Anforderungsdokument/kapitel/03_FunktionaleAnforderungen.tex`, `04_NichtfunktionaleAnforderungen.tex`
- Spezifikation: `docs/latex/03_Spezifikationsdokument/kapitel/01_Datenmodell.tex` … `05_Benutzerschnittstellen.tex` (Datenmodell, GP01–GP09, Formeln und Rechenbeispiele, R01–R10 mit Texten, GR01–GR30, CSV/JSON-Format, Dialoge, Validierungstabelle)
- Mock-ups und Dialogfluss: `docs/diagramme/06_Mockups/`
- Planung und Risiken: `docs/latex/01_Projektdokumentation/kapitel/01_Projektuebersicht.tex`, `02_Risikomanagement.tex`, `03_Zeitplanung.tex`
- Architektur-Gerüst: `docs/latex/04_Architekturdokument/kapitel/`
- Build: `tools/build_docs.py`, Formalia: `CHECKLISTE.md`
