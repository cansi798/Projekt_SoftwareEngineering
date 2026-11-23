"""Oberflächentests von Export-, Demodaten- und Löschdialog (US16–US18)."""

from datetime import date

import pytest

from balanceos.domaene.kalender import KW

pytestmark = pytest.mark.gui


@pytest.fixture
def zustand(heute):
    from balanceos.praesentation.zustand import Zustand

    return Zustand(KW.heute(heute))


@pytest.fixture
def meldungen(monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    gesammelt = []
    for art in ("information", "warning"):
        monkeypatch.setattr(QMessageBox, art, lambda *a, **k: gesammelt.append(a[2]))
    return gesammelt


def test_loeschen_erst_bei_exakter_eingabe_aktiv(qtbot, kontext, zustand):
    from balanceos.praesentation.dialoge.loeschen import LoeschenDialog

    kontext.daten.demodaten_laden()
    d = LoeschenDialog(kontext, zustand)
    qtbot.addWidget(d)
    d.show()
    assert d.focusWidget() is d.abbrechen_knopf
    assert "Bereits exportierte Dateien bleiben erhalten." in d.hinweis_text
    assert not d.loeschen_knopf.isEnabled()
    for falsch in ["löschen", "LÖSCHEN ", "LOESCHEN"]:
        d.eingabe.setText(falsch)
        assert not d.loeschen_knopf.isEnabled()
    d.eingabe.setText("LÖSCHEN")
    assert d.loeschen_knopf.isEnabled()
    with qtbot.waitSignal(zustand.seite_angefordert) as signal:
        d.loeschen_knopf.click()
    assert signal.args == [0]
    assert not kontext.auswertung.gibt_aktivitaeten()


def test_demodaten_dialog_nur_moegliche_option(qtbot, kontext, zustand, meldungen):
    from balanceos.praesentation.dialoge.demodaten import DemodatenDialog

    d = DemodatenDialog(kontext, zustand)
    qtbot.addWidget(d)
    assert d.laden_option.isEnabled() and d.laden_option.isChecked()
    assert not d.entfernen_option.isEnabled()
    d.ausfuehren_knopf.click()
    assert kontext.daten.demodaten_vorhanden()
    d2 = DemodatenDialog(kontext, zustand)
    qtbot.addWidget(d2)
    assert not d2.laden_option.isEnabled()
    assert d2.entfernen_option.isEnabled() and d2.entfernen_option.isChecked()
    d2.ausfuehren_knopf.click()
    assert not kontext.daten.demodaten_vorhanden()


def test_dashboard_laedt_demodaten_und_zeigt_vorwoche(qtbot, kontext, zustand, meldungen):
    from balanceos.praesentation.seiten.dashboard import DashboardSeite

    seite = DashboardSeite(kontext, zustand)
    qtbot.addWidget(seite)
    seite.show()
    seite.demodaten_knopf.click()
    assert kontext.daten.demodaten_vorhanden()
    assert seite.stapel.currentWidget() is seite.inhalt
    # HEUTE ist Mittwoch, 18.11.2026: die aktuelle Woche hat erst drei Tage mit Daten.
    assert zustand.kw == KW(2026, 46)
    assert meldungen[0].startswith("Demodaten geladen. Entfernen unter Einstellungen → Daten.")
    assert "Angezeigt wird KW 46." in meldungen[0]


def test_export_dialog_csv(qtbot, kontext, zustand, meldungen, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    from balanceos.praesentation.dialoge.export import ExportDialog

    kontext.daten.demodaten_laden()
    vorschlaege = []

    def speichern_unter(parent, titel, vorschlag, filter_):
        vorschlaege.append(vorschlag)
        return str(tmp_path / "x.csv"), filter_

    monkeypatch.setattr(QFileDialog, "getSaveFileName", speichern_unter)
    d = ExportDialog(kontext, zustand)
    qtbot.addWidget(d)
    assert d.csv_option.isChecked()
    assert d.von_feld.date().toPython() == date(2026, 11, 16)
    assert d.bis_feld.date().toPython() == date(2026, 11, 22)
    d.exportieren_knopf.click()
    assert vorschlaege[0].endswith("BalanceOS_Aktivitaeten_2026-11-16_2026-11-22.csv")
    assert (tmp_path / "x.csv").exists()
    assert "x.csv" in meldungen[0]


def test_export_dialog_zeitraum_ungueltig(qtbot, kontext, zustand):
    from PySide6.QtCore import QDate

    from balanceos.praesentation.dialoge.export import ExportDialog

    d = ExportDialog(kontext, zustand)
    qtbot.addWidget(d)
    d.bis_feld.setDate(QDate(2026, 11, 1))
    assert d.zeitraum_fehler.text() == "Ende vor Beginn des Zeitraums."
    assert not d.exportieren_knopf.isEnabled()
    d.json_option.setChecked(True)
    assert d.exportieren_knopf.isEnabled()


def test_dashboard_neuaufbau_ohne_sichtbare_altzeilen(qtbot, kontext, zustand, meldungen):
    from balanceos.praesentation.seiten.dashboard import DashboardSeite, HinweisZeile

    seite = DashboardSeite(kontext, zustand)
    qtbot.addWidget(seite)
    seite.show()
    seite.demodaten_knopf.click()
    seite.aktualisieren()
    # Alte Zeilen dürfen bis zur verzögerten Freigabe nicht mehr im Dashboard hängen.
    assert len(seite.findChildren(HinweisZeile)) == len(seite.hinweis_zeilen) == 5
