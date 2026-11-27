"""Oberflächentests für Hauptfenster und Navigation."""

import pytest

from balanceos.domaene.kalender import KW

pytestmark = pytest.mark.gui


@pytest.fixture
def fenster(qtbot, kontext):
    from balanceos.praesentation.hauptfenster import Hauptfenster
    from balanceos.praesentation.zustand import Zustand

    zustand = Zustand(KW.heute(kontext.heute()))
    f = Hauptfenster(kontext, zustand)
    qtbot.addWidget(f)
    f.show()
    return f


def test_sieben_seiten_in_fester_reihenfolge(fenster):
    leiste = fenster.seitenleiste
    texte = [leiste.item(i).text() for i in range(leiste.count())]
    assert texte == [
        "Dashboard",
        "Woche",
        "Aktivitäten",
        "Statistik",
        "Reflexion",
        "Kompass",
        "Einstellungen",
    ]
    assert fenster.stapel.count() == 7


def test_navigation_wechselt_seite_und_titel(fenster):
    fenster.seitenleiste.setCurrentRow(5)
    assert fenster.stapel.currentIndex() == 5
    assert fenster.titel_label.text() == "Kompass"


def test_wochenblaettern_aendert_kw(qtbot, fenster):
    start = fenster.zustand.kw
    with qtbot.waitSignal(fenster.zustand.woche_geaendert):
        fenster.vor_knopf.click()
    assert fenster.zustand.kw == start.verschoben(1)
    assert fenster.kw_label.text().startswith(start.verschoben(1).label())
    fenster.zurueck_knopf.click()
    fenster.zurueck_knopf.click()
    assert fenster.zustand.kw == start.verschoben(-1)
    fenster.heute_knopf.click()
    assert fenster.zustand.kw == start


def test_mindestgroesse(fenster):
    assert fenster.minimumWidth() == 960
    assert fenster.minimumHeight() == 520
