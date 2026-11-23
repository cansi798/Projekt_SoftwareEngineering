"""Seite „Statistik“."""

from PySide6.QtWidgets import QLabel, QVBoxLayout

from balanceos.praesentation.seiten.basis import Seite


class StatistikSeite(Seite):
    """Seite „Statistik“ (vorläufig ohne Inhalt)."""

    titel = "Statistik"

    def __init__(self, kontext, zustand) -> None:
        """Baut die Seite auf."""
        super().__init__(kontext, zustand)
        QVBoxLayout(self).addWidget(QLabel("Statistik"))
