"""Oberflächentests des Dialogs „Aktivität erfassen/bearbeiten“."""

from datetime import date, time

import pytest
from PySide6.QtCore import QDate, QTime

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel, Wochentag

pytestmark = pytest.mark.gui
HEUTE = date(2026, 11, 18)


@pytest.fixture
def zustand(kontext):
    from balanceos.praesentation.zustand import Zustand

    return Zustand(KW.heute(HEUTE))


def _dialog(qtbot, kontext, zustand, **k):
    from balanceos.praesentation.dialoge.aktivitaet import AktivitaetDialog

    d = AktivitaetDialog(kontext, zustand, **k)
    qtbot.addWidget(d)
    return d


def _bereich_waehlen(d, kontext, schluessel):
    bid = kontext.repos.bereiche.nach_schluessel(schluessel).id
    d.bereich_feld.setCurrentIndex(d.bereich_feld.findData(bid))


def test_speichern_gesperrt_bei_leerem_titel(qtbot, kontext, zustand):
    d = _dialog(qtbot, kontext, zustand, datum=HEUTE)
    assert d.windowTitle() == "Aktivität erfassen"
    assert not d.speichern_knopf.isEnabled()
    assert "Titel" in d.speichern_knopf.toolTip()
    d.titel_feld.setText("Joggen")
    assert d.speichern_knopf.isEnabled()


def test_vorbelegung_status_heute_durchgefuehrt(qtbot, kontext, zustand):
    d = _dialog(qtbot, kontext, zustand, datum=HEUTE)
    assert d.status_feld.currentData() is Aktivitaetsstatus.DURCHGEFUEHRT
    d2 = _dialog(qtbot, kontext, zustand, datum=date(2026, 11, 20))
    assert d2.status_feld.currentData() is Aktivitaetsstatus.GEPLANT


def test_enddatum_vor_datum_zeigt_meldung(qtbot, kontext, zustand):
    d = _dialog(qtbot, kontext, zustand, datum=HEUTE)
    d.titel_feld.setText("Joggen")
    d.wiederholen_feld.setChecked(True)
    d.enddatum_aktiv.setChecked(True)
    d.enddatum_feld.setDate(QDate(2026, 11, 17))
    assert d.fehlerlabels["enddatum"].text() == "Enddatum darf nicht vor dem Datum liegen."
    assert not d.fehlerlabels["enddatum"].isHidden()
    assert not d.speichern_knopf.isEnabled()


def test_bewertung_nur_bei_durchgefuehrt_aktiv(qtbot, kontext, zustand):
    d = _dialog(qtbot, kontext, zustand, datum=HEUTE)
    assert d.skalen["zufriedenheit"].isEnabled()
    d.status_feld.setCurrentIndex(d.status_feld.findData(Aktivitaetsstatus.GEPLANT))
    assert not d.skalen["zufriedenheit"].isEnabled()


def test_bewegungsart_nur_im_bereich_bewegung_sichtbar(qtbot, kontext, zustand):
    d = _dialog(qtbot, kontext, zustand, datum=HEUTE)
    _bereich_waehlen(d, kontext, StandardSchluessel.ARBEIT)
    assert d.bewegungsart_feld.isHidden()
    _bereich_waehlen(d, kontext, StandardSchluessel.BEWEGUNG)
    assert not d.bewegungsart_feld.isHidden()


def test_folgetag_hinweis(qtbot, kontext, zustand):
    d = _dialog(qtbot, kontext, zustand, datum=HEUTE)
    d.modus_zeit.setChecked(True)
    d.beginn_feld.setTime(QTime(23, 0))
    d.ende_feld.setTime(QTime(6, 30))
    assert not d.folgetag_label.isHidden()
    assert "450" in d.dauer_info.text()


def test_speichern_legt_aktivitaet_an_und_signalisiert(qtbot, kontext, zustand):
    d = _dialog(qtbot, kontext, zustand, datum=HEUTE)
    d.titel_feld.setText("Joggen")
    _bereich_waehlen(d, kontext, StandardSchluessel.BEWEGUNG)
    d.dauer_feld.setValue(45)
    d.skalen["zufriedenheit"].setze(4)
    with qtbot.waitSignal(zustand.daten_geaendert):
        d.speichern_knopf.click()
    alle = kontext.repos.aktivitaeten.alle()
    assert len(alle) == 1
    assert (alle[0].titel, alle[0].dauer_minuten, alle[0].zufriedenheit) == ("Joggen", 45, 4)


def test_wiederholung_legt_serie_an(qtbot, kontext, zustand):
    d = _dialog(qtbot, kontext, zustand, datum=date(2026, 11, 17))
    d.titel_feld.setText("Kurs")
    d.wiederholen_feld.setChecked(True)
    assert d.wochentag_felder[Wochentag.DI].isChecked()
    d.enddatum_aktiv.setChecked(True)
    d.enddatum_feld.setDate(QDate(2026, 12, 1))
    d.speichern_knopf.click()
    assert len(kontext.repos.serien.alle()) == 1
    assert len(kontext.repos.aktivitaeten.alle()) == 3


def test_bearbeiten_modus(qtbot, kontext, zustand):
    bid = kontext.repos.bereiche.nach_schluessel(StandardSchluessel.BEWEGUNG).id
    a = kontext.aktivitaeten.speichern(
        Aktivitaet(
            "Joggen",
            bid,
            HEUTE,
            45,
            Aktivitaetsstatus.DURCHGEFUEHRT,
            beginn=time(18),
            ende=time(18, 45),
        )
    )
    d = _dialog(qtbot, kontext, zustand, aktivitaet=a)
    assert d.windowTitle() == "Aktivität bearbeiten"
    assert d.titel_feld.text() == "Joggen" and d.modus_zeit.isChecked()
    assert not d.loeschen_knopf.isHidden()
    assert d.ueberspringen_knopf.isHidden()
    assert d.wiederholen_feld.isHidden()
    d.titel_feld.setText("Lauf")
    d.speichern_knopf.click()
    assert kontext.repos.aktivitaeten.nach_id(a.id).titel == "Lauf"


def test_datum_nimmt_nur_gueltige_daten_an(qtbot, kontext, zustand):
    """Validierungszeile „Datum“: Format TT.MM.JJJJ, ungültige Daten werden nicht übernommen."""
    d = _dialog(qtbot, kontext, zustand, datum=HEUTE)
    assert d.datum_feld.displayFormat() == "dd.MM.yyyy"
    vorher = d.datum_feld.date()
    d.datum_feld.setDate(QDate(2026, 2, 31))  # 31. Februar existiert nicht
    assert d.datum_feld.date() == vorher
    assert d.datum_feld.date().isValid()
