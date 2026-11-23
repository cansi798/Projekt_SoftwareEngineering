"""Seite „Kompass“."""

from PySide6.QtWidgets import QLabel, QVBoxLayout

from balanceos.praesentation.seiten.basis import Seite


class KompassSeite(Seite):
    """Seite „Kompass“ (vorläufig ohne Inhalt)."""

    titel = "Kompass"

    def __init__(self, kontext, zustand) -> None:
        """Baut die Seite auf."""
        super().__init__(kontext, zustand)
        QVBoxLayout(self).addWidget(QLabel("Kompass"))
