"""Seite „Dashboard“."""

from PySide6.QtWidgets import QLabel, QVBoxLayout

from balanceos.praesentation.seiten.basis import Seite


class DashboardSeite(Seite):
    """Seite „Dashboard“ (vorläufig ohne Inhalt)."""

    titel = "Dashboard"

    def __init__(self, kontext, zustand) -> None:
        """Baut die Seite auf."""
        super().__init__(kontext, zustand)
        QVBoxLayout(self).addWidget(QLabel("Dashboard"))
