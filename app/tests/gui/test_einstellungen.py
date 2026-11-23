"""Oberflächentests von Einstellungen und Balance-Kompass (US02–US04, US14, US15, US19)."""

import pytest

from balanceos.domaene.kalender import KW
from balanceos.domaene.typen import StandardSchluessel as S

pytestmark = pytest.mark.gui


@pytest.fixture
def zustand(heute):
    from balanceos.praesentation.zustand import Zustand

    return Zustand(KW.heute(heute))


@pytest.fixture
def seite(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.einstellungen import EinstellungenSeite

    s = EinstellungenSeite(kontext, zustand)
    qtbot.addWidget(s)
    s.show()
    return s


def _id(kontext, schluessel) -> int:
    return kontext.repos.bereiche.nach_schluessel(schluessel).id


def test_vier_reiter(seite):
    namen = [seite.reiter.tabText(i) for i in range(seite.reiter.count())]
    assert namen == ["Lebensbereiche", "Wunschprofil", "Regeln", "Daten"]


def test_wunschprofil_ungueltige_summe_nicht_gespeichert(seite, kontext):
    schlaf = _id(kontext, S.SCHLAF)
    seite.soll_felder[schlaf].setValue(82)  # 143 − 56 + 82 = 169 h
    assert kontext.repos.bereiche.nach_id(schlaf).soll_stunden == 56
    assert seite.wunsch_fehler.text() == "Summe übersteigt 168 h pro Woche."
    assert not seite.wunsch_fehler.isHidden()
    seite.soll_felder[schlaf].setValue(60)
    assert kontext.repos.bereiche.nach_id(schlaf).soll_stunden == 60
    assert seite.wunsch_fehler.isHidden()
    assert seite.summe_label.text() == "147 von 168 h verplant"


def test_wunschprofil_gewicht_und_gesamtscore(seite, kontext, zustand, qtbot):
    arbeit = _id(kontext, S.ARBEIT)
    with qtbot.waitSignal(zustand.daten_geaendert):
        seite.gewicht_felder[arbeit].setValue(3)
    assert kontext.repos.bereiche.nach_id(arbeit).gewicht == 3
    seite.gesamtscore_feld.setChecked(True)
    seite.alpha_regler.setValue(3)
    e = kontext.stammdaten.einstellungen()
    assert e.gesamtscore_anzeigen and e.alpha == pytest.approx(0.3)
    assert seite.alpha_label.text() == "0,3"


def test_regel_schalter_deaktiviert_regel(seite, kontext, zustand, qtbot):
    assert seite.regel_schalter["R03"].isChecked()
    with qtbot.waitSignal(zustand.daten_geaendert):
        seite.regel_schalter["R03"].setChecked(False)
    assert not next(r for r in kontext.auswertung.regeln() if r.kennung == "R03").aktiv


def test_standardbereich_nicht_loeschbar_meldung(seite, kontext, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    meldungen = []
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: meldungen.append(a[2]))
    seite.bereich_tabelle.selectRow(0)
    seite.loeschen_knopf.click()
    assert meldungen == ["Standardbereiche können nicht gelöscht, nur deaktiviert werden."]
    assert len(kontext.stammdaten.alle_bereiche()) == 10


def test_bereich_deaktivieren_und_aktivieren(seite, kontext):
    seite.bereich_tabelle.selectRow(4)  # Hobbys
    hobbys = _id(kontext, S.HOBBYS)
    assert seite.aktiv_knopf.text() == "Deaktivieren"
    seite.aktiv_knopf.click()
    assert not kontext.repos.bereiche.nach_id(hobbys).aktiv
    seite.bereich_tabelle.selectRow(4)
    assert seite.aktiv_knopf.text() == "Aktivieren"
    seite.aktiv_knopf.click()
    assert kontext.repos.bereiche.nach_id(hobbys).aktiv


def test_lebensbereich_dialog_neu(qtbot, kontext, zustand):
    from balanceos.praesentation.dialoge.lebensbereich import LebensbereichDialog

    d = LebensbereichDialog(kontext, zustand)
    qtbot.addWidget(d)
    assert not d.speichern_knopf.isEnabled()
    d.name_feld.setText("Bewegung")
    assert d.fehlerlabels["name"].text() == "Name existiert bereits."
    assert not d.speichern_knopf.isEnabled()
    d.name_feld.setText("Garten")
    d.soll_feld.setValue(2.5)
    assert d.verplant_label.text() == "145,5 von 168 h verplant"
    assert len(d.farb_knoepfe) == 12
    d.farb_knoepfe[10].click()
    d.speichern_knopf.click()
    garten = next(b for b in kontext.stammdaten.alle_bereiche() if b.name == "Garten")
    assert (garten.soll_stunden, garten.farbe) == (2.5, "#C2255C")


def test_kompass_zeigt_sechs_modelle(qtbot, kontext, zustand):
    from PySide6.QtWidgets import QLabel

    from balanceos.praesentation.seiten.kompass import KompassSeite

    s = KompassSeite(kontext, zustand)
    qtbot.addWidget(s)
    s.show()
    assert s.modell_liste.count() == 6
    assert "kein Medizinprodukt" in s.hinweis_kasten_text.text()
    s.modell_liste.setCurrentRow(3)
    assert s.name_label.text() == "WHO-Bewegungsleitlinie"
    assert s.evidenz_label.text() == "Empfehlung"
    assert "Bull" in s.quelle_label.text()
    assert [kennung for kennung, _ in s.regel_zeilen] == ["R01", "R02"]
    titel = [w.text() for w in s.findChildren(QLabel) if w.parent() is not None]
    assert "Regeln in BalanceOS" in titel
