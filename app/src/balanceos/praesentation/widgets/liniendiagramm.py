"""Liniendiagramm für Score-Verläufe (0–100), gezeichnet mit QPainter (US21)."""

from collections.abc import Iterable

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QCheckBox, QGridLayout, QSizePolicy, QVBoxLayout, QWidget

Reihe = tuple[str, str, list[int | None]]
"""Name, Farbe (Hex) und ein Wert je Beschriftung; ``None`` erzeugt eine Lücke."""

RAND_LINKS, RAND_RECHTS, RAND_OBEN, RAND_UNTEN = 40, 16, 12, 28
LEGENDE_SPALTEN = 4


class _Zeichenflaeche(QWidget):
    """Zeichnet Achsen, Gitter und die sichtbaren Reihen des Diagramms."""

    def __init__(self, diagramm: "Liniendiagramm") -> None:
        super().__init__(diagramm)
        self._d = diagramm
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def paintEvent(self, _event) -> None:  # noqa: N802 – Qt-Methodenname
        """Zeichnet Gitter, Achsen und eine Linie je Lebensbereich."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("white"))
        flaeche = QRectF(
            RAND_LINKS,
            RAND_OBEN,
            max(1, self.width() - RAND_LINKS - RAND_RECHTS),
            max(1, self.height() - RAND_OBEN - RAND_UNTEN),
        )
        self._gitter(p, flaeche)
        n = len(self._d.beschriftungen)
        if n == 0:
            return

        def punkt(i: int, wert: int) -> QPointF:
            """Rechnet Woche ``i`` und Prozentwert in Bildpunkte um."""
            x = flaeche.left() + (flaeche.width() * (i + 0.5) / n)
            y = flaeche.bottom() - flaeche.height() * wert / 100
            return QPointF(x, y)

        p.setPen(QColor("#495057"))
        for i, text in enumerate(self._d.beschriftungen):
            x = punkt(i, 0).x()
            p.drawText(
                QRectF(x - 40, flaeche.bottom() + 4, 80, RAND_UNTEN - 4),
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                text,
            )
        for name, farbe, werte in self._d.reihen:
            if name not in self._d.sichtbare_reihen():
                continue
            stift = QPen(QColor(farbe), 2)
            if name in self._d.gestrichelt:
                stift.setStyle(Qt.PenStyle.DashLine)
                stift.setWidth(3)
            p.setPen(stift)
            vorher: QPointF | None = None
            for i, wert in enumerate(werte):
                if wert is None:
                    vorher = None
                    continue
                aktuell = punkt(i, wert)
                if vorher is not None:
                    p.drawLine(vorher, aktuell)
                p.setBrush(QColor(farbe))
                p.drawEllipse(aktuell, 3, 3)
                vorher = aktuell
        p.end()

    @staticmethod
    def _gitter(p: QPainter, flaeche: QRectF) -> None:
        for wert in range(0, 101, 25):
            y = flaeche.bottom() - flaeche.height() * wert / 100
            p.setPen(QPen(QColor("#DEE2E6"), 1))
            p.drawLine(QPointF(flaeche.left(), y), QPointF(flaeche.right(), y))
            p.setPen(QColor("#6C757D"))
            p.drawText(
                QRectF(0, y - 8, RAND_LINKS - 6, 16),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                str(wert),
            )


class Liniendiagramm(QWidget):
    """Diagramm mit Y-Achse 0–100 und Legende zum Ein- und Ausblenden der Reihen."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Erzeugt ein leeres Diagramm."""
        super().__init__(parent)
        self.beschriftungen: list[str] = []
        self.reihen: list[Reihe] = []
        self.gestrichelt: set[str] = set()
        self.legende_felder: dict[str, QCheckBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.flaeche = _Zeichenflaeche(self)
        layout.addWidget(self.flaeche, 1)
        self._legende = QGridLayout()
        self._legende.setHorizontalSpacing(16)
        layout.addLayout(self._legende)

    def setze_reihen(
        self,
        beschriftungen: list[str],
        reihen: list[Reihe],
        gestrichelt: Iterable[str] = (),
    ) -> None:
        """Setzt X-Beschriftungen und Reihen; ausgeblendete Reihen bleiben ausgeblendet."""
        ausgeblendet = {n for n, feld in self.legende_felder.items() if not feld.isChecked()}
        self.beschriftungen = list(beschriftungen)
        self.reihen = list(reihen)
        self.gestrichelt = set(gestrichelt)
        while self._legende.count():
            widget = self._legende.takeAt(0).widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.legende_felder = {}
        for nr, (name, farbe, _) in enumerate(self.reihen):
            feld = QCheckBox(name)
            linie = "dashed" if name in self.gestrichelt else "solid"
            feld.setStyleSheet(
                f"QCheckBox {{ border-left: 4px {linie} {farbe}; padding-left: 4px; }}"
            )
            feld.setChecked(name not in ausgeblendet)
            feld.toggled.connect(self.flaeche.update)
            self.legende_felder[name] = feld
            self._legende.addWidget(feld, nr // LEGENDE_SPALTEN, nr % LEGENDE_SPALTEN)
        self.flaeche.update()

    def sichtbare_reihen(self) -> list[str]:
        """Namen der Reihen, deren Kontrollkästchen gesetzt ist, in Reihenfolge."""
        return [n for n, _, _ in self.reihen if self.legende_felder[n].isChecked()]
