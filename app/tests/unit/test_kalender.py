"""Tests für ISO-Kalenderwoche, Dauerberechnung und Rundung."""

from datetime import date, time

import pytest

from balanceos.domaene.kalender import (
    KW,
    berechne_dauer,
    kaufmaennisch_runden,
    stunden_text,
    zahl_text,
)


def test_kw_montag_und_label():
    kw = KW(2026, 46)
    assert kw.montag() == date(2026, 11, 9)
    assert kw.sonntag() == date(2026, 11, 15)
    assert kw.label() == "KW 46/2026"
    assert kw.iso() == "2026-W46"
    assert kw.zeitraum_text() == "KW 46/2026 (09.11.–15.11.2026)"


def test_kw_tage_montag_bis_sonntag():
    tage = KW(2026, 46).tage()
    assert len(tage) == 7
    assert tage[0] == date(2026, 11, 9)
    assert tage[-1] == date(2026, 11, 15)


def test_kw53_und_jahreswechsel():
    assert KW.aus_datum(date(2027, 1, 1)) == KW(2026, 53)
    assert KW(2026, 53).verschoben(1) == KW(2027, 1)
    assert KW(2027, 1).verschoben(-2) == KW(2026, 52)


def test_kw_heute():
    assert KW.heute(date(2026, 11, 23)) == KW(2026, 48)


def test_kw_ordnung():
    assert KW(2026, 52) < KW(2026, 53) < KW(2027, 1)


def test_dauer_aus_beginn_und_ende():
    assert berechne_dauer(time(18, 0), time(18, 45), None) == 45


def test_dauer_direkt():
    assert berechne_dauer(None, None, 90) == 90


def test_dauer_ueber_mitternacht():
    assert berechne_dauer(time(23, 0), time(6, 30), None) == 450


def test_dauer_ueber_mitternacht_sonntag_zaehlt_zur_kw_des_beginns():
    # Die Aktivität trägt das Datum des Beginns (Sonntag) und zählt zu dessen Woche.
    assert KW.aus_datum(date(2026, 11, 15)) == KW(2026, 46)


@pytest.mark.parametrize(
    ("beginn", "ende", "dauer"),
    [
        (time(8, 0), time(8, 0), None),
        (None, time(8, 0), None),
        (None, None, 0),
        (None, None, 1441),
        (None, None, None),
    ],
)
def test_dauer_ungueltig(beginn, ende, dauer):
    with pytest.raises(ValueError):
        berechne_dauer(beginn, ende, dauer)


@pytest.mark.parametrize(
    ("wert", "erwartet"),
    [(72.5, 73), (0.5, 1), (65.00000000000001, 65), (64.49, 64), (100.0, 100), (0.0, 0)],
)
def test_kaufmaennisch_runden(wert, erwartet):
    assert kaufmaennisch_runden(wert) == erwartet


def test_textformate_mit_komma():
    assert stunden_text(6.5) == "6,5 h"
    assert stunden_text(12) == "12,0 h"
    assert zahl_text(4.25) == "4,3"
    assert zahl_text(3.0) == "3,0"
