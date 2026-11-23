"""Integrationstests des Auswertungs-Services (US10–US14, US19)."""

from datetime import timedelta

import pytest

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet, Einstellungen
from balanceos.domaene.typen import Aktivitaetsstatus, Bewegungsart
from balanceos.domaene.typen import StandardSchluessel as S

KW46 = KW(2026, 46)
D = Aktivitaetsstatus.DURCHGEFUEHRT


def anlegen(kontext, schluessel, kw, tag, minuten, **k):
    bid = kontext.repos.bereiche.nach_schluessel(schluessel).id
    datum = kw.montag() + timedelta(days=tag)
    return kontext.repos.aktivitaeten.speichern(Aktivitaet("x", bid, datum, minuten, D, **k))


def beispielwoche(kontext, kw=KW46):
    """Rechenbeispiel 1 (Bewegung 2 × 45 min, Zufriedenheit 4 und 5) plus vier Fülltage."""
    for tag in range(4):
        anlegen(kontext, S.VERPFLICHTUNGEN, kw, tag, 60)
    anlegen(kontext, S.BEWEGUNG, kw, 0, 45, zufriedenheit=4, bewegungsart=Bewegungsart.KRAFT)
    anlegen(kontext, S.BEWEGUNG, kw, 2, 45, zufriedenheit=5)


def test_wochenbewertung_rechenbeispiel(kontext):
    beispielwoche(kontext)
    bid = kontext.repos.bereiche.nach_schluessel(S.BEWEGUNG).id
    w = kontext.auswertung.wochenbewertung(KW46)
    assert w.ausreichende_daten and w.bereich(bid).score == 65
    assert w.gesamtscore is None
    kontext.stammdaten.einstellungen_speichern(Einstellungen(0.6, True))
    assert kontext.auswertung.wochenbewertung(KW46).gesamtscore is not None


def test_hinweise_ohne_ausgeblendete(kontext):
    beispielwoche(kontext)
    r01 = next(h for h in kontext.auswertung.hinweise(KW46) if h.regel == "R01")
    kontext.auswertung.hinweis_ausblenden(r01)
    assert all(h.regel != "R01" for h in kontext.auswertung.hinweise(KW46))
    assert any(h.regel == "R01" for h in kontext.auswertung.hinweise(KW46, True))
    assert kontext.repos.ausblendungen.ausgeblendet(KW46.verschoben(1)) == set()


def test_bereichshinweis_nur_fuer_diesen_bereich_ausgeblendet(kontext):
    beispielwoche(kontext)
    anlegen(kontext, S.FAMILIE, KW46, 5, 720)
    anlegen(kontext, S.HOBBYS, KW46, 5, 300)
    r08 = [h for h in kontext.auswertung.hinweise(KW46) if h.regel == "R08"]
    assert len(r08) == 2
    kontext.auswertung.hinweis_ausblenden(r08[0])
    rest = [h for h in kontext.auswertung.hinweise(KW46) if h.regel == "R08"]
    assert [h.lebensbereich_id for h in rest] == [r08[1].lebensbereich_id]


def test_verlauf_acht_wochen_aelteste_zuerst(kontext):
    beispielwoche(kontext, KW46)
    verlauf = kontext.auswertung.verlauf(KW(2026, 47))
    assert [w.kw for w in verlauf] == [KW(2026, 47).verschoben(-i) for i in range(7, -1, -1)]
    assert verlauf[-2].ausreichende_daten and not verlauf[-1].ausreichende_daten


def test_regel_aus_erzeugt_keinen_hinweis(kontext):
    beispielwoche(kontext)
    kontext.auswertung.regel_setzen("R01", False)
    assert all(h.regel != "R01" for h in kontext.auswertung.hinweise(KW46))
    assert not next(r for r in kontext.auswertung.regeln() if r.kennung == "R01").aktiv


def test_leere_datenbank(kontext):
    assert not kontext.auswertung.gibt_aktivitaeten()
    w = kontext.auswertung.wochenbewertung(KW46)
    assert w.vollstaendigkeit_tage == 0
    assert [h.regel for h in kontext.auswertung.hinweise(KW46)] == ["R10"]
    beispielwoche(kontext)
    assert kontext.auswertung.gibt_aktivitaeten()


def test_kompassmodelle(kontext):
    modelle = kontext.auswertung.kompassmodelle()
    assert [m.schluessel for m in modelle][0] == "LBM" and len(modelle) == 6
    assert kontext.auswertung.modell("WHO_BEWEGUNG").name == "WHO-Bewegungsleitlinie"
    with pytest.raises(KeyError):
        kontext.auswertung.modell("GIBT_ES_NICHT")
