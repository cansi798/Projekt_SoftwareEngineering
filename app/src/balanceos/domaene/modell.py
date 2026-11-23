"""Geschäftsobjekte von BalanceOS (Datenmodell der Spezifikation, Kapitel 1).

Die Klassen sind einfache Datencontainer ohne Abhängigkeit zu Oberfläche oder
Datenbank. Attributnamen folgen PEP 8 (snake_case); der Export übersetzt sie
in die camelCase-Bezeichner des Datenmodells.
"""

from dataclasses import dataclass, field
from datetime import date, time

from balanceos.domaene.kalender import KW
from balanceos.domaene.typen import (
    Aktivitaetsstatus,
    Bereichstyp,
    Bewegungsart,
    Evidenzart,
    Hinweisart,
    StandardSchluessel,
    Wochentag,
)


@dataclass(slots=True)
class Lebensbereich:
    """Kategorie des Alltags mit Wunschprofil (Soll-Stunden pro Woche)."""

    name: str
    typ: Bereichstyp
    farbe: str
    soll_stunden: float
    gewicht: int = 1
    aktiv: bool = True
    standard_schluessel: StandardSchluessel | None = None
    id: int | None = None

    @property
    def ist_standard(self) -> bool:
        """``True`` für die zehn Standardbereiche, die nicht gelöscht werden können."""
        return self.standard_schluessel is not None


@dataclass(slots=True)
class Aktivitaet:
    """Einzelner Eintrag mit Datum, Dauer, Status und optionalen Selbsteinschätzungen."""

    titel: str
    lebensbereich_id: int
    datum: date
    dauer_minuten: int
    status: Aktivitaetsstatus
    beginn: time | None = None
    ende: time | None = None
    zufriedenheit: int | None = None
    belastung: int | None = None
    erholung: int | None = None
    bewegungsart: Bewegungsart | None = None
    notiz: str | None = None
    ist_demo: bool = False
    serie_id: int | None = None
    einzeln_bearbeitet: bool = False
    id: int | None = None

    @property
    def stunden(self) -> float:
        """Dauer in Stunden."""
        return self.dauer_minuten / 60

    @property
    def ueber_mitternacht(self) -> bool:
        """``True``, wenn die Aktivität am Folgetag endet."""
        return self.beginn is not None and self.ende is not None and self.ende < self.beginn


@dataclass(slots=True)
class Wiederholungsserie:
    """Wöchentlich wiederkehrende Aktivität, aus der Termine erzeugt werden."""

    titel: str
    lebensbereich_id: int
    wochentage: frozenset[Wochentag]
    startdatum: date
    dauer_minuten: int
    enddatum: date | None = None
    beginn: time | None = None
    ausnahmen: set[date] = field(default_factory=set)
    generiert_bis: date | None = None
    id: int | None = None


@dataclass(slots=True)
class Einstellungen:
    """Parameter der Bewertung; existiert genau einmal."""

    alpha: float = 0.6
    gesamtscore_anzeigen: bool = False


@dataclass(slots=True)
class KompassModell:
    """Wissenschaftliches Modell, Empfehlung oder Systemregelwerk für den Balance-Kompass."""

    schluessel: str
    name: str
    kurzbeschreibung: str
    evidenzart: Evidenzart
    quelle: str
    grenzen: str


@dataclass(slots=True)
class Regel:
    """Prüfbare Bedingung R01–R10, die genau einem Kompass-Modell zugeordnet ist."""

    kennung: str
    bezeichnung: str
    modell_schluessel: str
    schwelle: float
    zeitraum: int
    aktiv: bool = True


@dataclass(frozen=True, slots=True)
class Begruendung:
    """Angaben für „Warum sehe ich das?“ (US13, NFA11) in fester Reihenfolge."""

    regel: str
    modell: str
    datenbasis: str
    zeitraum: str
    schwelle: str
    wert: str
    quelle: str
    evidenzart: str
    grenzen: str

    def zeilen(self) -> list[tuple[str, str]]:
        """Beschriftung und Inhalt in der Reihenfolge des Begründungsdialogs."""
        return [
            ("Regel", self.regel),
            ("Modell", self.modell),
            ("Datenbasis", self.datenbasis),
            ("Zeitraum", self.zeitraum),
            ("Schwelle", self.schwelle),
            ("Ihr Wert", self.wert),
            ("Quelle", self.quelle),
            ("Evidenzart", self.evidenzart),
            ("Grenzen", self.grenzen),
        ]


@dataclass(frozen=True, slots=True)
class Hinweis:
    """Regelbasierte Rückmeldung zu einer Kalenderwoche."""

    regel: str
    art: Hinweisart
    text: str
    begruendung: Begruendung
    kw: KW
    lebensbereich_id: int | None = None


@dataclass(frozen=True, slots=True)
class Bereichsbewertung:
    """Ergebnis eines Lebensbereichs in einer Woche.

    ``zielerfuellung`` ist ``None``, wenn für den Bereich kein Soll festgelegt
    ist; ``score`` ist ``None`` ohne Soll oder bei unzureichenden Daten.
    """

    lebensbereich_id: int
    ist_stunden: float
    soll_stunden: float
    zielerfuellung: float | None
    zufriedenheitsanteil: float | None
    score: int | None
    abweichung: float


@dataclass(frozen=True, slots=True)
class Wochenbewertung:
    """Abgeleitete Bewertung einer Kalenderwoche; wird stets neu berechnet."""

    kw: KW
    vollstaendigkeit_tage: int
    ausreichende_daten: bool
    bereiche: list[Bereichsbewertung]
    gesamtscore: int | None

    def bereich(self, lebensbereich_id: int) -> Bereichsbewertung | None:
        """Bewertung eines Lebensbereichs oder ``None``, falls er nicht bewertet wurde."""
        return next((b for b in self.bereiche if b.lebensbereich_id == lebensbereich_id), None)


@dataclass(slots=True)
class Who5Erhebung:
    """Ausgefüllter WHO-5-Fragebogen (US20)."""

    datum: date
    antworten: tuple[int, int, int, int, int]
    id: int | None = None

    @property
    def rohwert(self) -> int:
        """Summe der fünf Antworten (0–25)."""
        return sum(self.antworten)

    @property
    def prozentwert(self) -> int:
        """Rohwert mal vier (0–100)."""
        return self.rohwert * 4


@dataclass(slots=True)
class Wochenreflexion:
    """Reflexion einer Kalenderwoche zu drei Leitfragen (US22)."""

    kw: KW
    antworten: tuple[str, str, str]
    stimmung: int | None = None
    id: int | None = None
