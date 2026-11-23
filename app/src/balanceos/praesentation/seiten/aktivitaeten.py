"""Seite „Aktivitäten“."""

from PySide6.QtWidgets import QLabel, QVBoxLayout

from balanceos.praesentation.seiten.basis import Seite


class AktivitaetenSeite(Seite):
    """Seite „Aktivitäten“ (vorläufig ohne Inhalt)."""

    titel = "Aktivitäten"

    def __init__(self, kontext, zustand) -> None:
        """Baut die Seite auf."""
        super().__init__(kontext, zustand)
        QVBoxLayout(self).addWidget(QLabel("Aktivitäten"))
