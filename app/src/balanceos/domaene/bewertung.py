"""Wochenbewertung und Gesamt-Score (GP03, GP05; Spezifikation Kap. 2.2).

Die Bewertung wird bei jeder Anzeige neu aus den Aktivitäten berechnet und
nicht gespeichert. Die Formeln sind programmeigen und nicht validiert.
"""

from collections import defaultdict
from statistics import fmean

from balanceos.domaene.kalender import KW, kaufmaennisch_runden
from balanceos.domaene.modell import (
    Aktivitaet,
    Bereichsbewertung,
    Einstellungen,
    Lebensbereich,
    Wochenbewertung,
)
from balanceos.domaene.typen import Aktivitaetsstatus, Bereichstyp

MIN_TAGE = 4
"""Mindestzahl erfasster Tage, ab der Scores berechnet werden (GR21)."""


def zielerfuellung(typ: Bereichstyp, ist: float, soll: float) -> float:
    """Zielerfüllung z eines Bereichs zwischen 0 und 1 (Schritt 3).

    Args:
        typ: Mindestziel oder Obergrenze.
        ist: Durchgeführte Stunden der Woche.
        soll: Soll-Stunden pro Woche, größer als 0.
    """
    if typ is Bereichstyp.MINDESTZIEL:
        return min(ist / soll, 1.0)
    if ist <= soll:
        return 1.0
    return max(0.0, 1 - (ist - soll) / soll)


def _bereich_bewerten(
    b: Lebensbereich, aktivitaeten: list[Aktivitaet], alpha: float, mit_score: bool
) -> Bereichsbewertung:
    ist = sum(a.dauer_minuten for a in aktivitaeten) / 60
    werte = [a.zufriedenheit for a in aktivitaeten if a.zufriedenheit is not None]
    anteil = (fmean(werte) - 1) / 4 if werte else None
    z = zielerfuellung(b.typ, ist, b.soll_stunden) if b.soll_stunden > 0 else None
    score = None
    if z is not None and mit_score:
        roh = z if anteil is None else alpha * z + (1 - alpha) * anteil
        score = kaufmaennisch_runden(100 * roh)
    return Bereichsbewertung(
        lebensbereich_id=b.id,
        ist_stunden=ist,
        soll_stunden=b.soll_stunden,
        zielerfuellung=z,
        zufriedenheitsanteil=anteil,
        score=score,
        abweichung=ist - b.soll_stunden,
    )


def bewerte_woche(
    kw: KW,
    bereiche: list[Lebensbereich],
    aktivitaeten: list[Aktivitaet],
    einstellungen: Einstellungen,
) -> Wochenbewertung:
    """Berechnet die Bewertung einer Kalenderwoche.

    Es zählen nur durchgeführte Aktivitäten in aktiven Bereichen, deren Datum
    in ``kw`` liegt; eine Aktivität über Mitternacht zählt zur Woche ihres
    Beginns (GR14). Bei weniger als ``MIN_TAGE`` erfassten Tagen bleiben Ist,
    Soll, Zielerfüllung und Abweichung gefüllt, alle Scores aber ``None``.

    Args:
        kw: Zu bewertende Kalenderwoche.
        bereiche: Alle Lebensbereiche; inaktive werden übergangen.
        aktivitaeten: Aktivitäten, die auch außerhalb der Woche liegen dürfen.
        einstellungen: Gewichtung ``alpha`` und Anzeige des Gesamt-Scores.
    """
    aktive = [b for b in bereiche if b.aktiv]
    aktive_ids = {b.id for b in aktive}
    montag, sonntag = kw.montag(), kw.sonntag()
    zaehlend = [
        a
        for a in aktivitaeten
        if a.status is Aktivitaetsstatus.DURCHGEFUEHRT
        and a.lebensbereich_id in aktive_ids
        and montag <= a.datum <= sonntag
    ]
    tage = len({a.datum for a in zaehlend})
    ausreichend = tage >= MIN_TAGE
    nach_bereich: dict[int, list[Aktivitaet]] = defaultdict(list)
    for a in zaehlend:
        nach_bereich[a.lebensbereich_id].append(a)
    bewertungen = [
        _bereich_bewerten(b, nach_bereich[b.id], einstellungen.alpha, ausreichend) for b in aktive
    ]
    gesamt = None
    if ausreichend and einstellungen.gesamtscore_anzeigen:
        gewichtet = [
            (b.gewicht, bw.score)
            for b, bw in zip(aktive, bewertungen, strict=True)
            if bw.score is not None and b.gewicht > 0
        ]
        summe = sum(g for g, _ in gewichtet)
        if summe > 0:
            gesamt = kaufmaennisch_runden(sum(g * s for g, s in gewichtet) / summe)
    return Wochenbewertung(
        kw=kw,
        vollstaendigkeit_tage=tage,
        ausreichende_daten=ausreichend,
        bereiche=bewertungen,
        gesamtscore=gesamt,
    )
