"""Regressionstests zu Befunden des Phase-3-Reviews: Wochenansicht und Wochenkalender (US09)."""

from datetime import date, time

import pytest

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel

pytestmark = pytest.mark.gui
D = Aktivitaetsstatus.DURCHGEFUEHRT
G = Aktivitaetsstatus.GEPLANT


def _bid(kontext, schluessel):
    return kontext.repos.bereiche.nach_schluessel(schluessel).id


def _schlaf_sonntag(kontext):
    """Schlaf vom Sonntag, 22.11. (KW 47), 23:00 bis Montag, 23.11. (KW 48), 06:30."""
    return kontext.repos.aktivitaeten.speichern(
        Aktivitaet(
            "Schlaf",
            _bid(kontext, StandardSchluessel.SCHLAF),
            date(2026, 11, 22),
            450,
            D,
            beginn=time(23),
            ende=time(6, 30),
        )
    )


def _kalender(qtbot):
    from balanceos.praesentation.widgets.wochenkalender import Wochenkalender

    k = Wochenkalender()
    qtbot.addWidget(k)
    k.resize(900, 700)
    return k


def _woche(qtbot, kontext, kw):
    from balanceos.praesentation.seiten.woche import WocheSeite
    from balanceos.praesentation.zustand import Zustand

    seite = WocheSeite(kontext, Zustand(kw))
    qtbot.addWidget(seite)
    seite.resize(1000, 800)
    seite.aktualisieren()
    return seite


# --- B6: Aktivität über Mitternacht vom Sonntag der Vorwoche --------------------------------


def test_wochenkalender_zeichnet_ueberlauf_vom_sonntag_der_vorwoche(qtbot, kontext):
    schlaf = _schlaf_sonntag(kontext)
    k = _kalender(qtbot)
    k.setze(KW(2026, 48), [schlaf], {}, date(2026, 11, 25))
    bloecke = [r for i, r in k.bloecke() if i == schlaf.id]
    assert len(bloecke) == 1  # nur der Teil am Montag, nicht der Beginn am Sonntag
    montag = k.punkt_fuer(0, time(3, 0))
    assert bloecke[0].contains(montag)
    assert bloecke[0].top() == pytest.approx(k.punkt_fuer(0, time(0, 0)).y() - 1)
    assert bloecke[0].bottom() == pytest.approx(k.punkt_fuer(0, time(6, 30)).y() - 1)


def test_wochenkalender_ignoriert_vorwoche_ohne_ueberlauf(qtbot, kontext):
    bew = _bid(kontext, StandardSchluessel.BEWEGUNG)
    tagsueber = kontext.repos.aktivitaeten.speichern(
        Aktivitaet("Joggen", bew, date(2026, 11, 22), 45, D, beginn=time(18), ende=time(18, 45))
    )
    ohne_zeit = kontext.repos.aktivitaeten.speichern(
        Aktivitaet("Yoga", bew, date(2026, 11, 22), 30, D)
    )
    k = _kalender(qtbot)
    k.setze(KW(2026, 48), [tagsueber, ohne_zeit, ohne_zeit], {}, date(2026, 11, 25))
    assert k.bloecke() == []
    assert k._ohne_zeilen == 1


def test_wochenseite_zeigt_ueberlauf_ohne_ihn_zu_zaehlen(qtbot, kontext):
    _schlaf_sonntag(kontext)
    seite = _woche(qtbot, kontext, KW(2026, 48))
    assert len(seite.kalender.bloecke()) == 1
    assert seite.summe_label.text().startswith("0 Aktivitäten · 0,0 h durchgeführt")


def test_wochenseite_vorwoche_zaehlt_ueberlauf_einmal(qtbot, kontext):
    schlaf = _schlaf_sonntag(kontext)
    seite = _woche(qtbot, kontext, KW(2026, 47))
    assert [i for i, _ in seite.kalender.bloecke()] == [schlaf.id]  # Sonntag bis 24 Uhr
    assert seite.summe_label.text().startswith("1 Aktivität · 7,5 h durchgeführt")


# --- C3: Singular und Plural in der Zusammenfassung ------------------------------------------


def test_wochenseite_zusammenfassung_singular_und_plural(qtbot, kontext):
    bew = _bid(kontext, StandardSchluessel.BEWEGUNG)
    seite = _woche(qtbot, kontext, KW(2026, 47))
    assert seite.summe_label.text().startswith("0 Aktivitäten ·")
    kontext.repos.aktivitaeten.speichern(Aktivitaet("Yoga", bew, date(2026, 11, 17), 30, D))
    seite.aktualisieren()
    assert seite.summe_label.text().startswith("1 Aktivität ·")
    kontext.repos.aktivitaeten.speichern(Aktivitaet("Lauf", bew, date(2026, 11, 18), 30, D))
    seite.aktualisieren()
    assert seite.summe_label.text().startswith("2 Aktivitäten ·")


# --- C5: Breite überlappender Blöcke und Achsenbeschriftung ----------------------------------


def test_nur_ueberlappende_bloecke_teilen_sich_die_breite(qtbot, kontext):
    bew = _bid(kontext, StandardSchluessel.BEWEGUNG)
    tag = date(2026, 11, 24)
    werte = [
        Aktivitaet("Joggen", bew, tag, 60, D, beginn=time(8), ende=time(9)),
        Aktivitaet("Lesen", bew, tag, 60, G, beginn=time(8, 30), ende=time(9, 30)),
        Aktivitaet("Kochen", bew, tag, 90, D, beginn=time(14), ende=time(15, 30)),
        Aktivitaet("Spaziergang", bew, date(2026, 11, 25), 60, D, beginn=time(14), ende=time(15)),
    ]
    gespeichert = [kontext.repos.aktivitaeten.speichern(a) for a in werte]
    k = _kalender(qtbot)
    k.setze(KW(2026, 48), gespeichert, {}, date(2026, 11, 25))
    breite = {i: r.width() for i, r in k.bloecke()}
    voll = breite[gespeichert[3].id]  # allein am Tag
    joggen, lesen, kochen = (breite[a.id] for a in gespeichert[:3])
    assert kochen == pytest.approx(voll)
    assert joggen == pytest.approx(lesen)
    assert joggen < voll / 2 + 1


def test_beschriftung_ohne_zeit_ueberlappt_nicht_mit_null_uhr(qtbot):
    k = _kalender(qtbot)
    k.setze(KW(2026, 48), [], {}, date(2026, 11, 25))
    beschriftungen = dict(k.achsenbeschriftungen())
    ohne = beschriftungen["ohne\nZeit"]
    null_uhr = beschriftungen["00:00"]
    assert ohne.bottom() <= null_uhr.top()
    assert ohne.top() >= 38  # unterhalb der Kopfzeile
