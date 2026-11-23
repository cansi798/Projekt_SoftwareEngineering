"""Seite „Reflexion“."""

from PySide6.QtWidgets import QLabel, QVBoxLayout

from balanceos.praesentation.seiten.basis import Seite


class ReflexionSeite(Seite):
    """Seite „Reflexion“ (vorläufig ohne Inhalt)."""

    titel = "Reflexion"

    def __init__(self, kontext, zustand) -> None:
        """Baut die Seite auf."""
        super().__init__(kontext, zustand)
        QVBoxLayout(self).addWidget(QLabel("Reflexion"))
