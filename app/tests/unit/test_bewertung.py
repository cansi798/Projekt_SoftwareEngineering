"""Tests der Wochenbewertung (GP03, GP05) mit den Rechenbeispielen der Spezifikation."""

from datetime import date, time, timedelta

import pytest

from balanceos.domaene.bewertung import MIN_TAGE, bewerte_woche, zielerfuellung
from balanceos.domaene.kalender import KW, kaufmaennisch_runden
from balanceos.domaene.modell import Aktivitaet, Einstellungen, Lebensbereich
from balanceos.domaene.typen import Aktivitaetsstatus, Bereichstyp

KW47 = KW(2026, 47)
MO = KW47.montag()
D = Aktivitaetsstatus.DURCHGEFUEHRT
BEWEGUNG = Lebensbereich("Bewegung", Bereichstyp.MINDESTZIEL, "#3A7D44", 3, id=1)
ARBEIT = Lebensbereich("Arbeit", Bereichstyp.OBERGRENZE, "#4C6EF5", 40, id=2)
FREIZEIT = Lebensbereich("Freizeit", Bereichstyp.MINDESTZIEL, "#1098AD", 0, id=3)
EIN = Einstellungen(alpha=0.6, gesamtscore_anzeigen=True)


def _akt(bereich, tag, minuten, status=D, zufriedenheit=None, **k) -> Aktivitaet:
    return Aktivitaet(
        "x", bereich.id, MO + timedelta(days=tag), minuten, status, zufriedenheit=zufriedenheit, **k
    )


def _beispiel() -> list[Aktivitaet]:
    """Bewegung 2 × 45 min (Zufriedenheit 4 und 5), Arbeit 46 h an fünf Tagen."""
    return [
        _akt(BEWEGUNG, 0, 45, zufriedenheit=4),
        _akt(BEWEGUNG, 2, 45, zufriedenheit=5),
        *(_akt(ARBEIT, tag, 552) for tag in range(5)),
    ]


@pytest.fixture
def bewertung():
    return bewerte_woche(KW47, [BEWEGUNG, ARBEIT], _beispiel(), EIN)


def test_beispiel1_mindestziel_mit_zufriedenheit(bewertung):
    b = bewertung.bereich(BEWEGUNG.id)
    assert b.score == 65
    assert b.zielerfuellung == pytest.approx(0.5)
    assert b.zufriedenheitsanteil == pytest.approx(0.875)
    assert b.ist_stunden == pytest.approx(1.5)


def test_beispiel2_obergrenze_ohne_zufriedenheit(bewertung):
    b = bewertung.bereich(ARBEIT.id)
    assert b.score == 85
    assert b.zielerfuellung == pytest.approx(0.85)
    assert b.abweichung == pytest.approx(6.0)
    assert b.zufriedenheitsanteil is None


def test_beispiel3_gesamtscore(bewertung):
    assert bewertung.ausreichende_daten and bewertung.vollstaendigkeit_tage == 5
    assert bewertung.gesamtscore == 75


def test_unter_vier_tagen_keine_scores():
    daten = [_akt(BEWEGUNG, t, 60, zufriedenheit=5) for t in range(MIN_TAGE - 1)]
    w = bewerte_woche(KW47, [BEWEGUNG, ARBEIT], daten, EIN)
    assert w.vollstaendigkeit_tage == 3 and not w.ausreichende_daten
    assert all(b.score is None for b in w.bereiche) and w.gesamtscore is None
    assert w.bereich(BEWEGUNG.id).ist_stunden == pytest.approx(3)
    assert w.bereich(BEWEGUNG.id).zielerfuellung == pytest.approx(1)


def test_geplant_und_ausgefallen_zaehlen_nicht(bewertung):
    extra = [
        _akt(BEWEGUNG, 5, 600, Aktivitaetsstatus.GEPLANT),
        _akt(BEWEGUNG, 6, 600, Aktivitaetsstatus.AUSGEFALLEN),
    ]
    w = bewerte_woche(KW47, [BEWEGUNG, ARBEIT], _beispiel() + extra, EIN)
    assert w.bereich(BEWEGUNG.id).ist_stunden == pytest.approx(1.5)
    assert w.vollstaendigkeit_tage == 5


def test_soll_null_nicht_bewertet():
    w = bewerte_woche(
        KW47, [BEWEGUNG, ARBEIT, FREIZEIT], [*_beispiel(), _akt(FREIZEIT, 1, 90)], EIN
    )
    f = w.bereich(FREIZEIT.id)
    assert f.ist_stunden == pytest.approx(1.5)
    assert f.zielerfuellung is None and f.score is None
    assert w.gesamtscore == 75


def test_obergrenze_doppeltes_soll_ist_null():
    assert zielerfuellung(Bereichstyp.OBERGRENZE, 80, 40) == 0
    assert zielerfuellung(Bereichstyp.OBERGRENZE, 100, 40) == 0
    assert zielerfuellung(Bereichstyp.OBERGRENZE, 30, 40) == 1
    assert zielerfuellung(Bereichstyp.MINDESTZIEL, 5, 3) == 1


def test_gesamtscore_aus_wenn_alle_gewichte_null():
    bereiche = [
        Lebensbereich("Bewegung", Bereichstyp.MINDESTZIEL, "#3A7D44", 3, gewicht=0, id=1),
        Lebensbereich("Arbeit", Bereichstyp.OBERGRENZE, "#4C6EF5", 40, gewicht=0, id=2),
    ]
    assert bewerte_woche(KW47, bereiche, _beispiel(), EIN).gesamtscore is None


def test_gesamtscore_gewichtet():
    bereiche = [
        BEWEGUNG,
        Lebensbereich("Arbeit", Bereichstyp.OBERGRENZE, "#4C6EF5", 40, gewicht=3, id=2),
    ]
    # (1 · 65 + 3 · 85) / 4 = 80
    assert bewerte_woche(KW47, bereiche, _beispiel(), EIN).gesamtscore == 80


def test_gesamtscore_nur_wenn_angezeigt():
    w = bewerte_woche(KW47, [BEWEGUNG, ARBEIT], _beispiel(), Einstellungen(0.6, False))
    assert w.gesamtscore is None
    assert w.bereich(BEWEGUNG.id).score == 65


def test_alpha_eins_nur_zielerfuellung():
    w = bewerte_woche(KW47, [BEWEGUNG, ARBEIT], _beispiel(), Einstellungen(1.0, True))
    assert w.bereich(BEWEGUNG.id).score == 50


def test_bewertung_ohne_aktivitaeten():
    w = bewerte_woche(KW47, [BEWEGUNG, ARBEIT], [], EIN)
    assert w.vollstaendigkeit_tage == 0 and not w.ausreichende_daten
    assert w.bereich(ARBEIT.id).ist_stunden == 0
    assert w.bereich(ARBEIT.id).abweichung == pytest.approx(-40)


def test_bewertung_ohne_bereiche():
    w = bewerte_woche(KW47, [], _beispiel(), EIN)
    assert w.bereiche == [] and w.gesamtscore is None


def test_bewertung_ueber_mitternacht_nur_in_beginnwoche():
    sonntag = KW(2026, 46).sonntag()
    schlaf = Aktivitaet("Schlaf", BEWEGUNG.id, sonntag, 450, D, beginn=time(23), ende=time(6, 30))
    w46 = bewerte_woche(KW(2026, 46), [BEWEGUNG], [schlaf], EIN)
    w47 = bewerte_woche(KW47, [BEWEGUNG], [schlaf], EIN)
    assert w46.bereich(BEWEGUNG.id).ist_stunden == pytest.approx(7.5)
    assert w47.bereich(BEWEGUNG.id).ist_stunden == 0
    assert w47.vollstaendigkeit_tage == 0


def test_inaktiver_bereich_nicht_bewertet():
    inaktiv = Lebensbereich("Arbeit", Bereichstyp.OBERGRENZE, "#4C6EF5", 40, aktiv=False, id=2)
    w = bewerte_woche(KW47, [BEWEGUNG, inaktiv], _beispiel(), EIN)
    assert w.bereich(inaktiv.id) is None
    assert w.vollstaendigkeit_tage == 2  # nur noch die Bewegungstage zählen
    assert w.gesamtscore is None


def test_kw53_jahreswechsel():
    kw53 = KW(2026, 53)
    daten = [
        Aktivitaet("x", BEWEGUNG.id, kw53.montag() + timedelta(days=t), 60, D) for t in range(7)
    ]
    w = bewerte_woche(kw53, [BEWEGUNG], daten, EIN)
    assert w.vollstaendigkeit_tage == 7
    assert w.bereich(BEWEGUNG.id).ist_stunden == pytest.approx(7)
    assert kw53.sonntag() == date(2027, 1, 3)


def test_kaufmaennisch_runden_bei_rechenrauschen():
    assert kaufmaennisch_runden(72.49999999999999) == 73
    assert kaufmaennisch_runden(72.4) == 72
