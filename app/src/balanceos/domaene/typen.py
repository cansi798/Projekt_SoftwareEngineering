"""Aufzählungstypen des Datenmodells.

Die Werte entsprechen exakt den Literalen der Spezifikation (Tabelle
„Aufzählungstypen“), weil sie unverändert in den CSV- und JSON-Export
übernommen werden.
"""

from datetime import date
from enum import StrEnum


class Bereichstyp(StrEnum):
    """Art des Ziels eines Lebensbereichs."""

    MINDESTZIEL = "MINDESTZIEL"
    """Mehr Zeit ist bis zum Soll besser (z. B. Schlaf)."""
    OBERGRENZE = "OBERGRENZE"
    """Eine Überschreitung des Solls ist ungünstig (z. B. Arbeit)."""


class Aktivitaetsstatus(StrEnum):
    """Bearbeitungsstand einer Aktivität."""

    GEPLANT = "GEPLANT"
    DURCHGEFUEHRT = "DURCHGEFUEHRT"
    AUSGEFALLEN = "AUSGEFALLEN"


class Bewegungsart(StrEnum):
    """Art einer Bewegungsaktivität; Grundlage der Regeln R01 und R02."""

    AUSDAUER_MODERAT = "AUSDAUER_MODERAT"
    AUSDAUER_INTENSIV = "AUSDAUER_INTENSIV"
    KRAFT = "KRAFT"


class Evidenzart(StrEnum):
    """Art der wissenschaftlichen Grundlage eines Modells, Hinweises oder Scores."""

    THEORIE = "THEORIE"
    EMPFEHLUNG = "EMPFEHLUNG"
    VALIDIERTES_INSTRUMENT = "VALIDIERTES_INSTRUMENT"
    PERSOENLICHE_REGEL = "PERSOENLICHE_REGEL"
    PROGRAMMEIGEN = "PROGRAMMEIGEN"


EVIDENZ_TEXT: dict[Evidenzart, str] = {
    Evidenzart.THEORIE: "Theorie",
    Evidenzart.EMPFEHLUNG: "Empfehlung",
    Evidenzart.VALIDIERTES_INSTRUMENT: "validiertes Instrument",
    Evidenzart.PERSOENLICHE_REGEL: "persönliche Regel",
    Evidenzart.PROGRAMMEIGEN: "programmeigen",
}
"""Anzeigetexte der Evidenzarten für die Oberfläche."""


class Hinweisart(StrEnum):
    """Art eines Hinweises; bestimmt auch die Sortierung im Dashboard."""

    WARNUNG = "WARNUNG"
    POSITIV = "POSITIV"
    SYSTEM = "SYSTEM"


class Wochentag(StrEnum):
    """Wochentage von Montag bis Sonntag."""

    MO = "MO"
    DI = "DI"
    MI = "MI"
    DO = "DO"
    FR = "FR"
    SA = "SA"
    SO = "SO"

    @property
    def index(self) -> int:
        """Position in der Woche (Montag = 0, Sonntag = 6)."""
        return list(Wochentag).index(self)

    @classmethod
    def aus_datum(cls, tag: date) -> "Wochentag":
        """Liefert den Wochentag eines Datums."""
        return list(cls)[tag.weekday()]


class StandardSchluessel(StrEnum):
    """Feste Kennung der zehn Standardbereiche.

    Regeln finden ihren Bereich über diesen Schlüssel und nicht über den
    Namen, damit sie auch nach dem Umbenennen eines Standardbereichs greifen.
    """

    ARBEIT = "ARBEIT"
    SCHLAF = "SCHLAF"
    BEWEGUNG = "BEWEGUNG"
    FAMILIE = "FAMILIE"
    HOBBYS = "HOBBYS"
    SOZIALE_KONTAKTE = "SOZIALE_KONTAKTE"
    FREIZEIT = "FREIZEIT"
    ERHOLUNG = "ERHOLUNG"
    PERSOENLICHE_ENTWICKLUNG = "PERSOENLICHE_ENTWICKLUNG"
    VERPFLICHTUNGEN = "VERPFLICHTUNGEN"
