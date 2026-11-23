"""Auflösung wöchentlicher Wiederholungsserien in einzelne Termine (GP02, GR16–GR18)."""

from datetime import date, datetime, timedelta

from balanceos.domaene.modell import Aktivitaet, Wiederholungsserie
from balanceos.domaene.typen import Aktivitaetsstatus, Wochentag

HORIZONT_WOCHEN = 52
"""Termine entstehen höchstens so viele Wochen im Voraus (GR17)."""


def horizont(heute: date) -> date:
    """Letztes Datum, bis zu dem Termine im Voraus erzeugt werden."""
    return heute + timedelta(weeks=HORIZONT_WOCHEN)


def termindaten(serie: Wiederholungsserie, ab: date, bis: date) -> list[date]:
    """Termindaten der Serie im Zeitraum ``ab`` bis ``bis`` ohne Ausnahmen, aufsteigend."""
    start = max(ab, serie.startdatum)
    ende = min(bis, serie.enddatum) if serie.enddatum else bis
    tage: list[date] = []
    tag = start
    while tag <= ende:
        if Wochentag.aus_datum(tag) in serie.wochentage and tag not in serie.ausnahmen:
            tage.append(tag)
        tag += timedelta(days=1)
    return tage


def ist_termindatum(serie: Wiederholungsserie, tag: date) -> bool:
    """``True``, wenn an ``tag`` laut Serie ein Termin liegt (Voraussetzung für GR18)."""
    if tag < serie.startdatum or (serie.enddatum is not None and tag > serie.enddatum):
        return False
    return Wochentag.aus_datum(tag) in serie.wochentage


def erzeuge_termin(serie: Wiederholungsserie, tag: date) -> Aktivitaet:
    """Erzeugt den geplanten Termin der Serie an einem Tag."""
    ende = None
    if serie.beginn is not None:
        ende = (datetime.combine(tag, serie.beginn) + timedelta(minutes=serie.dauer_minuten)).time()
    return Aktivitaet(
        titel=serie.titel,
        lebensbereich_id=serie.lebensbereich_id,
        datum=tag,
        dauer_minuten=serie.dauer_minuten,
        status=Aktivitaetsstatus.GEPLANT,
        beginn=serie.beginn,
        ende=ende,
        serie_id=serie.id,
    )
