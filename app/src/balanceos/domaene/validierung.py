"""Prüfung von Eingaben gegen Geschäftsregeln und Gültigkeitsregeln der Eingabefelder.

Jede Prüffunktion liefert eine Liste von ``Fehler``-Objekten; eine leere Liste
bedeutet „gültig“. Die Meldungstexte stammen wörtlich aus der Tabelle
„Gültigkeitsregeln für Eingabefelder“ des Spezifikationsdokuments.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from balanceos.domaene.kalender import MAX_DAUER_MINUTEN, berechne_dauer
from balanceos.domaene.modell import Aktivitaet, Lebensbereich, Wiederholungsserie
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel

MAX_WOCHENSTUNDEN = 168
MAX_TITEL = 80
MAX_NAME = 40
MAX_NOTIZ = 500
MAX_LEITFRAGE = 1000

M_TITEL = "Bitte 1 bis 80 Zeichen eingeben."
M_BEREICH = "Bitte einen Lebensbereich wählen."
M_DATUM = "Bitte ein gültiges Datum eingeben."
M_ZEIT = "Format HH:MM; Beginn und Ende verschieden."
M_DAUER = "Dauer 1 bis 1.440 Minuten."
M_ZUKUNFT = "Zukünftige Aktivitäten sind noch nicht durchgeführt."
M_BEWERTUNG = "Bewertungen sind nur bei durchgeführten Aktivitäten von 1 bis 5 möglich."
M_BEWEGUNGSART = "Eine Bewegungsart ist nur im Bereich Bewegung möglich."
M_NOTIZ = "Höchstens 500 Zeichen."
M_WOCHENTAGE = "Bitte mindestens einen Wochentag wählen."
M_ENDDATUM = "Enddatum darf nicht vor dem Datum liegen."
M_NAME = "Bitte 1 bis 40 Zeichen eingeben."
M_NAME_DOPPELT = "Name existiert bereits."
M_AKTIV = "Mindestens ein aktiver Bereich braucht ein Soll."
M_SOLL = "0 bis 168 h in Schritten von 0,5 h."
M_SUMME = "Summe übersteigt 168 h pro Woche."
M_GEWICHT = "Ganze Zahl von 0 bis 10."
M_ALPHA = "Die Gewichtung liegt zwischen 0 und 1."
M_DATUM_ZUKUNFT = "Datum liegt in der Zukunft."
M_SKALA_WHO5 = "Jede Aussage wird mit 0 bis 5 beantwortet."
M_LEITFRAGE = "Höchstens 1.000 Zeichen."
M_STIMMUNG = "Stimmung 1 bis 5."
M_ZEITRAUM = "Ende vor Beginn des Zeitraums."
M_SPEICHERORT = "Hier kann nicht gespeichert werden."
M_LOESCHEN = "Bitte LÖSCHEN eingeben."
LOESCHWORT = "LÖSCHEN"


@dataclass(frozen=True, slots=True)
class Fehler:
    """Ein Verstoß gegen eine Gültigkeitsregel mit Feldbezug und Meldung."""

    feld: str
    meldung: str


def _laenge_ok(text: str | None, maximum: int) -> bool:
    return text is not None and 1 <= len(text.strip()) <= maximum


def pruefe_aktivitaet(a: Aktivitaet, bereich: Lebensbereich | None, heute: date) -> list[Fehler]:
    """Prüft eine Aktivität (GR05, GR09, GR10, GR12, GR13, GR15).

    Args:
        a: Zu prüfende Aktivität; ``a.id is None`` kennzeichnet eine neue Aktivität.
        bereich: Gewählter Lebensbereich oder ``None``.
        heute: Aktuelles Datum für die Prüfung von GR12.
    """
    fehler: list[Fehler] = []
    if not _laenge_ok(a.titel, MAX_TITEL):
        fehler.append(Fehler("titel", M_TITEL))
    if bereich is None or (a.id is None and not bereich.aktiv):
        fehler.append(Fehler("lebensbereich", M_BEREICH))
    if a.beginn is not None or a.ende is not None:
        try:
            berechne_dauer(a.beginn, a.ende, None)
        except ValueError:
            fehler.append(Fehler("zeit", M_ZEIT))
    elif not 1 <= a.dauer_minuten <= MAX_DAUER_MINUTEN:
        fehler.append(Fehler("dauer", M_DAUER))
    if a.status is Aktivitaetsstatus.DURCHGEFUEHRT and a.datum > heute:
        fehler.append(Fehler("status", M_ZUKUNFT))
    bewertungen = [w for w in (a.zufriedenheit, a.belastung, a.erholung) if w is not None]
    if bewertungen and (
        a.status is not Aktivitaetsstatus.DURCHGEFUEHRT or any(not 1 <= w <= 5 for w in bewertungen)
    ):
        fehler.append(Fehler("bewertung", M_BEWERTUNG))
    if a.bewegungsart is not None and (
        bereich is None or bereich.standard_schluessel is not StandardSchluessel.BEWEGUNG
    ):
        fehler.append(Fehler("bewegungsart", M_BEWEGUNGSART))
    if a.notiz is not None and len(a.notiz) > MAX_NOTIZ:
        fehler.append(Fehler("notiz", M_NOTIZ))
    return fehler


def pruefe_serie(s: Wiederholungsserie) -> list[Fehler]:
    """Prüft eine Wiederholungsserie (GR16)."""
    fehler: list[Fehler] = []
    if not s.wochentage:
        fehler.append(Fehler("wochentage", M_WOCHENTAGE))
    if s.enddatum is not None and s.enddatum < s.startdatum:
        fehler.append(Fehler("enddatum", M_ENDDATUM))
    if not 1 <= s.dauer_minuten <= MAX_DAUER_MINUTEN:
        fehler.append(Fehler("dauer", M_DAUER))
    return fehler


def pruefe_lebensbereich(b: Lebensbereich, alle: list[Lebensbereich]) -> list[Fehler]:
    """Prüft einen neuen oder geänderten Lebensbereich (GR01, GR02, GR06, GR07).

    Args:
        b: Bereich im geänderten Zustand.
        alle: Gespeicherter Bestand; ein Eintrag mit gleicher ID wird durch ``b`` ersetzt.
    """
    fehler: list[Fehler] = []
    andere = [x for x in alle if b.id is None or x.id != b.id]
    if not _laenge_ok(b.name, MAX_NAME):
        fehler.append(Fehler("name", M_NAME))
    elif any(x.name.strip().casefold() == b.name.strip().casefold() for x in andere):
        fehler.append(Fehler("name", M_NAME_DOPPELT))
    soll_ok = 0 <= b.soll_stunden <= MAX_WOCHENSTUNDEN and (b.soll_stunden * 2).is_integer()
    if not soll_ok:
        fehler.append(Fehler("soll", M_SOLL))
    if not (isinstance(b.gewicht, int) and 0 <= b.gewicht <= 10):
        fehler.append(Fehler("gewicht", M_GEWICHT))
    neu = [*andere, b]
    if soll_ok and sum(x.soll_stunden for x in neu if x.aktiv) > MAX_WOCHENSTUNDEN:
        fehler.append(Fehler("summe", M_SUMME))
    if not any(x.aktiv and x.soll_stunden > 0 for x in neu):
        fehler.append(Fehler("aktiv", M_AKTIV))
    return fehler


def pruefe_alpha(alpha: float) -> list[Fehler]:
    """Prüft den Anteil der Zielerfüllung am Score (GR08)."""
    return [] if 0 <= alpha <= 1 else [Fehler("alpha", M_ALPHA)]


def pruefe_who5(datum: date, antworten: Sequence[int | None], heute: date) -> list[Fehler]:
    """Prüft eine WHO-5-Erhebung (GR26)."""
    fehler: list[Fehler] = []
    if datum > heute:
        fehler.append(Fehler("datum", M_DATUM_ZUKUNFT))
    offen = sum(1 for a in antworten if a is None) + max(0, 5 - len(antworten))
    if offen:
        aussagen = "Aussage" if offen == 1 else "Aussagen"
        fehler.append(Fehler("antworten", f"Noch offen: {offen} {aussagen}."))
    elif any(not 0 <= a <= 5 for a in antworten):
        fehler.append(Fehler("antworten", M_SKALA_WHO5))
    return fehler


def pruefe_reflexion(antworten: Sequence[str], stimmung: int | None) -> list[Fehler]:
    """Prüft eine Wochenreflexion; die Antwortfelder heißen ``antwort1`` bis ``antwort3``."""
    fehler = [
        Fehler(f"antwort{nr}", M_LEITFRAGE)
        for nr, text in enumerate(antworten, start=1)
        if len(text) > MAX_LEITFRAGE
    ]
    if stimmung is not None and not 1 <= stimmung <= 5:
        fehler.append(Fehler("stimmung", M_STIMMUNG))
    return fehler


def pruefe_zeitraum(von: date, bis: date) -> list[Fehler]:
    """Prüft den Zeitraum des CSV-Exports."""
    return [Fehler("bis", M_ZEITRAUM)] if bis < von else []


def pruefe_loeschbestaetigung(text: str) -> list[Fehler]:
    """Prüft die Bestätigung für „Alle Daten löschen“ (GR29)."""
    return [] if text == LOESCHWORT else [Fehler("bestaetigung", M_LOESCHEN)]
