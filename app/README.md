# Anwendung (Work-Life-Balance-App für Windows)

> **Status: Hier liegt noch kein Code.** Die Implementierung beginnt erst in **Phase 2**
> (Erarbeitungs- und Reflexionsphase), nachdem Portfolioteil 1 eingereicht wurde.
> Der Prüfungsleitfaden schreibt vor, die Phasen strikt in der vorgegebenen
> Reihenfolge zu bearbeiten. Ein Verstoß gilt als nicht bestanden.
> Mock-ups für die Konzeptionsphase gehören nach `docs/diagramme/06_Mockups/`.

## Vorgaben aus der Aufgabenstellung

- Windows-10/11-Desktopanwendung in einer modernen objektorientierten Hochsprache: **Python**
- Grafische Benutzeroberfläche, selbsterklärend und intuitiv
- Funktionsfähige Anwendung mit ausreichend Quellcode, kein Mock-up
- Sinnvolle **Testdaten**, damit der Nutzen sofort sichtbar wird
- Third-Party-Bibliotheken sind erlaubt, müssen aber im Architekturdokument
  **dokumentiert und begründet** werden. Fremden Quellcode zu kopieren ist verboten.
- Vorausgesetzt werden dürfen nur Standard-Laufzeitumgebungen (Python-Interpreter).
  Alles darüber hinaus muss beschrieben **und mitgeliefert** werden.
- Der Code muss gut strukturiert und verständlich kommentiert sein.

## Geplante Struktur (wird im Architekturdokument festgelegt)

```
app/
├── src/<paketname>/     Quellcode (Schichten laut Architekturdokument)
├── tests/               automatisierte Tests (pytest): Unit- und Integrationstests
├── testdaten/           mitgelieferte Beispieldaten
├── release/             ausführbare Anwendung für die Abgabe (z. B. .exe)
├── pyproject.toml       Abhängigkeiten und Projektkonfiguration
└── README.md
```

Der Quellcode-Anhang der Projektdokumentation wird ab Phase 2 automatisch aus allen
`*.py`-Dateien unter `app/` erzeugt (`python tools/build_docs.py --phase 2`).
