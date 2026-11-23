"""Tests des ReflexionService (US20–US22; GR26, GR27)."""

from datetime import date

import pytest

from balanceos.anwendung.fehler import ValidierungsFehler
from balanceos.domaene.kalender import KW


def test_who5_speichern_und_verlauf(kontext):
    ergebnis = kontext.reflexion.who5_speichern(date(2026, 11, 15), [3, 4, 3, 2, 4])
    assert (ergebnis.rohwert, ergebnis.prozentwert, ergebnis.empfehlung) == (16, 64, False)
    kontext.reflexion.who5_speichern(date(2026, 11, 1), [1, 1, 1, 1, 1])
    assert [e.datum for e in kontext.reflexion.who5_verlauf()] == [
        date(2026, 11, 1),
        date(2026, 11, 15),
    ]


def test_who5_unvollstaendig_abgewiesen(kontext):
    with pytest.raises(ValidierungsFehler) as info:
        kontext.reflexion.who5_speichern(date(2026, 11, 15), [3, None, 3, None, 4])
    assert info.value.fehler[0].meldung == "Noch offen: 2 Aussagen."
    assert kontext.reflexion.who5_verlauf() == []


def test_who5_datum_in_zukunft_abgewiesen(kontext):
    with pytest.raises(ValidierungsFehler):
        kontext.reflexion.who5_speichern(date(2026, 11, 19), [3, 3, 3, 3, 3])


def test_reflexion_upsert_eine_je_woche(kontext):
    kw = KW(2026, 47)
    kontext.reflexion.reflexion_speichern(kw, ("Sport", "", ""), 3)
    kontext.reflexion.reflexion_speichern(kw, ("Sport", "Freunde", "Früher schlafen"), 4)
    r = kontext.reflexion.reflexion(kw)
    assert r.antworten == ("Sport", "Freunde", "Früher schlafen") and r.stimmung == 4
    assert len(kontext.repos.reflexionen.alle()) == 1
    assert kontext.reflexion.reflexion(KW(2026, 46)) is None


def test_reflexion_zu_lang_abgewiesen(kontext):
    with pytest.raises(ValidierungsFehler):
        kontext.reflexion.reflexion_speichern(KW(2026, 47), ("x" * 1001, "", ""), None)
