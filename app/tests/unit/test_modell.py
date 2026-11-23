"""Tests für Geschäftsobjekte und Aufzählungen."""

from datetime import date

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import (
    Begruendung,
    Lebensbereich,
    Who5Erhebung,
)
from balanceos.domaene.typen import Bereichstyp, StandardSchluessel, Wochentag


def test_who5_rohwert_prozentwert():
    erhebung = Who5Erhebung(date(2026, 11, 15), (3, 4, 3, 2, 4))
    assert erhebung.rohwert == 16
    assert erhebung.prozentwert == 64


def test_begruendung_reihenfolge():
    b = Begruendung("R01", "M", "D", "Z", "S", "W", "Q", "E", "G")
    assert [z[0] for z in b.zeilen()] == [
        "Regel",
        "Modell",
        "Datenbasis",
        "Zeitraum",
        "Schwelle",
        "Ihr Wert",
        "Quelle",
        "Evidenzart",
        "Grenzen",
    ]
    assert b.zeilen()[5] == ("Ihr Wert", "W")


def test_wochentag_aus_datum():
    assert Wochentag.aus_datum(date(2026, 11, 9)) is Wochentag.MO
    assert Wochentag.aus_datum(date(2026, 11, 15)) is Wochentag.SO
    assert Wochentag.SO.index == 6


def test_lebensbereich_ist_standard():
    eigen = Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#000000", 2.0)
    standard = Lebensbereich(
        "Bewegung",
        Bereichstyp.MINDESTZIEL,
        "#3A7D44",
        3.0,
        standard_schluessel=StandardSchluessel.BEWEGUNG,
    )
    assert not eigen.ist_standard
    assert standard.ist_standard


def test_aufzaehlungswerte_wie_literale():
    assert str(Bereichstyp.OBERGRENZE) == "OBERGRENZE"
    assert KW(2026, 1).iso() == "2026-W01"
