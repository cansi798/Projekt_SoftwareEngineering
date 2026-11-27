"""Regressionstests zu Befunden des Phase-3-Reviews: Aktivitätsdialog und Seite „Aktivitäten“."""

from datetime import date, time

import pytest
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QMessageBox

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel, Wochentag

pytestmark = pytest.mark.gui
HEUTE = date(2026, 11, 22)  # Sonntag, KW 47/2026


@pytest.fixture
def kontext22():
    from balanceos.anwendung.kontext import AppKontext

    k = AppKontext.erstellen(":memory:", heute=lambda: HEUTE)
    yield k
    k.db.schliessen()


@pytest.fixture
def zustand22():
    from balanceos.praesentation.zustand import Zustand

    return Zustand(KW.heute(HEUTE))


def _bid(kontext, schluessel=StandardSchluessel.BEWEGUNG) -> int:
    return kontext.repos.bereiche.nach_schluessel(schluessel).id


def _termin_am(kontext, serie, tag):
    return next(t for t in kontext.repos.aktivitaeten.termine_der_serie(serie.id) if t.datum == tag)


# --- A1: Verschieben eines Serientermins mit „auf alle zukünftigen Termine anwenden“ ----------


def test_dialog_verschieben_mit_serie_anwenden_erzeugt_keinen_doppeltermin(
    qtbot, kontext22, zustand22
):
    from balanceos.praesentation.dialoge.aktivitaet import AktivitaetDialog

    vorlage = Aktivitaet(
        titel="Yoga",
        lebensbereich_id=_bid(kontext22),
        datum=date(2026, 11, 23),
        dauer_minuten=60,
        status=Aktivitaetsstatus.GEPLANT,
        beginn=time(18, 0),
        ende=time(19, 0),
    )
    serie = kontext22.aktivitaeten.serie_anlegen(
        vorlage, frozenset({Wochentag.MO, Wochentag.MI}), date(2026, 12, 31)
    )
    termin = _termin_am(kontext22, serie, date(2026, 11, 30))
    d = AktivitaetDialog(kontext22, zustand22, kontext22.aktivitaeten.aktivitaet(termin.id))
    qtbot.addWidget(d)
    d.datum_feld.setDate(QDate(2026, 12, 1))
    d.serie_anwenden.setChecked(True)
    assert d.speichern_knopf.isEnabled()
    d.speichern_knopf.click()

    tage = [t.datum for t in kontext22.repos.aktivitaeten.termine_der_serie(serie.id)]
    assert date(2026, 11, 30) not in tage
    assert tage.count(date(2026, 12, 1)) == 1
    assert kontext22.aktivitaeten.serie(serie.id).ausnahmen == {date(2026, 11, 30)}


# --- A3: „Termin überspringen“ auf der Seite „Aktivitäten“ -----------------------------------


@pytest.fixture
def seite_mit_serie(qtbot, kontext22, zustand22):
    """Serie Mo+So: 16.11. durchgeführt mit Bewertung und Notiz, 22.11. geplant."""
    from balanceos.praesentation.seiten.aktivitaeten import AktivitaetenSeite

    vorlage = Aktivitaet(
        titel="Kurs",
        lebensbereich_id=_bid(kontext22),
        datum=date(2026, 11, 16),
        dauer_minuten=60,
        status=Aktivitaetsstatus.DURCHGEFUEHRT,
        zufriedenheit=5,
        notiz="wichtige Notiz",
    )
    serie = kontext22.aktivitaeten.serie_anlegen(
        vorlage, frozenset({Wochentag.MO, Wochentag.SO}), None
    )
    seite = AktivitaetenSeite(kontext22, zustand22)
    qtbot.addWidget(seite)
    seite.aktualisieren()
    return seite, serie


def _zeile_waehlen(seite, tag: date):
    for zeile in range(seite.tabelle.rowCount()):
        a = seite.tabelle.item(zeile, 0).data(0x0100)  # Qt.ItemDataRole.UserRole
        if a.datum == tag:
            seite.tabelle.selectRow(zeile)
            return a
    raise AssertionError(f"keine Zeile für {tag}")


def _fragen_beantworten(monkeypatch, antwort):
    fragen = []

    def ersatz(_parent, titel, text, *_, **__):
        fragen.append((titel, text))
        return antwort

    monkeypatch.setattr(QMessageBox, "question", ersatz)
    return fragen


def test_ueberspringen_fuer_durchgefuehrten_serientermin_gesperrt(
    qtbot, kontext22, seite_mit_serie, monkeypatch
):
    seite, _ = seite_mit_serie
    fragen = _fragen_beantworten(monkeypatch, QMessageBox.StandardButton.Yes)
    a = _zeile_waehlen(seite, date(2026, 11, 16))
    assert a.status is Aktivitaetsstatus.DURCHGEFUEHRT and a.serie_id is not None
    assert not seite.ueberspringen_knopf.isEnabled()
    seite._ueberspringen()  # auch ein direkter Aufruf löscht nichts
    assert fragen == []
    gelesen = kontext22.aktivitaeten.aktivitaet(a.id)
    assert gelesen is not None and gelesen.notiz == "wichtige Notiz"


def test_ueberspringen_geplanter_termin_fragt_nach_und_bricht_bei_nein_ab(
    qtbot, kontext22, seite_mit_serie, monkeypatch
):
    seite, serie = seite_mit_serie
    fragen = _fragen_beantworten(monkeypatch, QMessageBox.StandardButton.No)
    a = _zeile_waehlen(seite, date(2026, 11, 22))
    assert seite.ueberspringen_knopf.isEnabled()
    seite.ueberspringen_knopf.click()
    assert len(fragen) == 1
    titel, text = fragen[0]
    assert titel == "Termin überspringen"
    assert "22.11.2026" in text and "überspringen" in text
    assert kontext22.aktivitaeten.aktivitaet(a.id) is not None
    assert kontext22.aktivitaeten.serie(serie.id).ausnahmen == set()


def test_ueberspringen_geplanter_termin_nach_bestaetigung(
    qtbot, kontext22, seite_mit_serie, monkeypatch
):
    seite, serie = seite_mit_serie
    fragen = _fragen_beantworten(monkeypatch, QMessageBox.StandardButton.Yes)
    a = _zeile_waehlen(seite, date(2026, 11, 22))
    seite.ueberspringen_knopf.click()
    assert len(fragen) == 1
    assert kontext22.aktivitaeten.aktivitaet(a.id) is None
    assert date(2026, 11, 22) in kontext22.aktivitaeten.serie(serie.id).ausnahmen
