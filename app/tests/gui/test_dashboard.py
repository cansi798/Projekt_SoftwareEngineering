"""Oberflächentests von Dashboard und Begründungsdialog (US10–US13, US19)."""

from datetime import timedelta

import pytest

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet, Einstellungen
from balanceos.domaene.typen import Aktivitaetsstatus
from balanceos.domaene.typen import StandardSchluessel as S

pytestmark = pytest.mark.gui
KW46 = KW(2026, 46)
D = Aktivitaetsstatus.DURCHGEFUEHRT


def anlegen(kontext, schluessel, tag, minuten, **k):
    bid = kontext.repos.bereiche.nach_schluessel(schluessel).id
    datum = KW46.montag() + timedelta(days=tag)
    kontext.repos.aktivitaeten.speichern(Aktivitaet("x", bid, datum, minuten, D, **k))
    return bid


def beispielwoche(kontext) -> int:
    for tag in range(4):
        anlegen(kontext, S.VERPFLICHTUNGEN, tag, 60)
    anlegen(kontext, S.BEWEGUNG, 0, 45, zufriedenheit=4)
    return anlegen(kontext, S.BEWEGUNG, 2, 45, zufriedenheit=5)


def viele_hinweise(kontext) -> None:
    beispielwoche(kontext)
    for tag in range(4):
        anlegen(kontext, S.SCHLAF, tag, 300)
        anlegen(kontext, S.ARBEIT, tag, 300, belastung=5, erholung=1)
    anlegen(kontext, S.ARBEIT, 5, 400)
    anlegen(kontext, S.FAMILIE, 5, 720)
    anlegen(kontext, S.HOBBYS, 6, 300)


@pytest.fixture
def zustand():
    from balanceos.praesentation.zustand import Zustand

    return Zustand(KW46)


def _dashboard(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.dashboard import DashboardSeite

    seite = DashboardSeite(kontext, zustand)
    qtbot.addWidget(seite)
    seite.show()
    return seite


def test_dashboard_leerer_zustand_bei_leerer_db(qtbot, kontext, zustand):
    seite = _dashboard(qtbot, kontext, zustand)
    assert seite.stapel.currentWidget() is seite.leer_ansicht
    assert seite.erste_aktivitaet_knopf.text() == "Erste Aktivität erfassen"
    assert seite.demodaten_knopf.text() == "Demodaten laden"


def test_dashboard_zeigt_score_65_fuer_bewegung(qtbot, kontext, zustand):
    bid = beispielwoche(kontext)
    seite = _dashboard(qtbot, kontext, zustand)
    assert seite.stapel.currentWidget() is seite.inhalt
    assert seite.score_labels[bid].text() == "65"
    assert seite.vollstaendigkeit_label.text() == "4/7"
    assert seite.gesamt_karte.isHidden()


def test_gesamtscore_karte_nur_wenn_eingeschaltet(qtbot, kontext, zustand):
    beispielwoche(kontext)
    kontext.stammdaten.einstellungen_speichern(Einstellungen(0.6, True))
    seite = _dashboard(qtbot, kontext, zustand)
    assert not seite.gesamt_karte.isHidden()
    assert seite.gesamt_label.text().isdigit()


def test_unzureichende_daten_zeigen_striche(qtbot, kontext, zustand):
    bid = anlegen(kontext, S.BEWEGUNG, 0, 60)
    seite = _dashboard(qtbot, kontext, zustand)
    assert seite.score_labels[bid].text() == "–"
    assert seite.vollstaendigkeit_label.text() == "1/7"


def test_hoechstens_fuenf_hinweise_sichtbar(qtbot, kontext, zustand):
    viele_hinweise(kontext)
    anzahl = len(kontext.auswertung.hinweise(KW46))
    assert anzahl > 5
    seite = _dashboard(qtbot, kontext, zustand)
    assert len(seite.hinweis_zeilen) == 5
    assert seite.alle_hinweise_knopf.text() == f"Alle Hinweise ({anzahl})"


def test_ausblenden_entfernt_hinweis(qtbot, kontext, zustand):
    beispielwoche(kontext)
    seite = _dashboard(qtbot, kontext, zustand)
    vorher = len(kontext.auswertung.hinweise(KW46))
    seite.hinweis_zeilen[0].ausblenden_knopf.click()
    assert len(kontext.auswertung.hinweise(KW46)) == vorher - 1


def test_begruendungsdialog_zeigt_neun_zeilen(qtbot, kontext, zustand):
    from balanceos.praesentation.dialoge.begruendung import BegruendungDialog

    beispielwoche(kontext)
    hinweis = next(h for h in kontext.auswertung.hinweise(KW46) if h.regel == "R01")
    d = BegruendungDialog(hinweis, kontext, zustand)
    qtbot.addWidget(d)
    assert [b for b, _ in d.zeilen] == [
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
    assert d.deaktivieren_knopf.text() == "Regel R01 deaktivieren"
    with qtbot.waitSignal(zustand.daten_geaendert):
        d.deaktivieren_knopf.click()
    assert not next(r for r in kontext.auswertung.regeln() if r.kennung == "R01").aktiv


def test_soll_ist_balken_anteile(qtbot):
    from balanceos.domaene.modell import Bereichsbewertung
    from balanceos.domaene.typen import Bereichstyp
    from balanceos.praesentation.widgets.soll_ist_balken import SollIstBalken

    b = SollIstBalken()
    qtbot.addWidget(b)
    arbeit = Bereichsbewertung(1, 46, 40, 0.85, None, 85, 6)
    b.setze(arbeit, Bereichstyp.OBERGRENZE, "#4C6EF5")
    assert b.text() == "46 / 40 h"
    assert b.anteile() == pytest.approx((40 / 60, 6 / 60))
    viel = Bereichsbewertung(1, 100, 40, 0, None, 0, 60)
    b.setze(viel, Bereichstyp.OBERGRENZE, "#4C6EF5")
    assert sum(b.anteile()) == pytest.approx(1)
