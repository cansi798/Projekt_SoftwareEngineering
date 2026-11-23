"""Kalenderwochen nach ISO 8601, Dauerberechnung, Rundung und Zahlenformate."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

MAX_DAUER_MINUTEN = 1440
"""Größte zulässige Dauer einer Aktivität (GR10)."""


@dataclass(frozen=True, order=True)
class KW:
    """Kalenderwoche nach ISO 8601 (Montag bis Sonntag)."""

    jahr: int
    woche: int

    @classmethod
    def aus_datum(cls, tag: date) -> "KW":
        """Liefert die Kalenderwoche, in der ``tag`` liegt."""
        iso = tag.isocalendar()
        return cls(iso.year, iso.week)

    @classmethod
    def heute(cls, heute: date) -> "KW":
        """Liefert die Kalenderwoche des übergebenen Tagesdatums."""
        return cls.aus_datum(heute)

    def montag(self) -> date:
        """Erster Tag der Woche."""
        return date.fromisocalendar(self.jahr, self.woche, 1)

    def sonntag(self) -> date:
        """Letzter Tag der Woche."""
        return date.fromisocalendar(self.jahr, self.woche, 7)

    def tage(self) -> list[date]:
        """Alle sieben Tage der Woche von Montag bis Sonntag."""
        start = self.montag()
        return [start + timedelta(days=i) for i in range(7)]

    def verschoben(self, wochen: int) -> "KW":
        """Liefert die Woche, die ``wochen`` Wochen später (negativ: früher) liegt."""
        return KW.aus_datum(self.montag() + timedelta(weeks=wochen))

    def label(self) -> str:
        """Anzeigeform, z. B. ``KW 46/2026``."""
        return f"KW {self.woche}/{self.jahr}"

    def iso(self) -> str:
        """ISO-Form für den Export, z. B. ``2026-W46``."""
        return f"{self.jahr}-W{self.woche:02d}"

    def zeitraum_text(self) -> str:
        """Woche mit Datumsbereich, z. B. ``KW 46/2026 (09.11.–15.11.2026)``."""
        return f"{self.label()} ({self.montag():%d.%m.}–{self.sonntag():%d.%m.%Y})"


def berechne_dauer(beginn: time | None, ende: time | None, dauer_minuten: int | None) -> int:
    """Ermittelt die Dauer einer Aktivität in Minuten (GR10, GR11).

    Sind Beginn und Ende angegeben, wird die Dauer daraus berechnet. Liegt das
    Ende vor dem Beginn, verläuft die Aktivität über Mitternacht und es werden
    24 Stunden addiert. Andernfalls gilt die direkt angegebene Dauer.

    Raises:
        ValueError: bei Ende ohne Beginn, gleichem Beginn und Ende, fehlender
            Dauer oder einer Dauer außerhalb von 1 bis 1440 Minuten.
    """
    if ende is not None and beginn is None:
        raise ValueError("Ein Ende ist nur zusammen mit einem Beginn zulässig.")
    if beginn is not None and ende is not None:
        if beginn == ende:
            raise ValueError("Beginn und Ende dürfen nicht gleich sein.")
        start = datetime.combine(date.min, beginn)
        stop = datetime.combine(date.min, ende)
        minuten = int((stop - start).total_seconds() // 60)
        if minuten < 0:
            minuten += 24 * 60
        return minuten
    if dauer_minuten is None or not 1 <= dauer_minuten <= MAX_DAUER_MINUTEN:
        raise ValueError("Die Dauer muss zwischen 1 und 1440 Minuten liegen.")
    return dauer_minuten


def kaufmaennisch_runden(wert: float) -> int:
    """Rundet kaufmännisch auf eine ganze Zahl (0,5 wird stets aufgerundet).

    Über ``repr`` wird der kürzeste Dezimalwert des Floats verwendet, damit
    Rechenrauschen wie ``65.00000000000001`` keine Rolle spielt.
    """
    return int(Decimal(repr(float(wert))).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def zahl_text(wert: float, stellen: int = 1) -> str:
    """Formatiert eine Zahl mit deutschem Dezimalkomma, z. B. ``4,3``."""
    gerundet = Decimal(repr(float(wert))).quantize(Decimal(1).scaleb(-stellen), ROUND_HALF_UP)
    return f"{gerundet:.{stellen}f}".replace(".", ",")


def stunden_text(stunden: float) -> str:
    """Formatiert Stunden mit einer Nachkommastelle, z. B. ``6,5 h``."""
    return f"{zahl_text(stunden)} h"
