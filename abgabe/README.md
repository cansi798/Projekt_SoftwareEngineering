# Abgaben (PebblePad)

Hier liegen die eingereichten Fassungen je Phase. **Eine einmal eingereichte PDF wird nicht mehr
verändert.** Der Prüfungsleitfaden verlangt, dass die Endergebnisse aus Phase 1 und Phase 2
separat gespeichert werden. In Phase 3 werden sie unverändert erneut hochgeladen.
Nach jeder Einreichung setzt du einen Git-Tag (`phase1-abgabe` bzw. `phase2-abgabe`).
Danach weigert sich `tools/build_docs.py`, die Datei zu überschreiben.

| Phase | Einzureichen in PebblePad | Datei hier |
|---|---|---|
| 1 Konzeption | Kurzzusammenfassung (Textfeld, ca. ½ Seite) | `Phase1_Konzeption/Kurzzusammenfassung.md` |
| | PDF: Projekt-, Anforderungs- und Spezifikationsdokument | `Phase1_Konzeption/Nachname-Vorname_Matrikelnummer_PSE_P1_Abgabe.pdf` |
| 2 Erarbeitung | Kurzzusammenfassung Design- und Implementierungsentscheidungen | `Phase2_Erarbeitung/Kurzzusammenfassung.md` |
| | PDF: Projektdokumentation (mit GitHub-Link), Anforderungs-, Spezifikations- und Architekturdokument | `Phase2_Erarbeitung/…_PSE_P2_Abgabe.pdf` |
| 3 Finalisierung | Abstract (2 Seiten) | `Phase3_Finalisierung/…_PSE_P3_Abstract.pdf` |
| | „Finales Produkt“: alle 6 Dokumente in einer PDF | `Phase3_Finalisierung/…_PSE_P3_FinalesProdukt.pdf` |
| | ZIP mit allen Inhalten des GitHub-Repositorys | `dist/…_PSE_P3_Abgabe.zip` (nicht im Repository) |
| | PDF aus Phase 1 erneut | `Phase1_Konzeption/…_PSE_P1_Abgabe.pdf` |
| | PDF aus Phase 2 erneut | `Phase2_Erarbeitung/…_PSE_P2_Abgabe.pdf` |

## Ablauf je Phase

```powershell
# 1. Dokumente bauen, prüfen und Abgabe-PDF erzeugen
python tools/build_docs.py --phase 1 --abgabe
# 2. Vor dem Hochladen: PDF öffnen und Ausgabe des Skripts prüfen (0 × TODO, keine Platzhalter)
# 3. Committen, pushen und die eingereichte Fassung markieren
git add -A; git commit -m "Abgabe Portfolioteil 1"; git push
git tag phase1-abgabe; git push origin phase1-abgabe
```

**Phase 3:** Die ZIP-Datei muss mit dem GitHub-Repository **identisch** sein. Nachträgliche
Änderungen am Repository sind verboten. Deshalb gilt diese Reihenfolge:

1. `python tools/build_docs.py --phase 3 --abgabe` ausführen
2. Ausführbare Anwendung in `app/release/` ablegen
3. Committen und pushen
4. `python tools/build_docs.py --phase 3 --zip` ausführen. Das Skript bricht ab, wenn der lokale
   Stand von GitHub abweicht.
5. In PebblePad hochladen. Danach nichts mehr am Repository ändern.

Vor jeder Einreichung muss die **Eidesstattliche Erklärung** elektronisch über myCampus abgegeben
sein. Vorher ist keine Einreichung möglich.
