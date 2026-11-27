# Checkliste: alle Vorgaben der IU

Quellen (lokal in `Vorgaben/`, nicht im Repository):
- **[A]** Aufgabenstellung DLMCSPSE01_D
- **[P]** Prüfungsleitfaden Portfolio
- **[R]** Richtlinien für die Gestaltung wissenschaftlicher Arbeiten (Stand 01.10.2025)
- **[Z]** Allgemeiner Zitierleitfaden (Stand 01.10.2026)
- **[D]** Anleitung „Schriftliche Prüfungsleistungen mit Dateianlagen“

Legende: ⚙ = automatisch durch Vorlage oder Skript erfüllt · ☐ = von dir zu erledigen

---

## 0. Ablauf und kritische Regeln

- ☐ **Phasen strikt in der Reihenfolge bearbeiten und einreichen.** Ein Verstoß führt zu „nicht bestanden“ [P]. Kein Anwendungscode vor der Einreichung von Portfolioteil 1.
- ☐ Feedback der Tutor:innen abwarten (bis zu 7 Tage) und einarbeiten [P]. Online-Tutorien vor jeder Abgabe nutzen [A].
- ☐ Endergebnisse von Phase 1 und Phase 2 **separat speichern** und in Phase 3 erneut einreichen [P]. ⚙ `abgabe/` und Git-Tags `phase1-abgabe` und `phase2-abgabe`; das Skript verhindert ein Überschreiben.
- ☐ **Eidesstattliche Erklärung** elektronisch über myCampus abgeben. Vorher ist keine Einreichung möglich [A][P].
- ☐ Die eigenständige Erarbeitung ist Teil der Bewertung [A]. Die **KI-Richtlinie der IU** (myCampus) prüfen und einhalten [R][Z]. KI ist keine zitierfähige Quelle [Z].
- ☐ Keine Lösungen teilen (Plagiatsprüfung) [A]. Entschieden am 23.11.2026: Das GitHub-Repository **bleibt öffentlich**, damit die Tutor:in ohne Einladung zugreifen kann (Projektdokumentation, Kapitel Versionsverwaltung).
- ⚙ Die Aufgabenstellung wird nicht veröffentlicht (Urheberrecht der IU) [A]. `Vorgaben/` steht in `.gitignore`.

## 1. Anforderungen an die Anwendung [A]

- ☐ Windows-10/11-Desktopanwendung in Python (objektorientiert)
- ☐ Klar definierter **Kundennutzen** für eine definierte Zielgruppe → Projektdokumentation 1.2, Anforderungsdokument 2
- ✅ **Sinnvolle Testdaten**, damit der Nutzen sofort sichtbar wird → Demodaten über acht Wochen (`app/src/balanceos/anwendung/demodaten.py`), per Knopf in den Einstellungen
- ☐ **Kreativ und neu**, kein Nachbau → Projektdokumentation 1.3 (Abgrenzung), Konzept Kap. 3
- ☐ Funktionsfähig mit ausreichend Quellcode, kein Mock-up
- ☐ Selbsterklärende, intuitive GUI
- ☐ Alle FA und NFA umgesetzt, sonst als **Technical Debt** dokumentiert → Projektdokumentation 6.2
- ☐ Third-Party-Bibliotheken dokumentiert und begründet; kein kopierter Fremdcode → Architekturdokument 1.2
- ☐ Alles außer Standard-Laufzeitumgebungen ist beschrieben **und mitgeliefert** → Benutzeranleitung, `app/release/`
- ☐ GitHub enthält die lauffähige Anwendung, alle Dokumente, den Quellcode und alle Zusatzdateien
- ☐ Code ist gut strukturiert und verständlich kommentiert

## 2. Portfolioteil 1: Konzeptionsphase

| Inhalt | Ort | Status |
|---|---|---|
| Projektübersicht (Projekt und angestrebtes Ergebnis) | `01_Projektdokumentation/kapitel/01_Projektuebersicht.tex` | ☐ |
| Risikomanagement mit Bewertung nach Wahrscheinlichkeit × Schwere und Gegenmaßnahmen | `…/02_Risikomanagement.tex` | ☐ |
| Zeitplan mit Arbeitspaketen und Meilensteinen | `…/03_Zeitplanung.tex` | ☐ |
| Stakeholder und Zielgruppe | `02_Anforderungsdokument/kapitel/02_Stakeholder.tex` | ☐ |
| Funktionale Anforderungen als **User Stories** und **UML-Use-Case-Diagramm** | `…/03_FunktionaleAnforderungen.tex`, `docs/diagramme/01_UseCase/` | ☐ |
| Nichtfunktionale Anforderungen (Performance, Sicherheit, Usability …) | `…/04_NichtfunktionaleAnforderungen.tex` | ☐ |
| Glossar | `…/05_Glossar.tex` | ☐ |
| Datenmodell textuell und als **UML-Klassendiagramm** | `03_Spezifikationsdokument/kapitel/01_Datenmodell.tex` | ☐ |
| Geschäftsprozesse und ein Kernprozess als **UML-Aktivitätsdiagramm** | `…/02_Geschaeftsprozesse.tex` | ☐ |
| Geschäftsregeln | `…/03_Geschaeftsregeln.tex` | ☐ |
| Systemschnittstellen (Zweck, Protokoll, Format) | `…/04_Systemschnittstellen.tex` | ☐ |
| Benutzerschnittstellen: Dialoge, Mock-ups, Dialogfluss, Eingabevalidierung | `…/05_Benutzerschnittstellen.tex` | ☐ |

**Einreichung in PebblePad:**
1. ☐ Kurzzusammenfassung von ca. ½ DIN-A4-Seite im Textfeld → `abgabe/Phase1_Konzeption/Kurzzusammenfassung.md`
2. ☐ Eine PDF mit den drei Dokumenten, Name `Nachname-Vorname_Matrikelnummer_PSE_P1_Abgabe.pdf`. ⚙ `python tools/build_docs.py --phase 1 --abgabe`

## 3. Portfolioteil 2: Erarbeitungs- und Reflexionsphase

| Inhalt | Ort | Status |
|---|---|---|
| Technologieübersicht mit Begründung (Sprache, Frameworks, Bibliotheken) | `04_Architekturdokument/kapitel/01_Technologieuebersicht.tex` | ☐ |
| Architekturübersicht mit Begründung | `…/02_Architekturuebersicht.tex` | ☐ |
| Struktur als **UML-Klassendiagramm** (Attribute, Methoden, Beziehungen) | `…/03_Struktur.tex` | ☐ |
| Verhalten als **UML-Sequenzdiagramm** eines zentralen Ablaufs | `…/04_Verhalten.tex` | ☐ |
| Implementierung gemäß Anforderungen, Spezifikation und Architektur | `app/` | ☐ |
| **Link zum GitHub-Repository** in der Projektdokumentation | ⚙ `04_Versionsverwaltung.tex` (ab Phase 2 automatisch) | ⚙ |
| Signifikante Änderungen an Anforderungen und Spezifikation begründet | Architektur 2.3 und Projektdokumentation, Kapitel 7 | ☐ |

**Einreichung:**
1. ☐ Kurzzusammenfassung der Design- und Implementierungsentscheidungen (ca. ½ Seite)
2. ☐ Eine PDF aus Projektdokumentation (mit GitHub-Link), Anforderungs-, Spezifikations- und Architekturdokument, Name `…_PSE_P2_Abgabe.pdf`. ⚙ `--phase 2 --abgabe`

## 4. Portfolioteil 3: Finalisierungsphase

| Inhalt | Ort | Status |
|---|---|---|
| Teststrategie (Vorgehen, Unit-, Integrations- und Systemtests) | `05_Testdokument/kapitel/01_Teststrategie.tex` | ✅ |
| Testprotokoll je Testfall: ID, Kurzbeschreibung, Vorbedingungen, Eingaben/Aktionen, erwartetes und tatsächliches Ergebnis | ⚙ Makro `\testfall` in `02_Testprotokoll.tex` | ✅ |
| Optional: automatisierte Tests (pytest) | `app/tests/` | ✅ |
| **Benutzeranleitung** (Installation, Ausführung) in der Projektdokumentation | ⚙ `05_Benutzeranleitung.tex` (Phase 3) | ✅ |
| **Abstract**: 2 Seiten, Making-of und Reflexion inkl. Problemen und Zeitplantreue | `06_Abstract/Abstract.tex` | ✅ |
| Feedback aus Phase 1 und 2 umgesetzt | Projektdokumentation, Kapitel 7 (Tabellen je Phase) | ✅ |
| Limitationen, kritische Bewertung und Fazit (Feedback Phase 2) | `01_Projektdokumentation/kapitel/08_Fazit.tex` | ✅ |

**Einreichung (5 Teile):**
1. ☐ `…_PSE_P3_Abstract.pdf` (erzeugt am 27.11.2026 in `abgabe/Phase3_Finalisierung/`)
2. ☐ `…_PSE_P3_FinalesProdukt.pdf` mit allen 6 Dokumenten (erzeugt am 27.11.2026, 370 Seiten). ⚙ `--phase 3 --abgabe`
3. ☐ `…_PSE_P3_Abgabe.zip` mit **identischem** Inhalt wie das GitHub-Repository. ⚙ `--phase 3 --zip` prüft Commit und Push. **Danach keine Änderungen mehr am Repository.**
4. ☐ PDF aus Phase 1 erneut (eingefrorene Fassung)
5. ☐ PDF aus Phase 2 erneut (eingefrorene Fassung)

## 5. Formalia der Dokumente [R], ⚙ durch `iu-pse.cls`

- ⚙ DIN A4, alle Ränder 2,00 cm, Arial 11 pt, einfarbig schwarz, Blocksatz, Silbentrennung, Zeilenabstand 1,5
- ⚙ Absatz ohne Einzug mit 6 pt Abstand. Überschriften fett und linksbündig: 16, 14 und 11 pt. Abstände 12/12 bzw. 12/6 pt. Höchstens 3 Ebenen.
- ⚙ Fußnoten in Arial 10 pt, Blocksatz
- ⚙ Titelblatt nur mit den Pflichtangaben: Hochschule ausgeschrieben, Prüfungsform, Kurs, Studiengang ausgeschrieben, Titel, Name, Matrikelnummer, Tutor:in mit Titel, Abgabedatum → ☐ `meta.tex` ausfüllen
- ⚙ Seitenzahlen zentriert unten. Der Vorspann ist römisch nummeriert (Titelblatt = I, ohne Anzeige). Der Textteil beginnt arabisch bei 1 und läuft bis durch den Anhang.
- ⚙ Im Inhaltsverzeichnis ist nur Ebene 1 fett. Verzeichnisse sind nicht nummeriert.
- ⚙ Abbildungs- bzw. Tabellenverzeichnis ab je 3 Einträgen. Das Skript gibt dazu einen Hinweis.
- ⚙ Abkürzungsverzeichnis alphabetisch, nur verwendete Abkürzungen (`\ac{…}`), keine allgemein üblichen wie „z. B.“
- ⚙ Anhänge als „Anhang A: …“ mit Anhangsverzeichnis. ☐ Im Text mindestens einmal auf den Anhang verweisen.
- ☐ Kein „ich“, „wir“, „man“. Ausnahme: das Abstract, weil es selbstreflexiv ist.
- ☐ Jedes (Unter-)Kapitel umfasst mindestens ½ Seite. Unterteilen nur mit mindestens 2 Unterpunkten. Zwischen Kapitel und Unterkapitel stehen höchstens 2–3 Sätze Hinführung. Die Kapitelüberschrift wiederholt nicht den Titel.
- ☐ Keine Unterstreichungen; sparsam *kursiv* oder **fett**
- ☐ Keine Rechtschreib- und Grammatikfehler. Das zählt zu den Formalia (10 %).
- ☐ Gender-Hinweis optional (`\genderhinweis`)

**Abstract [A 4.3]:** ⚙ Klassenoption `abstract` setzt die Überschriften auf 12 pt. ☐ Genau 2 Seiten Textteil; das Skript prüft das.

## 6. Zitieren [Z], APA 7 mit IU-Abweichungen

- ⚙ Literaturverzeichnis nach APA 7 (biblatex-apa): linksbündig, Zeilenabstand 1,5, hängender Einzug 1,27 cm, ein gemeinsames Verzeichnis
- ☐ **Kurzbelege immer mit Seitenangabe**, auch bei indirekten Zitaten (IU strenger als APA): `\parencite[S.~12]{key}`
- ☐ Direkte Zitate über 40 Wörter als Blockzitat (`\begin{quote}…\end{quote}`), ohne Anführungszeichen
- ☐ **Keine** Skripte, Vorlesungsfolien, Webinare, Wikipedia oder KI-Ausgaben als Quellen
- ☐ Internetquellen ohne Abrufdatum. Datum = letzte Aktualisierung, sonst „n.d.“. DOI vor URL.
- ☐ Wenig bekannte Software (z. B. PySide6, PyInstaller) ins Literaturverzeichnis; übliche Software nur im Text nennen (Kap. 2.3.9)
- ☐ Abbildungen und Tabellen: Überschrift „Abb. 1 …“ bzw. „Tab. 1 …“ ⚙. Darunter `\quelle{…}` mit einer der Formulierungen aus dem Zitierleitfaden:
  - „Eigene Darstellung.“
  - „Eigene Darstellung in Anlehnung an …“
  - „Eigene Darstellung (geändert) in Anlehnung an …“
  - „Eigene Darstellung auf der Basis von …“
  - „Übernommen aus …“
- ☐ Screenshots fremder Abbildungen vermeiden, besser nachbauen. Screenshots der eigenen App sind „Eigene Darstellung.“.
- ☐ Jede Quelle im Literaturverzeichnis ist im Text zitiert und umgekehrt. ⚙ biblatex druckt nur zitierte Einträge.

## 7. Dateianlagen und Quellcode [D]

- ⚙ Der **Quellcode steht maschinenlesbar und kopierfähig im Anhang** der Projektdokumentation, ab Phase 2 automatisch aus `app/**/*.py`. Leerzeichen bleiben beim Kopieren erhalten.
- ⚙ Optional für eine Abgabe mit Dateianlage: `--phase 3 --abgabe --anlage` bettet die Repository-ZIP als `.zip.txt` oben links auf dem Deckblatt ein. Die Variante landet in `dist/`. Die Anleitung stammt aus dem Dualen Studium. Für PebblePad wird die ZIP ohnehin separat hochgeladen; die Notwendigkeit vorab mit der Tutor:in klären.
- ☐ Vor der Abgabe die PDF öffnen und Anlagen sowie Lesezeichen testen; die `.exe` aus dem ZIP auf einem frischen Windows starten.

## 8. Bewertung [A 3], worauf geachtet wird

| Kriterium | Gewicht | Leitfrage |
|---|---|---|
| Problemabgrenzung/Zielsetzung | 10 % | Sind Ziele, Umfang und Ergebnis klar? Wird der Nutzen für die Zielgruppe deutlich? Sind die Anforderungen präzise? |
| Methodik/Idee/Vorgehen | 20 % | Passen Methoden und Technologien? Sind die Entscheidungen nachvollziehbar? Ist der Prozess transparent und kritisch reflektiert? |
| Qualität der Umsetzung | 40 % | Funktioniert die App fehlerfrei und intuitiv? Ist der Code strukturiert und dokumentiert? Sind die Tests sinnvoll? Sind die Dokumente sauber? |
| Kreativität/Richtigkeit | 20 % | Werden die Ziele erreicht? Gibt es Kundennutzen und Innovation? Sind alle FA und NFA umgesetzt? Sind die **UML-Diagramme korrekt**? Wurde der **Zeitplan eingehalten**? |
| Formale Anforderungen | 10 % | Sind alle Vorgaben erfüllt? Ist die Rechtschreibung fehlerfrei? |
