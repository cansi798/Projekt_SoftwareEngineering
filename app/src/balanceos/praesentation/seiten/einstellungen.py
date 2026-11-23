"""Seite „Einstellungen“."""

from PySide6.QtWidgets import QLabel, QVBoxLayout

from balanceos.praesentation.seiten.basis import Seite


class EinstellungenSeite(Seite):
    """Seite „Einstellungen“ (vorläufig ohne Inhalt)."""

    titel = "Einstellungen"

    def __init__(self, kontext, zustand) -> None:
        """Baut die Seite auf."""
        super().__init__(kontext, zustand)
        QVBoxLayout(self).addWidget(QLabel("Einstellungen"))
