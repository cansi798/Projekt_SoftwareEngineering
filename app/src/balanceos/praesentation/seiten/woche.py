"""Seite „Woche“."""

from PySide6.QtWidgets import QLabel, QVBoxLayout

from balanceos.praesentation.seiten.basis import Seite


class WocheSeite(Seite):
    """Seite „Woche“ (vorläufig ohne Inhalt)."""

    titel = "Woche"

    def __init__(self, kontext, zustand) -> None:
        """Baut die Seite auf."""
        super().__init__(kontext, zustand)
        QVBoxLayout(self).addWidget(QLabel("Woche"))
