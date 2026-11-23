# Kurzzusammenfassung Portfolioteil 2 (Erarbeitungs- und Reflexionsphase)

> Für das **Textfeld in PebblePad** gedacht, nicht als PDF.
> PebblePad erlaubt höchstens 200 Wörter.
> Inhalt: die wichtigsten **Design- und Implementierungsentscheidungen**.
> Zu berücksichtigen: Orientierung am Projektplan, Ressourcen, erkannte Probleme und Risiken,
> Fortschritt, umgesetztes Feedback aus Phase 1.

## Text (zum Einfügen in PebblePad)

BalanceOS ist in Python 3.12 mit PySide6 und SQLite umgesetzt und folgt einer Schichtenarchitektur aus Präsentation, Anwendung, Domäne und Persistenz. Die Schichten halten die Fachlogik testbar und passen eins zu eins zu den Mock-ups der Spezifikation. Drei Entscheidungen prägen die Umsetzung. Die Domäne mit Bewertung, Regeln R01–R10 und Validierung kennt weder Qt noch SQLite; ein Architekturtest prüft das. Die Wochenbewertung wird bei jeder Anzeige neu berechnet statt gespeichert, daher kann kein veralteter Score stehen bleiben. Soll-Ist-Balken und Verlaufsdiagramm zeichnet BalanceOS selbst mit QPainter, ohne zusätzliche Diagrammbibliothek.

Alle 22 User Stories sind in fünf Inkrementen umgesetzt und mit 261 automatisierten Tests abgesichert. Mit 30.000 Aktivitäten dauert die Neuberechnung des Dashboards rund 4 ms. Aus dem Feedback zu Phase 1 kamen eine ausdrückliche Projektfrage, messbare Prüfkriterien, die neue Anforderung NFA12 zur Skalierbarkeit und gestraffte, weniger redundante Texte hinzu. Der Start von Phase 2 verschob sich bis zum Eingang des Feedbacks am 23.11. (Risiko RI02); durch Verdichtung und die Zeitreserve war der Stand für M2 trotzdem eine Woche vor dem Termin fertig. Beim Entwickeln wurde das KI-Werkzeug Claude Code eingesetzt; die Projektdokumentation beschreibt Umfang und Regeln.

Repository: https://github.com/cansi798/Projekt_SoftwareEngineering
