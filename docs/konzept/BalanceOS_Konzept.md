# BalanceOS: überarbeitetes Konzept (Arbeitsgrundlage)

> **Status:** Diese Fassung ist ein Entwurf zur Abstimmung. Sie bildet die Arbeitsgrundlage für
> Phase 1 und wird **nicht abgegeben**. Die Ideenskizze bleibt unverändert in
> `BalanceOS_Ideenskizze_Original.md`.
> Die abzugebenden LaTeX-Dokumente (`docs/latex/`) schreibst du in eigenen Worten. Grund ist die
> eigenständige Erarbeitung als Teil der Prüfungsleistung, außerdem gilt die KI-Richtlinie der IU.
> Markierung im Text: **[Vorschlag]** heißt, dass die Entscheidung noch bei dir liegt.

---

## 0. Was gegenüber der Ideenskizze verbessert wurde

| # | Verbesserung | Warum (Bezug zur Bewertung) |
|---|---|---|
| 1 | **Umfang nach MoSCoW geschnitten** (Kap. 4). Die Skizze umfasst 15 Module, ein Kern-Release ist abgegrenzt. | Bewertet wird: „Wurden alle FA/NFA umgesetzt?“ und „Wurde der Zeitplan eingehalten?“. Alles, was im Anforderungsdokument steht und nicht gebaut wird, muss als technische Schuld dokumentiert werden. |
| 2 | **Zielgruppe und Kundennutzen** ausdrücklich formuliert (Kap. 2). | Die Aufgabenstellung verlangt einen „klar definierten Customer Value“ für eine „zu definierende Zielgruppe“ (Problemabgrenzung 10 %). |
| 3 | **Alleinstellungsmerkmal** gegenüber bestehenden Apps herausgearbeitet (Kap. 3). | „Hinreichend kreativ und neu“ (Kreativität 20 %) |
| 4 | **Bewertungslogik als konkreter Algorithmus** (Kap. 6) | Das Spezifikationsdokument fordert Geschäftsprozesse mit Algorithmus und ein Aktivitätsdiagramm eines Kernprozesses. |
| 5 | **Regelkatalog** mit prüfbaren Bedingungen (Kap. 7) | Daraus entstehen Geschäftsregeln und Testfälle; ergibt Nachverfolgbarkeit von der User Story bis zum Test. |
| 6 | **Bereichstyp „Mindestziel“ oder „Obergrenze“** | Bei Arbeit oder Überstunden ist „mehr“ nicht besser. Die Skizze behandelte alle Bereiche gleich. |
| 7 | **Quellen korrigiert und ergänzt** (Kap. 11), Lizenzfragen geklärt | Statt CDC-Webseite die Primärquelle (Watson et al., 2015). WHO-5 steht unter einer CC-Lizenz. Die deutsche COPSOQ-Fassung ist lizenzpflichtig und deshalb vorerst ausgeschlossen. |
| 8 | **Abhängigkeiten reduziert** (Kap. 9): Diagramme mit QtCharts (Teil von PySide6), `sqlite3` aus der Standardbibliothek | Jede Third-Party-Bibliothek muss begründet und mitgeliefert werden. Weniger Bibliotheken bedeuten weniger Risiko und weniger Dokumentationsaufwand. |
| 9 | **Begriff „Phase“ entschärft**: Die Entwicklungsschritte heißen jetzt „Inkremente“ (Kap. 10) | Sonst gibt es Verwechslungsgefahr mit den drei IU-Portfolio-Phasen. |
| 10 | **Testdaten** als Pflichtbestandteil eingeplant (Demo-Profil über 8 Wochen) | Die Aufgabenstellung verlangt, dass der Nutzen sofort sichtbar ist. |

---

## 1. Kurzbeschreibung

BalanceOS ist eine lokal laufende Windows-Desktopanwendung (Python, PySide6). Sie hilft Menschen,
ihren Alltag über **Lebensbereiche** hinweg zu erfassen und mit ihren **eigenen Wünschen** und
**wissenschaftlich begründeten Richtwerten** abzugleichen. Aus den Daten entstehen
**nachvollziehbare, regelbasierte Hinweise**. Jeder Hinweis erklärt, warum er erscheint und auf
welcher Grundlage. Es kommt keine KI zum Einsatz, und die Daten verlassen den Rechner nicht.

**Leitgedanke** (aus der Skizze übernommen): Balance heißt nicht, dass alle denselben Zeitplan haben.
Balance heißt, dass Bedürfnisse, Verpflichtungen, Gesundheit und Erholung langfristig in einem
persönlich zufriedenstellenden Verhältnis stehen. Dieser Gedanke entspricht dem Lifestyle Balance
Model (Matuska & Christiansen, 2008).

## 2. Problem, Zielgruppe und Kundennutzen

**Problem:** Berufstätige mit Mehrfachbelastung, etwa durch Beruf und Familie oder Beruf und Studium,
merken oft erst spät, dass Erholung, Bewegung oder Beziehungen dauerhaft zu kurz kommen. Bestehende
Werkzeuge messen meist nur **eine** Dimension: Zeiterfassung, Gewohnheiten oder Stimmung. Sie
verbinden diese Daten nicht mit den eigenen Wünschen und mit fundierten Richtwerten.

**Zielgruppe [Vorschlag]:**
- *Primär:* berufstätige Erwachsene von 25 bis 55 Jahren mit zusätzlicher Verantwortung, etwa Familie,
  berufsbegleitendes Studium oder Pflege, die ihren Alltag bewusster gestalten möchten.
- *Persona-Idee:* „Sarah, 34, Teilzeit im Büro, ein Kind, berufsbegleitendes Fernstudium“. Diese Persona
  passt auch zur Kursvorgabe, nach der die Tutor:innen als Zielgruppe gelten.
- *Nicht Zielgruppe:* Menschen in psychischen Krisen. Die App ist kein Behandlungsersatz und zeigt
  einen Hinweis auf professionelle Hilfe.

**Kundennutzen (Customer Value):**
1. Die Person sieht auf einen Blick, wo Wunsch und Wirklichkeit auseinanderliegen (Soll-Ist je Lebensbereich).
2. Sie bekommt verständliche, begründete Hinweise statt pauschaler Ratschläge.
3. Sie entscheidet selbst, welche Modelle und Richtwerte gelten.
4. Alle Daten bleiben lokal, ohne Konto, Cloud oder KI.

## 3. Alleinstellungsmerkmal und Abgrenzung

| Kategorie bestehender Apps | Fokus | Was BalanceOS anders macht |
|---|---|---|
| Zeiterfassung | Wie viel Zeit wofür? | + Abgleich mit **persönlichem Soll** und Zufriedenheit |
| Habit-Tracker | Gewohnheiten abhaken | + Lebensbereiche, Erholungswirkung, Richtwerte |
| Stimmungstagebuch | Stimmung protokollieren | + Verknüpfung mit Aktivitäten und Belastung |
| Fitness-Apps | Bewegung | + Bewegung als **ein** Bereich von vielen, WHO-Richtwert wählbar |

**Kern der Neuheit: der „Wissenschaftliche Balance-Kompass“.**
- Jeder Hinweis kann „**Warum sehe ich das?**“ beantworten: Er nennt Regel, Daten, Zeitraum,
  Schwelle und Quelle.
- **Evidenzkennzeichnung** an jedem Wert. Es gibt fünf Stufen:
  1. wissenschaftliche Theorie
  2. evidenzbasierte Empfehlung
  3. validiertes Instrument
  4. persönliche Regel
  5. programmeigener Score
- Modelle lassen sich einzeln ein- und ausschalten. Ihre Ergebnisse bleiben getrennt. Es gibt keine
  „wissenschaftlich validierte Gesamtnote“.

## 4. Umfang (MoSCoW): Was in die Portfolio-Version kommt

> **Regel:** Ins Anforderungsdokument kommen nur **Must** und **Should** als User Stories.
> **Could** erscheint als optionale Erweiterung, **Won't** im Kapitel „Abgrenzung“ der
> Projektdokumentation. So entsteht keine unnötige technische Schuld.

### Must (Kern, ohne den die App ihren Nutzen verfehlt)
- **M1 Lebensbereiche:** zehn Standardbereiche aus der Skizze, umbenennbar und deaktivierbar, eigene Bereiche möglich.
  Jeder Bereich ist vom Typ *Mindestziel* (z. B. Schlaf, Bewegung) oder *Obergrenze* (z. B. Arbeit, Überstunden).
- **M2 Aktivitäten erfassen:** Name, Bereich, Datum, Start, Ende oder Dauer, Status (geplant, durchgeführt,
  ausgefallen), Zufriedenheit (1–5), Belastung (1–5), Erholungswirkung (1–5) und Notiz.
- **M3 Wunschprofil (Soll):** gewünschte Stunden pro Woche je Bereich. Das ist die Grundlage des
  Lifestyle-Balance-Abgleichs.
- **M4 Wiederkehrende Aktivitäten:** täglich oder wöchentlich an gewählten Wochentagen; einzelne Termine
  lassen sich überspringen.
- **M5 Bewertung:** Score von 0 bis 100 je Bereich mit Anzeige der **Datenvollständigkeit**. Ein optionaler
  Gesamt-Score mit eigener Gewichtung ist als „programmeigen“ gekennzeichnet (Kap. 6).
- **M6 Regel-Engine und Feedback:** Regelkatalog (Kap. 7) mit Erklärung „Warum?“, Regeln einzeln abschaltbar.
- **M7 Balance-Kompass:** Infoseiten zu den Modellen (Erklärung, Quelle, Evidenzart, Grenzen),
  Modelle aktivieren und deaktivieren.
- **M8 Dashboard:** Scores je Bereich, Soll-Ist-Balken, aktuelle Hinweise, Aktivitäten der Woche.
- **M9 Wochenansicht** (Kalender) mit Farbe je Lebensbereich.
- **M10 Lokale Datenhaltung** in SQLite, Export der eigenen Daten als CSV und JSON, vollständiges Löschen.
- **M11 Testdaten:** Demo-Profil „Sarah“ mit acht Wochen realistischer Daten, per Knopfdruck lad- und entfernbar.

### Should (wichtig, wird eingeplant)
- **S1 Wochenreflexion** mit Leitfragen aus den Modellen (Erholung, Zufriedenheit); freiwillig, ohne Abwertung bei Auslassung.
- **S2 WHO-5-Fragebogen** mit separater Originalauswertung: Rohwert 0–25, mal 4 ergibt 0–100. Es gibt nur
  einen Hinweistext, keine Diagnose.
- **S3 Persönliche Ziele** je Bereich (Zeit oder Häufigkeit), pausierbar.
- **S4 Statistiken:** Verlauf der Scores und Zeitverteilung über Wochen (QtCharts), Vergleich zweier Zeiträume.
- **S5 Ersteinrichtung** mit Lebensprofil-Vorlagen (Berufstätig, Beruf und Familie, Studium …), die Startwerte vorbelegen.

### Could (nur wenn Zeit bleibt)
- C1 Tages- und Monatsansicht · C2 tägliche Kurzreflexion und Tagebuch · C3 PERMA- und SDT-Reflexionsfragen
- C4 Windows-Benachrichtigungen (über `QSystemTrayIcon`, ohne Zusatzbibliothek)
- C5 Hell- und Dunkelmodus · C6 Passwortschutz beim Start · C7 PDF-Wochenbericht · C8 Datensicherung und Wiederherstellung

### Won't (bewusst nicht in dieser Version, als Ausblick dokumentiert)
- COPSOQ: Die deutsche Fassung ist lizenzpflichtig.
- Datenbankverschlüsselung · frei anordenbares Dashboard per Drag & Drop · Jahresansicht
- komplexe Wiederholungsmuster und Urlaubsausnahmen · Mehrfachzuordnung einer Aktivität zu mehreren Bereichen
- jede Form von KI, Cloud-Synchronisation und Benutzerkonten

## 5. Wissenschaftliche Grundlage im Balance-Kompass

| Modell / Richtwert | Evidenzart | Verwendung in BalanceOS | Version |
|---|---|---|---|
| Lifestyle Balance Model (Matuska & Christiansen, 2008; Matuska, 2012) | Theorie | Soll-Ist-Abgleich je Bereich (Kern) | Must |
| Effort-Recovery Model (Meijman & Mulder, 1998) | Theorie | Belastung im Verhältnis zur Erholungswirkung (Regeln R05, R06) | Must |
| Job Demands–Resources (Bakker & Demerouti, 2017) | Theorie | Arbeitsbelastung im Verhältnis zu Ressourcen (Regel R07) | Must |
| WHO-Bewegungsempfehlung (WHO, 2020): 150–300 min moderat/Woche, 2 Tage Kraft | Empfehlung | Richtwert Bewegung (R01, R02) | Must |
| Schlaf ≥ 7 h für Erwachsene (Watson et al., 2015) | Empfehlung | Richtwert Schlaf (R03) | Must |
| WHO-5 (WHO, 2024; Topp et al., 2015) | validiertes Instrument | separater Fragebogen | Should |
| PERMA (Seligman, 2011) | Theorie | Reflexionsfragen | Could |
| Selbstbestimmungstheorie (Ryan & Deci, 2000) | Theorie | Reflexionsfragen | Could |

**Wichtige Einschränkungen**, die im Text und in der App stehen sollen:
- Die eigenen Skalen für Belastung, Erholung und Zufriedenheit (1–5) sind **keine validierten Instrumente**.
  Regeln, die darauf aufbauen, tragen die Kennzeichnung „programmeigen, theoriegeleitet“.
- Hinweise zeigen Zusammenhänge, aber **keine Ursachen**. Die App stellt keine Diagnosen und ist kein Medizinprodukt.
- Beim WHO-5 die Nutzungsbedingungen der WHO-Publikation prüfen. Sie ist vermutlich CC BY-NC-SA 3.0 IGO
  lizenziert; das vor der Verwendung am Original verifizieren.

## 6. Bewertungslogik [Vorschlag als Grundlage für die Spezifikation]

Zeitraum: Kalenderwoche (Montag bis Sonntag). Es zählen nur Aktivitäten mit Status *durchgeführt*.

1. **Ist-Zeit** je Bereich b: `Ist_b` ist die Summe der Dauern.
2. **Zielerfüllung** (abhängig vom Bereichstyp):
   - Mindestziel: `z_b = min(Ist_b / Soll_b, 1)`
   - Obergrenze: `z_b = 1`, wenn `Ist_b ≤ Soll_b`, sonst `max(0, 1 − (Ist_b − Soll_b) / Soll_b)`
3. **Zufriedenheit:** `s_b = (Mittelwert der Bewertungen − 1) / 4`, der Wert liegt im Bereich [0, 1].
4. **Bereichs-Score:** `Score_b = 100 · (α · z_b + (1 − α) · s_b)` mit dem Standardwert α = 0,6, einstellbar.
   Ohne Zufriedenheitsbewertungen gilt `Score_b = 100 · z_b`, und die Vollständigkeit sinkt.
5. **Datenvollständigkeit:** Anteil der Tage mit mindestens einem Eintrag. Liegt er **unter 4 von 7 Tagen**,
   zeigt die App „zu wenig Daten“ statt eines niedrigen Scores. Diese Regel übernimmt die Forderung der Skizze,
   dass fehlende Daten nicht zu Abwertung führen dürfen.
6. **Gesamt-Score (optional):** `Σ g_b · Score_b / Σ g_b` über die Bereiche mit ausreichenden Daten. Die
   Gewichte g_b legt die Person fest; Standard ist Gleichgewichtung. Kennzeichnung: *programmeigener Score,
   nicht validiert*.
7. **Lifestyle-Balance-Abweichung** je Bereich: `Ist_b − Soll_b` in Stunden, als Balken dargestellt.
   Sie geht nicht in den Score ein, sondern dient der Anschauung.

Diese Wochenauswertung ist der **Kernprozess** für das UML-Aktivitätsdiagramm (Spezifikation) und das
Sequenzdiagramm (Architektur).

## 7. Regelkatalog [Vorschlag, Startumfang]

Jede Regel hat diese Bestandteile:
- ID und Quelle oder Modell
- Datenbasis und Zeitraum
- Bedingung und Schwelle
- Priorität und Textvorlage

Die Regeln sind deterministisch und damit testbar.

| ID | Modell / Quelle | Bedingung (Zeitraum) | Hinweis (Kurzform) |
|---|---|---|---|
| R01 | WHO 2020 | moderate Bewegung < 150 min in der letzten vollständigen Woche | Bewegung unter dem gewählten WHO-Richtwert |
| R02 | WHO 2020 | weniger als 2 Tage Krafttraining pro Woche | muskelkräftigende Aktivität ergänzen |
| R03 | Watson et al. 2015 | Ø Schlaf < 7 h über 7 Tage | Schlafdauer unter der Empfehlung |
| R04 | Lifestyle Balance | Mindestziel-Bereich: Ist < 50 % von Soll in 3 aufeinanderfolgenden Wochen | dauerhafte Lücke zum eigenen Wunsch |
| R05 | Effort-Recovery | Ø Belastung ≥ 4 und Ø Erholungswirkung ≤ 2 an ≥ 4 von 7 Tagen | hohe Belastung bei wenig Erholung |
| R06 | Effort-Recovery | Kategorie Erholung = 0 h an einem Wochenende mit ≥ 6 h Verpflichtungen | Wochenende ohne Erholung |
| R07 | JD-R | Arbeit über der Obergrenze in 2 von 3 Wochen und Ø Belastung ≥ 4 | Anforderungen und Ressourcen prüfen |
| R08 | persönliches Ziel | Ziel in der Woche erreicht | positives Feedback |
| R09 | Lifestyle Balance | Zufriedenheit eines Bereichs gegenüber der Vorwoche um ≥ 1 Punkt gestiegen | positive Entwicklung |
| R10 | Systemregel | Datenvollständigkeit < 4/7 | Hinweis: zu wenig Daten für eine Bewertung |

## 8. Benutzeroberfläche [Vorschlag]

```
┌───────────────┬──────────────────────────────────────────────────────┐
│ BalanceOS     │  Dashboard – KW 46                     [+ Aktivität] │
│               │ ┌──────────────┐ ┌──────────────────────────────────┐ │
│ ▸ Dashboard   │ │ Balance  72  │ │ Soll/Ist je Lebensbereich        │ │
│   Woche       │ │ (programm-   │ │ Schlaf     ███████████░  52/56 h │ │
│   Aktivitäten │ │  eigen) ⓘ   │ │ Bewegung   ████░░░░░░░░  90/150m │ │
│   Ziele       │ │ Daten: 6/7 ✓ │ │ Familie    █████████░░░  9/12 h  │ │
│   Reflexion   │ └──────────────┘ │ Arbeit     ██████████▲  44/40 h  │ │
│   Kompass     │ ┌──────────────────────────────────────────────────┐ │
│   Statistik   │ │ Hinweise                                         │ │
│   Einstellung │ │ ⚠ Bewegung unter WHO-Richtwert   [Warum?] [×]    │ │
│               │ │ ✓ Familienziel erreicht                          │ │
└───────────────┴──────────────────────────────────────────────────────┘
```

Navigation über eine Seitenleiste, eine Seite pro Funktion. Pro Seite gibt es eine Hauptaktion. Alle
Eingaben werden geprüft, etwa „Ende nach Start“ und „Dauer > 0“. Das ergibt die Tabelle zur
Eingabevalidierung im Spezifikationsdokument.

## 9. Technik [Vorschlag, wird im Architekturdokument in Phase 2 begründet]

| Baustein | Wahl | Begründung |
|---|---|---|
| Sprache | Python 3.12+ | Vorgabe: objektorientierte Hochsprache |
| GUI | PySide6 (Qt for Python), LGPL-3.0 | native Windows-Oberfläche, Kalender- und Tabellen-Widgets, **QtCharts inklusive** |
| Diagramme | QtCharts (in PySide6) | keine zusätzliche Bibliothek wie matplotlib, pandas oder NumPy nötig |
| Datenbank | SQLite über `sqlite3` (Standardbibliothek) | lokal, ohne Server, ohne Zusatzbibliothek |
| Architektur | Schichten: Präsentation → Anwendung (Services) → Domäne (Bewertungs- und Regel-Engine, reines Python) → Persistenz (Repositorys) | Die Domänenlogik lässt sich ohne GUI testen. |
| Tests | pytest (Unit und Integration), pytest-qt optional | automatisierte Tests sind ausdrücklich erwünscht |
| Auslieferung | PyInstaller → `BalanceOS.exe` in `app/release/` | Python muss nicht installiert sein; alle Komponenten werden mitgeliefert. |

## 10. Vorgehen: Inkremente innerhalb der IU-Phasen

| IU-Phase | Inkrement | Inhalt |
|---|---|---|
| **1 Konzeption** | – | Projekt-, Anforderungs- und Spezifikationsdokument, Mock-ups. **Noch kein Code.** |
| **2 Erarbeitung** | I1 Grundgerüst | Projektstruktur, Datenbank, Hauptfenster, Navigation |
| | I2 Erfassen | Lebensbereiche, Aktivitäten, Wiederholungen, Wochenansicht |
| | I3 Auswerten | Wunschprofil, Bewertungs-Engine, Dashboard |
| | I4 Kompass | Regel-Engine, Feedback mit „Warum?“, Modellseiten |
| | I5 Should-Funktionen | Reflexion, WHO-5, Ziele, Statistiken, Ersteinrichtung |
| **3 Finalisierung** | I6 Qualität | Tests und Testdokument, Fehlerbehebung, Testdaten, `.exe`, Benutzeranleitung, Abstract |

## 11. Quellen (APA 7; vor dem Zitieren am Original prüfen, Seitenzahlen ergänzen)

- Bakker, A. B. & Demerouti, E. (2017). Job demands–resources theory: Taking stock and looking forward. *Journal of Occupational Health Psychology, 22*(3), 273–285. https://doi.org/10.1037/ocp0000056
- Matuska, K. (2012). Validity evidence of a model and measure of life balance. *OTJR: Occupation, Participation and Health, 32*(1), 229–237. https://doi.org/10.3928/15394492-20110610-02
- Matuska, K. M. & Christiansen, C. H. (2008). A proposed model of lifestyle balance. *Journal of Occupational Science, 15*(1), 9–19. https://doi.org/10.1080/14427591.2008.9686602
- Meijman, T. F. & Mulder, G. (1998). Psychological aspects of workload. In P. J. D. Drenth, H. Thierry & C. J. de Wolff (Hrsg.), *Handbook of work and organizational psychology: Vol. 2. Work psychology* (2. Aufl., S. 5–33). Psychology Press.
- Ryan, R. M. & Deci, E. L. (2000). Self-determination theory and the facilitation of intrinsic motivation, social development, and well-being. *American Psychologist, 55*(1), 68–78. https://doi.org/10.1037/0003-066X.55.1.68
- Seligman, M. E. P. (2011). *Flourish: A visionary new understanding of happiness and well-being*. Free Press.
- Topp, C. W., Østergaard, S. D., Søndergaard, S. & Bech, P. (2015). The WHO-5 Well-Being Index: A systematic review of the literature. *Psychotherapy and Psychosomatics, 84*(3), 167–176. https://doi.org/10.1159/000376585
- Watson, N. F., Badr, M. S., Belenky, G., Bliwise, D. L., Buxton, O. M., Buysse, D., Dinges, D. F., Gangwisch, J., Grandner, M. A., Kushida, C., Malhotra, R. K., Martin, J. L., Patel, S. R., Quan, S. F. & Tasali, E. (2015). Recommended amount of sleep for a healthy adult: A joint consensus statement of the American Academy of Sleep Medicine and Sleep Research Society. *Sleep, 38*(6), 843–844. https://doi.org/10.5665/sleep.4716
- World Health Organization. (2020). *WHO guidelines on physical activity and sedentary behaviour*. https://www.who.int/publications/i/item/9789240015128
- World Health Organization. (2024). *The World Health Organization-Five Well-Being Index (WHO-5)*. https://www.who.int/publications/m/item/WHO-UCN-MSD-MHE-2024.01

Die Einträge stehen auch in `docs/latex/_gemeinsam/literatur.bib`. Dort sind die Schlüssel für
`\parencite[S.~x]{…}` angelegt.

## 12. Offene Entscheidungen

1. **Zeitbudget und Abgabetermine**: Davon hängt ab, ob Should vollständig hineinpasst.
2. Bestätigung des **MoSCoW-Schnitts** (Kap. 4)
3. Bestätigung der **Zielgruppe und Persona** (Kap. 2)
4. Name „BalanceOS“: kurz prüfen, ob es bereits ein gleichnamiges Produkt gibt (Neuheit, Verwechslungsgefahr).
