"""Basisklasse und Hilfsbausteine für die Seiten des Hauptfensters."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from balanceos.anwendung.kontext import AppKontext
from balanceos.praesentation.zustand import Zustand


class Seite(QWidget):
    """Eine Seite im Inhaltsbereich des Hauptfensters.

    Unterklassen setzen ``titel`` und überschreiben ``aktualisieren``. Die
    Seite lädt ihre Daten neu, sobald sich Daten oder die Woche ändern; ist sie
    gerade nicht sichtbar, holt sie das beim nächsten Anzeigen nach.
    """

    titel = ""

    def __init__(self, kontext: AppKontext, zustand: Zustand) -> None:
        """Verbindet die Seite mit Kontext und Zustand."""
        super().__init__()
        self.kontext = kontext
        self.zustand = zustand
        self._veraltet = True
        zustand.daten_geaendert.connect(self._geaendert)
        zustand.woche_geaendert.connect(self._geaendert)

    def _geaendert(self, *_: object) -> None:
        if self.isVisible():
            self.aktualisieren()
            self._veraltet = False
        else:
            self._veraltet = True

    def showEvent(self, event) -> None:  # noqa: N802 – Qt-Methodenname
        """Lädt veraltete Daten beim Anzeigen nach."""
        super().showEvent(event)
        if self._veraltet:
            self.aktualisieren()
            self._veraltet = False

    def aktualisieren(self) -> None:
        """Lädt die Anzeige neu. Unterklassen überschreiben diese Methode."""


def karte(titel: str | None = None) -> tuple[QFrame, QVBoxLayout]:
    """Erzeugt einen weißen Kasten mit optionalem Titel und liefert sein Layout."""
    rahmen = QFrame()
    rahmen.setObjectName("karte")
    layout = QVBoxLayout(rahmen)
    layout.setContentsMargins(16, 12, 16, 14)
    if titel:
        kopf = QLabel(titel)
        kopf.setObjectName("kartentitel")
        layout.addWidget(kopf)
    return rahmen, layout


def scrollbar(inhalt: QWidget) -> QScrollArea:
    """Bettet ein Widget in einen rahmenlosen, vertikal scrollbaren Bereich ein."""
    bereich = QScrollArea()
    bereich.setWidgetResizable(True)
    bereich.setFrameShape(QFrame.Shape.NoFrame)
    bereich.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    bereich.setWidget(inhalt)
    return bereich


def etikett(text: str, farbe: str) -> QLabel:
    """Kleines farbiges Etikett, z. B. für die Evidenzart."""
    label = QLabel(text)
    label.setObjectName("etikett")
    label.setStyleSheet(f"background: {farbe};")
    return label
