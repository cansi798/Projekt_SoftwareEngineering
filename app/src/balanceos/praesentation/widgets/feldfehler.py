"""Markierung ungültiger Eingabefelder mit rotem Rahmen und Meldung (NFA02)."""

from PySide6.QtWidgets import QLabel, QWidget


def fehlerlabel() -> QLabel:
    """Erzeugt ein zunächst verborgenes Label für Fehlermeldungen unter einem Feld."""
    label = QLabel()
    label.setObjectName("feldfehler")
    label.setWordWrap(True)
    label.hide()
    return label


def markiere(feld: QWidget, label: QLabel, meldung: str | None) -> None:
    """Zeigt eine Meldung am Feld an oder entfernt sie.

    Args:
        feld: Eingabefeld, das bei einem Fehler rot umrandet wird.
        label: Label direkt unter dem Feld für den Meldungstext.
        meldung: Fehlermeldung oder ``None``, wenn das Feld gültig ist.
    """
    feld.setProperty("fehler", "true" if meldung else "false")
    feld.style().unpolish(feld)
    feld.style().polish(feld)
    label.setText(meldung or "")
    label.setVisible(bool(meldung))
