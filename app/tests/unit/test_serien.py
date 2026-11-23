"""Tests der Auflösung wöchentlicher Wiederholungsserien (GP02)."""

from datetime import date, time, timedelta

from balanceos.domaene.modell import Wiederholungsserie
from balanceos.domaene.serien import erzeuge_termin, horizont, ist_termindatum, termindaten
from balanceos.domaene.typen import Aktivitaetsstatus, Wochentag


def _serie(**k) -> Wiederholungsserie:
    basis = dict(
        titel="Joggen",
        lebensbereich_id=3,
        wochentage=frozenset({Wochentag.DI, Wochentag.DO}),
        startdatum=date(2026, 11, 3),
        dauer_minuten=45,
        beginn=time(18, 0),
        id=1,
    )
    basis.update(k)
    return Wiederholungsserie(**basis)


def test_termine_nur_an_gewaehlten_wochentagen():
    tage = termindaten(_serie(), date(2026, 11, 1), date(2026, 11, 19))
    assert tage == [date(2026, 11, d) for d in (3, 5, 10, 12, 17, 19)]


def test_ausnahme_wird_uebersprungen():
    tage = termindaten(
        _serie(ausnahmen={date(2026, 11, 19)}), date(2026, 11, 1), date(2026, 11, 19)
    )
    assert date(2026, 11, 19) not in tage
    assert len(tage) == 5


def test_enddatum_begrenzt():
    tage = termindaten(_serie(enddatum=date(2026, 11, 10)), date(2026, 11, 1), date(2026, 12, 31))
    assert tage == [date(2026, 11, 3), date(2026, 11, 5), date(2026, 11, 10)]


def test_unbefristet_bis_horizont():
    heute = date(2026, 11, 18)
    tage = termindaten(_serie(), heute, horizont(heute))
    assert max(tage) <= heute + timedelta(weeks=52)
    assert horizont(heute) == heute + timedelta(weeks=52)
    assert len(tage) == 104


def test_ist_termindatum():
    s = _serie(enddatum=date(2026, 11, 30))
    assert ist_termindatum(s, date(2026, 11, 10))
    assert not ist_termindatum(s, date(2026, 11, 11))  # Mittwoch
    assert not ist_termindatum(s, date(2026, 10, 27))  # vor dem Start
    assert not ist_termindatum(s, date(2026, 12, 1))  # nach dem Ende


def test_erzeuge_termin():
    a = erzeuge_termin(_serie(), date(2026, 11, 10))
    assert (a.titel, a.lebensbereich_id, a.datum, a.dauer_minuten) == (
        "Joggen",
        3,
        date(2026, 11, 10),
        45,
    )
    assert a.status is Aktivitaetsstatus.GEPLANT
    assert (a.beginn, a.ende, a.serie_id) == (time(18, 0), time(18, 45), 1)


def test_erzeuge_termin_ueber_mitternacht_und_ohne_beginn():
    nacht = erzeuge_termin(_serie(beginn=time(23, 0), dauer_minuten=450), date(2026, 11, 10))
    assert nacht.ende == time(6, 30)
    ohne = erzeuge_termin(_serie(beginn=None), date(2026, 11, 10))
    assert ohne.beginn is None and ohne.ende is None
