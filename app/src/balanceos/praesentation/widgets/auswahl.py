"""Auswahlliste, die beliebige Python-Werte unverändert zurückgibt."""

from typing import Any

from PySide6.QtWidgets import QComboBox, QWidget


class Auswahl(QComboBox):
    """``QComboBox``, deren Einträge Python-Werte tragen.

    Qt wandelt ``StrEnum``-Werte und ``None`` beim Speichern als Item-Daten in
    einfache Zeichenketten bzw. ungültige Werte um. Diese Klasse hält die Werte
    deshalb in einer eigenen Liste parallel zu den Einträgen.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Erzeugt eine leere Auswahlliste."""
        super().__init__(parent)
        self._werte: list[Any] = []

    def addItem(self, text: str, wert: Any = None) -> None:  # noqa: N802 – Qt-Methodenname
        """Fügt einen Eintrag mit Anzeigetext und Wert hinzu."""
        self._werte.append(wert)
        super().addItem(text)

    def clear(self) -> None:
        """Entfernt alle Einträge."""
        self._werte.clear()
        super().clear()

    def currentData(self, *_: Any) -> Any:  # noqa: N802 – Qt-Methodenname
        """Wert des gewählten Eintrags oder ``None``."""
        index = self.currentIndex()
        return self._werte[index] if 0 <= index < len(self._werte) else None

    def findData(self, wert: Any, *_: Any) -> int:  # noqa: N802 – Qt-Methodenname
        """Index des ersten Eintrags mit diesem Wert oder -1."""
        for index, vorhanden in enumerate(self._werte):
            if vorhanden == wert and type(vorhanden) is type(wert):
                return index
        return -1
