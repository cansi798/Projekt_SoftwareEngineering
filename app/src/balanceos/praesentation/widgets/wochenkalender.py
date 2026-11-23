"""Wochenkalender von Montag bis Sonntag mit Zeitachse 0–24 Uhr (US09)."""

from datetime import date, time, timedelta

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus
from balanceos.praesentation.texte import STATUS_TEXT, WOCHENTAG_TEXT

WOCHENTAGE = list(WOCHENTAG_TEXT.values())

ACHSE = 46
KOPF = 38
ZEILE_OHNE = 22
MIN_STUNDE = 20


def _minuten(t: time) -> int:
    return t.hour * 60 + t.minute


class Wochenkalender(QWidget):
    """Zeichnet die Aktivitäten einer Woche als farbige Blöcke.

    Die Farbe zeigt den Lebensbereich, die Darstellung den Status: geplant
    (heller Block mit Rahmen), durchgeführt (gefüllt), ausgefallen
    (schraffiert und durchgestrichen). Aktivitäten über Mitternacht werden auf
    zwei Tage verteilt gezeichnet, zählen aber zum Tag des Beginns. Aktivitäten
    ohne Uhrzeit stehen in einer eigenen Zeile oberhalb der Zeitachse.
    """

    aktivitaet_doppelklick = Signal(int)
    freie_flaeche_doppelklick = Signal(object, object)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Erzeugt einen leeren Kalender."""
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setMinimumHeight(KOPF + ZEILE_OHNE + 24 * MIN_STUNDE)
        self._montag = date.today()
        self._heute = date.today()
        self._aktivitaeten: list[Aktivitaet] = []
        self._farben: dict[int, str] = {}
        self._namen: dict[int, str] = {}
        self._bloecke: list[tuple[int, QRectF, bool]] = []
        self._ohne_zeilen = 1

    def sizeHint(self) -> QSize:  # noqa: N802 – Qt-Methodenname
        """Bevorzugte Größe mit 22 Pixeln je Stunde."""
        return QSize(900, KOPF + self._ohne_hoehe() + 24 * 22)

    def setze(
        self,
        kw,
        aktivitaeten: list[Aktivitaet],
        farben: dict[int, str],
        heute: date,
        namen: dict[int, str] | None = None,
    ) -> None:
        """Übernimmt Woche, Aktivitäten und Bereichsfarben und zeichnet neu."""
        self._montag = kw.montag()
        self._heute = heute
        self._aktivitaeten = list(aktivitaeten)
        self._farben = farben
        self._namen = namen or {}
        pro_tag: dict[date, int] = {}
        for a in self._aktivitaeten:
            if a.beginn is None:
                pro_tag[a.datum] = pro_tag.get(a.datum, 0) + 1
        self._ohne_zeilen = max([1, *pro_tag.values()])
        self.updateGeometry()
        self._layout_berechnen()
        self.update()

    # --- Geometrie ------------------------------------------------------------------------

    def _ohne_hoehe(self) -> int:
        return ZEILE_OHNE * self._ohne_zeilen + 6

    def _spaltenbreite(self) -> float:
        return (self.width() - ACHSE) / 7

    def _oben_zeitachse(self) -> float:
        return KOPF + self._ohne_hoehe()

    def _stundenhoehe(self) -> float:
        return max(1.0, (self.height() - self._oben_zeitachse() - 4) / 24)

    def _x(self, tag_index: int) -> float:
        return ACHSE + tag_index * self._spaltenbreite()

    def _y(self, minuten: int) -> float:
        return self._oben_zeitachse() + minuten / 60 * self._stundenhoehe()

    def punkt_fuer(self, tag_index: int, zeit: time) -> QPointF:
        """Bildschirmpunkt in der Spalte ``tag_index`` zur Uhrzeit ``zeit``."""
        return QPointF(self._x(tag_index) + self._spaltenbreite() / 2, self._y(_minuten(zeit)) + 1)

    def position_zu_zeit(self, punkt: QPointF) -> tuple[date | None, time | None]:
        """Tag und auf 30 Minuten abgerundete Uhrzeit an einem Punkt.

        In der Zeile „ohne Uhrzeit“ ist die Uhrzeit ``None``; außerhalb der
        Tagesspalten ist der Tag ``None``.
        """
        if punkt.x() < ACHSE or punkt.y() < KOPF:
            return None, None
        index = min(6, int((punkt.x() - ACHSE) // self._spaltenbreite()))
        tag = self._montag + timedelta(days=index)
        if punkt.y() < self._oben_zeitachse():
            return tag, None
        minuten = int((punkt.y() - self._oben_zeitachse()) / self._stundenhoehe() * 60)
        minuten = max(0, min(23 * 60 + 30, minuten // 30 * 30))
        return tag, time(minuten // 60, minuten % 60)

    def _layout_berechnen(self) -> None:
        """Berechnet die Rechtecke aller Blöcke; überlappende stehen nebeneinander."""
        self._bloecke = []
        breite = self._spaltenbreite()
        teile: dict[int, list[tuple[Aktivitaet, int, int, bool]]] = {i: [] for i in range(7)}
        ohne: dict[int, list[Aktivitaet]] = {i: [] for i in range(7)}
        for a in self._aktivitaeten:
            index = (a.datum - self._montag).days
            if not 0 <= index <= 6:
                continue
            if a.beginn is None:
                ohne[index].append(a)
                continue
            start = _minuten(a.beginn)
            ende = start + a.dauer_minuten
            teile[index].append((a, start, min(ende, 24 * 60), ende > 24 * 60 and index == 6))
            if ende > 24 * 60 and index < 6:
                teile[index + 1].append((a, 0, ende - 24 * 60, False))
        for index in range(7):
            for nr, a in enumerate(ohne[index]):
                rechteck = QRectF(
                    self._x(index) + 2, KOPF + 3 + nr * ZEILE_OHNE, breite - 4, ZEILE_OHNE - 3
                )
                self._bloecke.append((a.id, rechteck, False))
            spalten_ende: list[int] = []
            belegung: list[tuple[Aktivitaet, int, int, bool, int]] = []
            for a, start, ende, folgetag in sorted(teile[index], key=lambda t: (t[1], -t[2])):
                spalte = next((i for i, e in enumerate(spalten_ende) if e <= start), None)
                if spalte is None:
                    spalten_ende.append(ende)
                    spalte = len(spalten_ende) - 1
                else:
                    spalten_ende[spalte] = ende
                belegung.append((a, start, ende, folgetag, spalte))
            anzahl = max(1, len(spalten_ende))
            teilbreite = (breite - 4) / anzahl
            for a, start, ende, folgetag, spalte in belegung:
                y1, y2 = self._y(start), self._y(ende)
                rechteck = QRectF(
                    self._x(index) + 2 + spalte * teilbreite, y1, teilbreite - 1, max(6.0, y2 - y1)
                )
                self._bloecke.append((a.id, rechteck, folgetag))

    def bloecke(self) -> list[tuple[int, QRectF]]:
        """Gezeichnete Blöcke als Paare aus Aktivitäts-ID und Rechteck."""
        return [(i, r) for i, r, _ in self._bloecke]

    def id_an(self, punkt: QPointF) -> int | None:
        """ID der Aktivität unter einem Punkt oder ``None``."""
        for aktivitaet_id, rechteck, _ in reversed(self._bloecke):
            if rechteck.contains(punkt):
                return aktivitaet_id
        return None

    # --- Ereignisse -----------------------------------------------------------------------

    def resizeEvent(self, event) -> None:  # noqa: N802 – Qt-Methodenname
        """Berechnet die Blöcke bei Größenänderung neu."""
        super().resizeEvent(event)
        self._layout_berechnen()

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802
        """Doppelklick: Block bearbeiten oder an freier Stelle neu erfassen."""
        punkt = event.position()
        aktivitaet_id = self.id_an(punkt)
        if aktivitaet_id is not None:
            self.aktivitaet_doppelklick.emit(aktivitaet_id)
            return
        tag, zeit = self.position_zu_zeit(punkt)
        if tag is not None:
            self.freie_flaeche_doppelklick.emit(tag, zeit)

    def event(self, ereignis) -> bool:
        """Zeigt beim Zeigen auf einen Block dessen Angaben als Tooltip."""
        if ereignis.type() == ereignis.Type.ToolTip:
            aktivitaet_id = self.id_an(QPointF(ereignis.pos()))
            a = next((x for x in self._aktivitaeten if x.id == aktivitaet_id), None)
            if a is None:
                QToolTip.hideText()
            else:
                QToolTip.showText(ereignis.globalPos(), self._tooltip(a), self)
            return True
        return super().event(ereignis)

    def _tooltip(self, a: Aktivitaet) -> str:
        zeit = f"{a.beginn:%H:%M}–{a.ende:%H:%M}, " if a.beginn and a.ende else ""
        bereich = self._namen.get(a.lebensbereich_id, "")
        folgetag = " (endet am Folgetag)" if a.ueber_mitternacht else ""
        return (
            f"{a.titel}\n{bereich}\n{zeit}{a.dauer_minuten} min{folgetag}\n{STATUS_TEXT[a.status]}"
        )

    # --- Zeichnen -------------------------------------------------------------------------

    def paintEvent(self, event) -> None:  # noqa: N802 – Qt-Methodenname
        """Zeichnet Raster, Tagesköpfe und Blöcke."""
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor("#FFFFFF"))
        breite = self._spaltenbreite()
        leise = QColor("#868E96")
        linie = QPen(QColor("#E9ECEF"))
        heute_index = (self._heute - self._montag).days
        if 0 <= heute_index <= 6:
            p.fillRect(QRectF(self._x(heute_index), 0, breite, self.height()), QColor("#F4FCF5"))
        kopf_schrift = QFont(self.font())
        kopf_schrift.setBold(True)
        for i in range(7):
            tag = self._montag + timedelta(days=i)
            p.setPen(QColor("#2F9E44") if i == heute_index else QColor("#212529"))
            p.setFont(kopf_schrift)
            p.drawText(
                QRectF(self._x(i), 4, breite, KOPF - 8),
                Qt.AlignmentFlag.AlignCenter,
                f"{WOCHENTAGE[i]} {tag:%d.%m.}",
            )
            p.setPen(linie)
            p.drawLine(QPointF(self._x(i), KOPF), QPointF(self._x(i), self.height()))
        p.setFont(self.font())
        p.setPen(leise)
        p.drawText(
            QRectF(0, KOPF, ACHSE - 4, self._ohne_hoehe()),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            "ohne\nZeit",
        )
        for stunde in range(25):
            y = self._y(stunde * 60)
            p.setPen(linie)
            p.drawLine(QPointF(ACHSE, y), QPointF(self.width(), y))
            if stunde < 24 and stunde % 2 == 0:
                p.setPen(leise)
                p.drawText(
                    QRectF(0, y - 8, ACHSE - 6, 16),
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                    f"{stunde:02d}:00",
                )
        p.setPen(QPen(QColor("#CED4DA")))
        p.drawLine(QPointF(ACHSE, KOPF), QPointF(self.width(), KOPF))
        nach_id = {a.id: a for a in self._aktivitaeten}
        for aktivitaet_id, rechteck, folgetag in self._bloecke:
            self._block(p, nach_id[aktivitaet_id], rechteck, folgetag)
        p.end()

    def _block(self, p: QPainter, a: Aktivitaet, r: QRectF, folgetag: bool) -> None:
        farbe = QColor(self._farben.get(a.lebensbereich_id, "#868E96"))
        schrift = QFont(self.font())
        schrift.setPointSizeF(max(7.0, self.font().pointSizeF() - 1.5))
        if a.status is Aktivitaetsstatus.DURCHGEFUEHRT:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(farbe)
            textfarbe = QColor("white")
        elif a.status is Aktivitaetsstatus.GEPLANT:
            hell = QColor(farbe)
            hell.setAlpha(45)
            p.setPen(QPen(farbe, 1.5))
            p.setBrush(hell)
            textfarbe = farbe.darker(140)
        else:
            p.setPen(QPen(QColor("#ADB5BD"), 1))
            p.setBrush(QBrush(QColor("#ADB5BD"), Qt.BrushStyle.BDiagPattern))
            textfarbe = QColor("#495057")
            schrift.setStrikeOut(True)
        p.drawRoundedRect(r, 4, 4)
        if r.height() >= 12:
            p.setPen(textfarbe)
            p.setFont(schrift)
            text = a.titel + (" → Folgetag" if folgetag else "")
            p.drawText(
                r.adjusted(4, 1, -3, -1),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap,
                text,
            )
