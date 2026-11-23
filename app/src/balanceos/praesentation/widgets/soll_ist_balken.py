"""Soll-Ist-Balken eines Lebensbereichs für das Dashboard (US11)."""

from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from balanceos.domaene.modell import Bereichsbewertung
from balanceos.domaene.typen import Bereichstyp
from balanceos.praesentation.stil import GRUEN, ROT

SKALA = 1.5
"""Der Balken reicht bis 150 % des Solls."""


def _h(stunden: float) -> str:
    text = f"{stunden:.1f}".replace(".", ",")
    return text[:-2] if text.endswith(",0") else text


class SollIstBalken(QWidget):
    """Horizontaler Balken mit Ist-Wert und Marke beim Soll.

    Bei einem Mindestziel wird der Balken grün, sobald das Soll erreicht ist,
    vorher erscheint er in der Bereichsfarbe. Bei einer Obergrenze erscheint
    der Teil bis zum Soll in der Bereichsfarbe und die Überschreitung rot.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Erzeugt einen leeren Balken."""
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._ist = 0.0
        self._soll = 0.0
        self._typ = Bereichstyp.MINDESTZIEL
        self._farbe = QColor("#868E96")

    def sizeHint(self) -> QSize:  # noqa: N802 – Qt-Methodenname
        """Bevorzugte Größe."""
        return QSize(260, 18)

    def setze(self, bewertung: Bereichsbewertung, typ: Bereichstyp, farbe: str) -> None:
        """Übernimmt Ist, Soll, Bereichstyp und Farbe."""
        self._ist = bewertung.ist_stunden
        self._soll = bewertung.soll_stunden
        self._typ = typ
        self._farbe = QColor(farbe)
        self.setToolTip(f"Ist {self.text()} (Balken bis 150 % des Solls)")
        self.update()

    def text(self) -> str:
        """Beschriftung „Ist / Soll h“, z. B. „46 / 40 h“."""
        return f"{_h(self._ist)} / {_h(self._soll)} h"

    def anteile(self) -> tuple[float, float]:
        """Anteile der Balkenbreite (normaler Teil, roter Überschreitungsteil) zwischen 0 und 1."""
        if self._soll <= 0:
            return (0.0, 0.0)
        maximum = SKALA * self._soll
        ist = min(self._ist, maximum)
        if self._typ is Bereichstyp.OBERGRENZE and ist > self._soll:
            return (self._soll / maximum, (ist - self._soll) / maximum)
        return (ist / maximum, 0.0)

    def paintEvent(self, event) -> None:  # noqa: N802 – Qt-Methodenname
        """Zeichnet Hintergrund, Ist-Teile und Sollmarke."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        hoehe = 12.0
        y = (self.height() - hoehe) / 2
        breite = self.width() - 2.0
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#E9ECEF"))
        p.drawRoundedRect(QRectF(1, y, breite, hoehe), 3, 3)
        if self._soll > 0:
            normal, rot = self.anteile()
            erreicht = self._typ is Bereichstyp.MINDESTZIEL and self._ist >= self._soll
            p.setBrush(QColor(GRUEN) if erreicht else self._farbe)
            p.drawRoundedRect(QRectF(1, y, breite * normal, hoehe), 3, 3)
            if rot > 0:
                p.setBrush(QColor(ROT))
                p.drawRect(QRectF(1 + breite * normal, y, breite * rot, hoehe))
            x_soll = 1 + breite / SKALA
            p.setPen(QPen(QColor("#212529"), 2))
            p.drawLine(int(x_soll), int(y - 3), int(x_soll), int(y + hoehe + 3))
        p.end()
