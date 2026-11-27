# Phase 3 (Finalisierung) – Design

## Ziel und Grund
Portfolioteil 3 für BalanceOS abgabefertig machen. Abgabe am 04.12.2026; bis dahin testet der Nutzer selbst.
Bewertet wird vor allem die Qualität von Umsetzung und Dokumentation (40 %); die App muss lauffähig sein.

## Umfang (Aufgabenstellung 1.3 und Feedback Phase 2)
- Testdokument: Teststrategie (Unit-, Integrations-, Systemtests), Testprotokoll je Testfall mit ID,
  Kurzbeschreibung, Vorbedingungen, Eingaben/Aktionen, erwartetem und tatsächlichem Ergebnis, Ergebnisübersicht.
- Projektdokumentation: Benutzeranleitung (Installation, Start, erste Schritte), Anforderungserfüllung und
  technische Schulden, neues Schlusskapitel „Kritische Bewertung und Fazit“ (Projektfrage, a-posteriori-Limitationen, Fazit).
- Abstract: genau 2 Seiten Textteil, Making-of und Reflexion (Probleme, Zeitplantreue, Lessons Learned).
- Ausführbare Anwendung: `app/release/BalanceOS.exe` als einzelne Datei (PyInstaller onefile), unter 100 MB.
- Feedback Phase 2: Redundanzen zwischen den Dokumenten durch Verweise ersetzen; NFA-Prüfkriterien so schärfen,
  dass jedes automatisiert oder eindeutig prüfbar ist und auf einen Testfall verweist.
- Abgabe: Abstract-PDF, Finales Produkt (6 Dokumente), Repository-ZIP, eingefrorene PDFs aus Phase 1 und 2.

## Entscheidungen
- exe: onefile im Repository (Nutzerwahl 27.11.). Ordner-ZIP verworfen (größer); Release-Asset verworfen (nicht im Repo/ZIP).
- Systemtests: automatisiert durch die echte Oberfläche (pytest-qt, offscreen) auf frischer Datenbank,
  zusätzlich Absturz-Test (NFA04) per Unterprozess. Ins Protokoll kommen nur tatsächlich gelaufene Ergebnisse.
- NFA01 (Testpersonen) wird zu einem prüfbaren Kriterium (deutsche Texte, Beschriftungen, Erreichbarkeit des
  Erfassungsdialogs); ein Test mit Personen ist als Limitation genannt.
- Der exe-Start lässt sich hier nicht prüfen (Smart App Control blockiert unsignierte Programme, wird nicht umgangen).
  Das Protokoll weist den Testfall als vom Nutzer auszuführen aus; Ausweichweg `python -m balanceos`.
- Abgabedatum Phase 3 auf allen Titelblättern: 04.12.2026.
- Phase-1/2-PDFs bleiben eingefroren (Tags `phase1-abgabe`, `phase2-abgabe`).

## Nicht-Ziele
Keine neuen Funktionen der App; keine Änderungen an der Architektur. Code ändert sich nur für Tests, Build und Fehlerbehebungen.

## Regeln
Nur frei zugängliche neue Quellen; Humanizer-Stil; kein „ich/wir/man“ außer im Abstract; jeder Unterabschnitt ≥ ½ Seite;
keine Netzwerkzugriffe in der App; `Vorgaben/` nie committen; ZIP erst nach dem letzten Commit erzeugen.
