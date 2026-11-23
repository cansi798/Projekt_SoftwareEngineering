"""Tests der Gültigkeitsregeln (Spezifikation, Tabelle „Gültigkeitsregeln für Eingabefelder“)."""

from dataclasses import replace
from datetime import date, time

import pytest

from balanceos.domaene import validierung as v
from balanceos.domaene.modell import Aktivitaet, Lebensbereich, Wiederholungsserie
from balanceos.domaene.typen import (
    Aktivitaetsstatus,
    Bereichstyp,
    Bewegungsart,
    StandardSchluessel,
    Wochentag,
)

HEUTE = date(2026, 11, 18)
BEWEGUNG = Lebensbereich(
    "Bewegung",
    Bereichstyp.MINDESTZIEL,
    "#3A7D44",
    3,
    standard_schluessel=StandardSchluessel.BEWEGUNG,
    id=3,
)
ARBEIT = Lebensbereich(
    "Arbeit",
    Bereichstyp.OBERGRENZE,
    "#4C6EF5",
    40,
    standard_schluessel=StandardSchluessel.ARBEIT,
    id=1,
)


def _akt(**k) -> Aktivitaet:
    basis = dict(
        titel="Joggen",
        lebensbereich_id=3,
        datum=date(2026, 11, 17),
        dauer_minuten=45,
        status=Aktivitaetsstatus.DURCHGEFUEHRT,
    )
    basis.update(k)
    return Aktivitaet(**basis)


def _meldungen(fehler) -> dict[str, str]:
    return {f.feld: f.meldung for f in fehler}


# --- Aktivität ------------------------------------------------------------------------------


def test_gueltige_aktivitaet_ohne_fehler():
    a = _akt(zufriedenheit=4, bewegungsart=Bewegungsart.AUSDAUER_MODERAT, notiz="x" * 500)
    assert v.pruefe_aktivitaet(a, BEWEGUNG, HEUTE) == []


@pytest.mark.parametrize("titel", ["", "   ", "x" * 81])
def test_titel_ungueltig(titel):
    assert _meldungen(v.pruefe_aktivitaet(_akt(titel=titel), BEWEGUNG, HEUTE)) == {
        "titel": v.M_TITEL
    }


def test_titel_80_zeichen_mit_randleerzeichen_gueltig():
    assert v.pruefe_aktivitaet(_akt(titel=" " + "x" * 80 + " "), BEWEGUNG, HEUTE) == []


def test_fehlender_oder_inaktiver_bereich():
    assert _meldungen(v.pruefe_aktivitaet(_akt(), None, HEUTE))["lebensbereich"] == v.M_BEREICH
    inaktiv = replace(BEWEGUNG, aktiv=False)
    assert _meldungen(v.pruefe_aktivitaet(_akt(), inaktiv, HEUTE))["lebensbereich"] == v.M_BEREICH


def test_inaktiver_bereich_beim_bearbeiten_erlaubt():
    """GR05 betrifft nur neue Aktivitäten; bestehende bleiben bearbeitbar."""
    inaktiv = replace(BEWEGUNG, aktiv=False)
    assert v.pruefe_aktivitaet(_akt(id=7), inaktiv, HEUTE) == []


@pytest.mark.parametrize(("beginn", "ende"), [(time(8, 0), time(8, 0)), (None, time(8, 0))])
def test_zeitangaben_ungueltig(beginn, ende):
    assert _meldungen(v.pruefe_aktivitaet(_akt(beginn=beginn, ende=ende), BEWEGUNG, HEUTE)) == {
        "zeit": v.M_ZEIT
    }


@pytest.mark.parametrize("dauer", [0, 1441])
def test_dauer_ungueltig(dauer):
    assert _meldungen(v.pruefe_aktivitaet(_akt(dauer_minuten=dauer), BEWEGUNG, HEUTE)) == {
        "dauer": v.M_DAUER
    }


def test_durchgefuehrt_in_zukunft():
    a = _akt(datum=date(2026, 11, 19))
    assert _meldungen(v.pruefe_aktivitaet(a, BEWEGUNG, HEUTE)) == {"status": v.M_ZUKUNFT}


def test_geplant_in_zukunft_gueltig():
    a = _akt(datum=date(2026, 11, 19), status=Aktivitaetsstatus.GEPLANT)
    assert v.pruefe_aktivitaet(a, BEWEGUNG, HEUTE) == []


def test_bewertung_nur_bei_durchgefuehrt():
    a = _akt(status=Aktivitaetsstatus.GEPLANT, zufriedenheit=3)
    assert "bewertung" in _meldungen(v.pruefe_aktivitaet(a, BEWEGUNG, HEUTE))


@pytest.mark.parametrize("wert", [0, 6])
def test_bewertung_ausserhalb_skala(wert):
    assert "bewertung" in _meldungen(v.pruefe_aktivitaet(_akt(belastung=wert), BEWEGUNG, HEUTE))


def test_bewegungsart_nur_im_bereich_bewegung():
    a = _akt(lebensbereich_id=1, bewegungsart=Bewegungsart.KRAFT)
    assert "bewegungsart" in _meldungen(v.pruefe_aktivitaet(a, ARBEIT, HEUTE))


def test_notiz_zu_lang():
    assert _meldungen(v.pruefe_aktivitaet(_akt(notiz="x" * 501), BEWEGUNG, HEUTE)) == {
        "notiz": v.M_NOTIZ
    }


# --- Serie ----------------------------------------------------------------------------------


def _serie(**k) -> Wiederholungsserie:
    basis = dict(
        titel="Joggen",
        lebensbereich_id=3,
        wochentage=frozenset({Wochentag.DI}),
        startdatum=date(2026, 11, 17),
        dauer_minuten=45,
    )
    basis.update(k)
    return Wiederholungsserie(**basis)


def test_serie_gueltig():
    assert v.pruefe_serie(_serie(enddatum=date(2026, 11, 17))) == []


def test_serie_ohne_wochentag():
    assert _meldungen(v.pruefe_serie(_serie(wochentage=frozenset()))) == {
        "wochentage": v.M_WOCHENTAGE
    }


def test_serie_enddatum_vor_datum():
    assert _meldungen(v.pruefe_serie(_serie(enddatum=date(2026, 11, 16)))) == {
        "enddatum": v.M_ENDDATUM
    }


# --- Lebensbereich --------------------------------------------------------------------------


def _bestand() -> list[Lebensbereich]:
    return [ARBEIT, BEWEGUNG]


def test_lebensbereich_gueltig():
    neu = Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", 2.5)
    assert v.pruefe_lebensbereich(neu, _bestand()) == []


@pytest.mark.parametrize("name", ["", "  ", "x" * 41])
def test_name_ungueltig(name):
    neu = Lebensbereich(name, Bereichstyp.MINDESTZIEL, "#C2255C", 2)
    assert _meldungen(v.pruefe_lebensbereich(neu, _bestand())) == {"name": v.M_NAME}


def test_name_doppelt_ohne_gross_klein():
    neu = Lebensbereich(" bewegung ", Bereichstyp.MINDESTZIEL, "#C2255C", 2)
    assert _meldungen(v.pruefe_lebensbereich(neu, _bestand())) == {"name": v.M_NAME_DOPPELT}


def test_eigener_name_beim_bearbeiten_erlaubt():
    assert v.pruefe_lebensbereich(replace(BEWEGUNG, soll_stunden=4), _bestand()) == []


@pytest.mark.parametrize("soll", [-0.5, 2.3, 168.5])
def test_soll_ungueltig(soll):
    neu = Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", soll)
    assert v.M_SOLL in _meldungen(v.pruefe_lebensbereich(neu, _bestand())).values()


def test_summe_ueber_168():
    neu = Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", 125.5)
    assert _meldungen(v.pruefe_lebensbereich(neu, _bestand())) == {"summe": v.M_SUMME}


def test_summe_zaehlt_nur_aktive():
    neu = Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", 125.5, aktiv=False)
    assert v.pruefe_lebensbereich(neu, _bestand()) == []


def test_letzter_aktiver_bereich_mit_soll():
    einzig = [BEWEGUNG]
    assert _meldungen(v.pruefe_lebensbereich(replace(BEWEGUNG, aktiv=False), einzig)) == {
        "aktiv": v.M_AKTIV
    }
    assert _meldungen(v.pruefe_lebensbereich(replace(BEWEGUNG, soll_stunden=0), einzig)) == {
        "aktiv": v.M_AKTIV
    }


@pytest.mark.parametrize("gewicht", [-1, 11])
def test_gewicht_ungueltig(gewicht):
    neu = Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", 2, gewicht=gewicht)
    assert _meldungen(v.pruefe_lebensbereich(neu, _bestand())) == {"gewicht": v.M_GEWICHT}


# --- Einstellungen, WHO-5, Reflexion, Export, Löschen ---------------------------------------


@pytest.mark.parametrize(
    ("alpha", "gueltig"), [(0.0, True), (1.0, True), (0.6, True), (1.1, False), (-0.1, False)]
)
def test_alpha(alpha, gueltig):
    assert (v.pruefe_alpha(alpha) == []) is gueltig


def test_who5():
    assert v.pruefe_who5(HEUTE, [1, 2, 3, 4, 5], HEUTE) == []
    assert _meldungen(v.pruefe_who5(HEUTE, [1, None, 3, None, 5], HEUTE)) == {
        "antworten": "Noch offen: 2 Aussagen."
    }
    assert _meldungen(v.pruefe_who5(date(2026, 11, 19), [1, 2, 3, 4, 5], HEUTE)) == {
        "datum": v.M_DATUM_ZUKUNFT
    }
    assert "antworten" in _meldungen(v.pruefe_who5(HEUTE, [1, 2, 3, 4, 6], HEUTE))


def test_reflexion():
    assert v.pruefe_reflexion(["x" * 1000, "", ""], None) == []
    assert _meldungen(v.pruefe_reflexion(["", "x" * 1001, ""], 3)) == {"antwort2": v.M_LEITFRAGE}
    assert "stimmung" in _meldungen(v.pruefe_reflexion(["", "", ""], 6))


def test_zeitraum():
    assert v.pruefe_zeitraum(date(2026, 11, 9), date(2026, 11, 9)) == []
    assert _meldungen(v.pruefe_zeitraum(date(2026, 11, 9), date(2026, 11, 8))) == {
        "bis": v.M_ZEITRAUM
    }


@pytest.mark.parametrize(
    ("text", "gueltig"), [("LÖSCHEN", True), ("löschen", False), ("LÖSCHEN ", False), ("", False)]
)
def test_loeschbestaetigung(text, gueltig):
    assert (v.pruefe_loeschbestaetigung(text) == []) is gueltig


def test_meldungen_wortgleich_mit_spezifikation():
    assert v.M_TITEL == "Bitte 1 bis 80 Zeichen eingeben."
    assert v.M_ZUKUNFT == "Zukünftige Aktivitäten sind noch nicht durchgeführt."
    assert v.M_ENDDATUM == "Enddatum darf nicht vor dem Datum liegen."
    assert v.M_SUMME == "Summe übersteigt 168 h pro Woche."
    assert v.M_LOESCHEN == "Bitte LÖSCHEN eingeben."
