"""Oberflächentests von Reflexion, WHO-5-Dialog, Statistik und Liniendiagramm (US20–US22)."""

from datetime import date

import pytest

from balanceos.domaene.kalender import KW

pytestmark = pytest.mark.gui


@pytest.fixture
def zustand(heute):
    from balanceos.praesentation.zustand import Zustand

    return Zustand(KW.heute(heute))


def test_alle_seiten_laden_mit_leerer_db(qtbot, kontext, zustand):
    from balanceos.praesentation.hauptfenster import SEITEN

    for klasse in SEITEN:
        seite = klasse(kontext, zustand)
        qtbot.addWidget(seite)
        seite.aktualisieren()


def test_statistik_ohne_daten(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.statistik import StatistikSeite

    s = StatistikSeite(kontext, zustand)
    qtbot.addWidget(s)
    s.show()
    assert s.stapel.currentWidget() is s.leer_label
    assert s.leer_label.text() == "Noch keine bewertbaren Wochen."


def test_statistik_mit_demodaten(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.statistik import StatistikSeite

    kontext.daten.demodaten_laden()
    kontext.stammdaten.einstellungen_speichern(
        kontext.stammdaten.einstellungen().__class__(0.6, True)
    )
    s = StatistikSeite(kontext, zustand)
    qtbot.addWidget(s)
    s.show()
    assert s.stapel.currentWidget() is s.inhalt
    namen = [name for name, _, _ in s.diagramm.reihen]
    assert len(namen) == 11 and namen[-1] == "Gesamt-Score (programmeigen)"
    assert s.diagramm.beschriftungen[-1] == "KW 47"
    assert s.tabelle.rowCount() == 8 and s.tabelle.columnCount() == 11
    # KW 40 hat nur drei Tage mit Daten: keine Scores, im Diagramm eine Lücke.
    assert all(werte[0] is None for _, _, werte in s.diagramm.reihen)


def test_liniendiagramm_reihe_ausblenden(qtbot):
    from balanceos.praesentation.widgets.liniendiagramm import Liniendiagramm

    d = Liniendiagramm()
    qtbot.addWidget(d)
    d.setze_reihen(
        ["KW 1", "KW 2", "KW 3"], [("A", "#1C7ED6", [10, None, 80]), ("B", "#E03131", [50, 60, 70])]
    )
    assert d.sichtbare_reihen() == ["A", "B"]
    d.legende_felder["A"].setChecked(False)
    assert d.sichtbare_reihen() == ["B"]
    d.resize(500, 300)
    d.grab()  # zeichnet ohne Ausnahme, auch mit Lücke


def test_who5_dialog_auswerten_erst_vollstaendig(qtbot, kontext, zustand):
    from balanceos.praesentation.dialoge.who5 import Who5Dialog

    d = Who5Dialog(kontext, zustand)
    qtbot.addWidget(d)
    assert len(d.optionen) == 5 and all(len(z) == 6 for z in d.optionen)
    assert not d.auswerten_knopf.isEnabled()
    for zeile, wert in zip(d.optionen, (2, 3, 2, 2, 2), strict=True):
        zeile[wert].setChecked(True)
        assert d.auswerten_knopf.isEnabled() is (zeile is d.optionen[-1])
    d.auswerten_knopf.click()
    assert d.ergebnis_label.text().startswith("Rohwert 11 von 25 · 44 %")
    assert not d.empfehlung_label.isHidden()
    assert kontext.reflexion.who5_verlauf()[0].antworten == (2, 3, 2, 2, 2)


def test_who5_dialog_ohne_empfehlung(qtbot, kontext, zustand):
    from balanceos.praesentation.dialoge.who5 import Who5Dialog

    d = Who5Dialog(kontext, zustand)
    qtbot.addWidget(d)
    for zeile in d.optionen:
        zeile[4].setChecked(True)
    d.auswerten_knopf.click()
    assert d.ergebnis_label.text().startswith("Rohwert 20 von 25 · 80 %")
    assert d.empfehlung_label.isHidden()


def test_reflexion_seite_speichert_und_laedt(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.reflexion import ReflexionSeite

    s = ReflexionSeite(kontext, zustand)
    qtbot.addWidget(s)
    s.show()
    assert [f.text() for f in s.fragen_labels] == [
        "Was ist diese Woche gut gelungen?",
        "Was ist zu kurz gekommen?",
        "Was nehme ich mir für die nächste Woche vor?",
    ]
    s.antwort_felder[0].setPlainText("Zweimal joggen")
    assert s.zaehler[0].text() == "14/1000"
    s.stimmung.setze(4)
    s.speichern_knopf.click()
    r = kontext.reflexion.reflexion(KW(2026, 47))
    assert r.antworten == ("Zweimal joggen", "", "") and r.stimmung == 4
    zustand.setze_kw(KW(2026, 46))
    s.aktualisieren()
    assert s.antwort_felder[0].toPlainText() == ""
    zustand.setze_kw(KW(2026, 47))
    s.aktualisieren()
    assert s.antwort_felder[0].toPlainText() == "Zweimal joggen"


def test_reflexion_zeigt_letztes_who5(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.reflexion import ReflexionSeite

    kontext.reflexion.who5_speichern(date(2026, 11, 15), [3, 4, 3, 2, 4])
    s = ReflexionSeite(kontext, zustand)
    qtbot.addWidget(s)
    s.show()
    assert "64 %" in s.who5_label.text() and "15.11.2026" in s.who5_label.text()
    assert s.who5_etikett.text() == "validiertes Instrument"
