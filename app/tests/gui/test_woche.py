"""Oberflächentests der Wochenansicht und der Aktivitätenliste."""

from datetime import date, time

import pytest

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel

pytestmark = pytest.mark.gui
D = Aktivitaetsstatus.DURCHGEFUEHRT
G = Aktivitaetsstatus.GEPLANT


def _anlegen(kontext):
    bew = kontext.repos.bereiche.nach_schluessel(StandardSchluessel.BEWEGUNG).id
    schlaf = kontext.repos.bereiche.nach_schluessel(StandardSchluessel.SCHLAF).id
    nacht = {"beginn": time(23), "ende": time(6, 30)}
    werte = [
        Aktivitaet("Joggen", bew, date(2026, 11, 16), 45, D, beginn=time(18), ende=time(18, 45)),
        Aktivitaet("Schlaf", schlaf, date(2026, 11, 16), 450, D, **nacht),
        Aktivitaet("Yoga", bew, date(2026, 11, 17), 30, D),
        Aktivitaet("Schlaf", schlaf, date(2026, 11, 22), 450, G, **nacht),
        Aktivitaet("Andere Woche", bew, date(2026, 11, 23), 30, D),
    ]
    return [kontext.repos.aktivitaeten.speichern(a) for a in werte]


def _kalender(qtbot):
    from balanceos.praesentation.widgets.wochenkalender import Wochenkalender

    k = Wochenkalender()
    qtbot.addWidget(k)
    k.resize(900, 700)
    return k


def test_wochenkalender_zeigt_aktivitaeten_der_kw(qtbot, kontext):
    angelegt = _anlegen(kontext)
    k = _kalender(qtbot)
    farben = {b.id: b.farbe for b in kontext.stammdaten.alle_bereiche()}
    k.setze(KW(2026, 47), kontext.aktivitaeten.fuer_woche(KW(2026, 47)), farben, date(2026, 11, 18))
    ids = [i for i, _ in k.bloecke()]
    assert set(ids) == {a.id for a in angelegt[:4]}
    assert ids.count(angelegt[1].id) == 2  # über Mitternacht: zwei Teile
    assert ids.count(angelegt[3].id) == 1  # Sonntag: nur bis 24 Uhr
    rechteck = next(r for i, r in k.bloecke() if i == angelegt[0].id)
    assert k.id_an(rechteck.center()) == angelegt[0].id


def test_wochenkalender_freie_flaeche(qtbot):
    k = _kalender(qtbot)
    k.setze(KW(2026, 47), [], {}, date(2026, 11, 18))
    tag, zeit = k.position_zu_zeit(k.punkt_fuer(2, time(9, 10)))
    assert tag == date(2026, 11, 18)
    assert zeit == time(9, 0)


def test_aktivitaeten_seite_filtert(qtbot, kontext):
    from balanceos.praesentation.seiten.aktivitaeten import AktivitaetenSeite
    from balanceos.praesentation.zustand import Zustand

    _anlegen(kontext)
    seite = AktivitaetenSeite(kontext, Zustand(KW(2026, 47)))
    qtbot.addWidget(seite)
    seite.show()
    assert seite.tabelle.rowCount() == 4
    seite.status_filter.setCurrentIndex(seite.status_filter.findData(G))
    assert seite.tabelle.rowCount() == 1
