"""Regressionstests zu den Review-Befunden der Phase 3 an der Oberfläche.

Abgedeckt sind Datenverlust in der Wochenreflexion (A2), fehlende Feldmeldungen (B7),
als HTML gedeutete Bereichsnamen (B1), Fenstergröße (B2), Meldung bei Datenbankfehlern
(B3), Abweichung und „zu wenig Daten“ im Dashboard (B4, B5), Stundenrundung (C2),
Einzahl im WHO-5-Dialog (C3) und abgelehnte Werte im Wunschprofil (C4).
"""

import sqlite3
import sys
from dataclasses import replace
from datetime import timedelta

import pytest
from PySide6 import QtGui
from PySide6.QtCore import QObject, QSize, Qt, Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QApplication, QLabel, QMessageBox

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet, Bereichsbewertung, Lebensbereich
from balanceos.domaene.typen import Aktivitaetsstatus, Bereichstyp
from balanceos.domaene.typen import StandardSchluessel as S
from balanceos.domaene.validierung import M_AKTIV, M_LEITFRAGE, M_LOESCHEN, M_SOLL, M_SUMME

pytestmark = pytest.mark.gui
KW46 = KW(2026, 46)
KW47 = KW(2026, 47)
D = Aktivitaetsstatus.DURCHGEFUEHRT


@pytest.fixture
def zustand():
    from balanceos.praesentation.zustand import Zustand

    return Zustand(KW47)


def sichtbar(label: QLabel) -> str:
    """Text, den ein QLabel tatsächlich darstellt (Rich Text aufgelöst)."""
    text = label.text()
    fmt = label.textFormat()
    rich = fmt == Qt.TextFormat.RichText or (
        fmt == Qt.TextFormat.AutoText and QtGui.Qt.mightBeRichText(text)
    )
    doc = QTextDocument()
    if rich:
        doc.setHtml(text)
    else:
        doc.setPlainText(text)
    return doc.toPlainText()


def _id(kontext, schluessel) -> int:
    return kontext.repos.bereiche.nach_schluessel(schluessel).id


def _anlegen(kontext, schluessel, kw, tag, minuten, **k) -> int:
    bid = _id(kontext, schluessel)
    datum = kw.montag() + timedelta(days=tag)
    kontext.repos.aktivitaeten.speichern(Aktivitaet("x", bid, datum, minuten, D, **k))
    return bid


def _umbenennen(kontext, schluessel, name) -> int:
    b = kontext.repos.bereiche.nach_schluessel(schluessel)
    kontext.stammdaten.speichern(replace(b, name=name))
    return b.id


# --- A2: Wochenreflexion ohne Datenverlust ------------------------------------------------


@pytest.fixture
def reflexion(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.reflexion import ReflexionSeite

    s = ReflexionSeite(kontext, zustand)
    qtbot.addWidget(s)
    s.show()
    return s


@pytest.fixture
def fragen(monkeypatch):
    """Ersetzt QMessageBox.question; ``fragen.antwort`` legt die gewählte Schaltfläche fest."""

    class Fragen(list):
        antwort = QMessageBox.StandardButton.Discard

    gesammelt = Fragen()

    def ersatz(_parent, _titel, text, *_a, **_k):
        gesammelt.append(text)
        return gesammelt.antwort

    monkeypatch.setattr(QMessageBox, "question", ersatz)
    return gesammelt


def test_a2_who5_auswertung_behaelt_ungespeicherten_text(qtbot, kontext, zustand, reflexion):
    from balanceos.praesentation.dialoge.who5 import Who5Dialog

    reflexion.antwort_felder[0].setPlainText("Mein ungespeicherter Text")
    d = Who5Dialog(kontext, zustand, reflexion)
    qtbot.addWidget(d)
    for zeile in d.optionen:
        zeile[3].setChecked(True)
    d.auswerten_knopf.click()
    assert reflexion.antwort_felder[0].toPlainText() == "Mein ungespeicherter Text"
    assert "60 %" in reflexion.who5_label.text()


def test_a2_wochenwechsel_ohne_aenderung_fragt_nicht(kontext, zustand, reflexion, fragen):
    kontext.reflexion.reflexion_speichern(KW46, ("Alt", "", ""), None)
    zustand.setze_kw(KW46)
    assert fragen == []
    assert reflexion.antwort_felder[0].toPlainText() == "Alt"


def test_a2_wochenwechsel_fragt_und_verwirft(kontext, zustand, reflexion, fragen):
    reflexion.antwort_felder[0].setPlainText("Entwurf")
    fragen.antwort = QMessageBox.StandardButton.Discard
    zustand.setze_kw(KW46)
    assert len(fragen) == 1 and KW47.label() in fragen[0]
    assert reflexion.antwort_felder[0].toPlainText() == ""
    assert kontext.reflexion.reflexion(KW47) is None
    zustand.setze_kw(KW47)
    assert len(fragen) == 1, "nach dem Verwerfen keine zweite Rückfrage"


def test_a2_wochenwechsel_fragt_und_speichert_alte_woche(kontext, zustand, reflexion, fragen):
    reflexion.antwort_felder[1].setPlainText("Zu wenig Schlaf")
    reflexion.stimmung.setze(2)
    fragen.antwort = QMessageBox.StandardButton.Save
    zustand.setze_kw(KW46)
    r = kontext.reflexion.reflexion(KW47)
    assert r is not None and r.antworten == ("", "Zu wenig Schlaf", "") and r.stimmung == 2
    assert reflexion.antwort_felder[1].toPlainText() == ""
    assert reflexion.kw_label.text() == KW46.zeitraum_text()


def test_a2_wochenwechsel_abbrechen_bleibt_in_alter_woche(qtbot, zustand, reflexion, fragen):
    reflexion.antwort_felder[2].setPlainText("Mehr Sport")
    fragen.antwort = QMessageBox.StandardButton.Cancel
    zustand.setze_kw(KW46)
    qtbot.waitUntil(lambda: zustand.kw == KW47)
    assert reflexion.antwort_felder[2].toPlainText() == "Mehr Sport"
    assert reflexion.kw_label.text() == KW47.zeitraum_text()


def test_a2_wochenwechsel_fragt_auch_bei_verborgener_seite(kontext, zustand, reflexion, fragen):
    reflexion.antwort_felder[0].setPlainText("Entwurf")
    reflexion.hide()
    fragen.antwort = QMessageBox.StandardButton.Save
    zustand.setze_kw(KW46)
    assert len(fragen) == 1
    assert kontext.reflexion.reflexion(KW47).antworten[0] == "Entwurf"
    reflexion.show()
    assert reflexion.antwort_felder[0].toPlainText() == ""


def test_a2_nach_speichern_keine_rueckfrage(zustand, reflexion, fragen):
    reflexion.antwort_felder[0].setPlainText("Gespeichert")
    reflexion.speichern_knopf.click()
    zustand.setze_kw(KW46)
    assert fragen == []


# --- B7: Meldungen der Validierungstabelle -------------------------------------------------


def test_b7_leitfrage_zu_lang_meldung_am_feld(reflexion):
    feld = reflexion.antwort_felder[1]
    feld.setPlainText("x" * 1001)
    meldung = reflexion.feld_fehler[1]
    assert meldung.text() == M_LEITFRAGE and not meldung.isHidden()
    assert feld.property("fehler") == "true"
    assert not reflexion.speichern_knopf.isEnabled()
    feld.setPlainText("x" * 1000)
    assert meldung.isHidden() and feld.property("fehler") == "false"
    assert reflexion.speichern_knopf.isEnabled()


def test_b7_loeschbestaetigung_meldung(qtbot, kontext, zustand):
    from balanceos.praesentation.dialoge.loeschen import LoeschenDialog

    d = LoeschenDialog(kontext, zustand)
    qtbot.addWidget(d)
    assert d.fehler_label.isHidden(), "leeres Feld: noch keine Meldung"
    d.eingabe.setText("löschen")
    assert d.fehler_label.text() == M_LOESCHEN and not d.fehler_label.isHidden()
    assert d.eingabe.property("fehler") == "true"
    assert not d.loeschen_knopf.isEnabled()
    d.eingabe.setText("LÖSCHEN")
    assert d.fehler_label.isHidden() and d.eingabe.property("fehler") == "false"
    assert d.loeschen_knopf.isEnabled()


def _bereich_dialog(qtbot, kontext, zustand, bereich=None):
    from balanceos.praesentation.dialoge.lebensbereich import LebensbereichDialog

    d = LebensbereichDialog(kontext, zustand, bereich)
    qtbot.addWidget(d)
    return d


def test_b7_lebensbereich_soll_rot_umrandet(qtbot, kontext, zustand):
    d = _bereich_dialog(qtbot, kontext, zustand, kontext.repos.bereiche.nach_schluessel(S.HOBBYS))
    d.soll_feld.setValue(0.3)
    assert d.fehlerlabels["soll"].text() == M_SOLL
    assert d.soll_feld.property("fehler") == "true"
    d.soll_feld.setValue(0.5)
    assert d.soll_feld.property("fehler") == "false"


def test_b7_lebensbereich_summe_rot_umrandet(qtbot, kontext, zustand):
    d = _bereich_dialog(qtbot, kontext, zustand, kontext.repos.bereiche.nach_schluessel(S.SCHLAF))
    d.soll_feld.setValue(82)  # 143 − 56 + 82 = 169 h
    assert d.fehlerlabels["summe"].text() == M_SUMME
    assert d.soll_feld.property("fehler") == "true"
    d.soll_feld.setValue(60)
    assert d.soll_feld.property("fehler") == "false"


def test_b7_lebensbereich_aktiv_rot_umrandet(qtbot, kontext, zustand):
    for b in kontext.repos.bereiche.alle():
        kontext.repos.bereiche.speichern(replace(b, soll_stunden=0))
    d = _bereich_dialog(qtbot, kontext, zustand, kontext.repos.bereiche.nach_schluessel(S.HOBBYS))
    assert d.fehlerlabels["aktiv"].text() == M_AKTIV
    assert d.aktiv_feld.property("fehler") == "true"
    d.soll_feld.setValue(2)
    assert d.aktiv_feld.property("fehler") == "false"


# --- B1: Bereichsnamen werden nicht als HTML gedeutet --------------------------------------


def _dashboard(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.dashboard import DashboardSeite

    seite = DashboardSeite(kontext, zustand)
    qtbot.addWidget(seite)
    seite.show()
    return seite


def _texte(widget) -> list[str]:
    return [sichtbar(label) for label in widget.findChildren(QLabel)]


def test_b1_dashboard_zeigt_namen_mit_spitzen_klammern(qtbot, kontext, zustand):
    _umbenennen(kontext, S.FAMILIE, "Kinder <Leni & Tom>")
    _umbenennen(kontext, S.HOBBYS, "<b>Hobbys</b>")
    _anlegen(kontext, S.FAMILIE, KW47, 0, 60)
    seite = _dashboard(qtbot, kontext, zustand)
    texte = _texte(seite.inhalt)
    assert any("Kinder <Leni & Tom>" in t for t in texte)
    assert any("<b>Hobbys</b>" in t for t in texte)


def test_b1_hinweistext_als_klartext(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.dashboard import HinweisZeile

    _anlegen(kontext, S.FAMILIE, KW47, 0, 60)
    seite = _dashboard(qtbot, kontext, zustand)
    hinweis = replace(kontext.auswertung.hinweise(KW47)[0], text="<b>Hobbys</b> & mehr")
    zeile = HinweisZeile(hinweis, seite)
    qtbot.addWidget(zeile)
    assert "<b>Hobbys</b> & mehr" in _texte(zeile)


def test_b1_begruendung_als_klartext(qtbot, kontext, zustand):
    from balanceos.praesentation.dialoge.begruendung import BegruendungDialog

    _anlegen(kontext, S.FAMILIE, KW47, 0, 60)
    hinweis = kontext.auswertung.hinweise(KW47)[0]
    hinweis = replace(
        hinweis,
        text="<b>Hobbys</b> zu kurz",
        begruendung=replace(hinweis.begruendung, datenbasis="Kinder <b>Leni</b>"),
    )
    d = BegruendungDialog(hinweis, kontext, zustand)
    qtbot.addWidget(d)
    texte = _texte(d)
    assert any(t.endswith("<b>Hobbys</b> zu kurz") for t in texte)
    assert "Kinder <b>Leni</b>" in texte


def test_b1_wunschprofil_und_loeschfrage_als_klartext(qtbot, kontext, zustand, fragen):
    from balanceos.praesentation.seiten.einstellungen import EinstellungenSeite

    _umbenennen(kontext, S.HOBBYS, "<b>Hobbys</b>")
    eigener = kontext.stammdaten.speichern(
        Lebensbereich("<i>Ehrenamt</i>", Bereichstyp.MINDESTZIEL, "#1C7ED6", 0)
    )
    seite = EinstellungenSeite(kontext, zustand)
    qtbot.addWidget(seite)
    seite.show()
    assert any("<b>Hobbys</b>" in t for t in _texte(seite.reiter.widget(1)))

    seite.bereich_tabelle.selectRow([b.id for b in seite._bereiche].index(eigener.id))
    fragen.antwort = QMessageBox.StandardButton.No
    seite.loeschen_knopf.click()
    frage = QLabel(fragen[0])
    assert sichtbar(frage) == "Lebensbereich „<i>Ehrenamt</i>“ wirklich löschen?"


# --- B2: Fenstergröße -------------------------------------------------------------------


@pytest.fixture
def fenster(qtbot, kontext, zustand):
    from balanceos.praesentation.hauptfenster import Hauptfenster

    kontext.daten.demodaten_laden()
    f = Hauptfenster(kontext, zustand)
    qtbot.addWidget(f)
    return f


def test_b2_fenster_passt_auf_1024_mal_600(qtbot, fenster):
    fenster.show()
    fenster.resize(1024, 600)
    QApplication.processEvents()
    assert fenster.size() == QSize(1024, 600)
    assert fenster.minimumWidth() <= 1000 and fenster.minimumHeight() <= 560


def test_b2_inhalt_bleibt_per_scrollbereich_erreichbar(qtbot, fenster):
    fenster.show()
    fenster.resize(1024, 600)
    bereich = fenster.inhalt_bereich
    for index, seite in enumerate(fenster.seiten):
        fenster.zeige_seite(index)
        QApplication.processEvents()
        mindest = seite.minimumSizeHint()
        assert seite.width() >= mindest.width(), seite.titel
        assert seite.height() >= mindest.height(), seite.titel
        breite = bereich.viewport().width() + bereich.horizontalScrollBar().maximum()
        hoehe = bereich.viewport().height() + bereich.verticalScrollBar().maximum()
        assert breite >= fenster.stapel.width() and hoehe >= fenster.stapel.height(), seite.titel


def test_b2_startgroesse_passt_auf_den_bildschirm(fenster):
    verfuegbar = fenster.screen().availableGeometry()
    assert fenster.width() <= max(verfuegbar.width(), fenster.minimumWidth())
    assert fenster.height() <= max(verfuegbar.height(), fenster.minimumHeight())


# --- B3: Datenbankfehler im Betrieb werden gemeldet ---------------------------------------


@pytest.fixture
def kritisch(monkeypatch):
    gesammelt = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda _p, titel, text, *a, **k: gesammelt.append((titel, text))
    )
    return gesammelt


def test_b3_datenbankfehler_zeigt_deutsche_meldung(qtbot, kritisch, tmp_path, monkeypatch):
    from balanceos.praesentation import app

    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    logdatei = tmp_path / "fehler.log"
    app.fehlerbehandlung_installieren(logdatei)
    fehler = sqlite3.OperationalError("database is locked")
    sys.excepthook(type(fehler), fehler, None)
    assert len(kritisch) == 1
    titel, text = kritisch[0]
    assert titel == "BalanceOS"
    assert text.startswith("Die Daten konnten nicht gespeichert werden.")
    assert "database is locked" in text
    assert "database is locked" in logdatei.read_text(encoding="utf-8")


def test_b3_fehler_in_slot_wird_gemeldet(qtbot, kritisch, tmp_path, monkeypatch):
    from balanceos.praesentation import app

    class Sender(QObject):
        ausloesen = Signal()

    def schreiben():
        raise sqlite3.OperationalError("database or disk is full")

    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    app.fehlerbehandlung_installieren(tmp_path / "fehler.log")
    sender = Sender()
    sender.ausloesen.connect(schreiben)
    sender.ausloesen.emit()
    assert len(kritisch) == 1 and "database or disk is full" in kritisch[0][1]


def test_b3_sonstiger_fehler_allgemeine_meldung(qtbot, kritisch, tmp_path, monkeypatch):
    from balanceos.praesentation import app

    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    app.fehlerbehandlung_installieren(tmp_path / "fehler.log")
    fehler = ValueError("kaputt")
    sys.excepthook(type(fehler), fehler, None)
    assert kritisch[0][1].startswith("Ein unerwarteter Fehler ist aufgetreten.")
    assert "kaputt" in kritisch[0][1]


# --- B4, B5: Abweichung und „zu wenig Daten“ im Dashboard ---------------------------------


def _bewertbare_woche(kontext) -> int:
    for tag in range(4):
        _anlegen(kontext, S.VERPFLICHTUNGEN, KW47, tag, 60)
    return _anlegen(kontext, S.BEWEGUNG, KW47, 0, 90)


def test_b4_dashboard_zeigt_abweichung_ist_minus_soll(qtbot, kontext, zustand):
    bewegung = _bewertbare_woche(kontext)  # Ist 1,5 h, Soll 3 h
    for tag in range(4):
        arbeit = _anlegen(kontext, S.ARBEIT, KW47, tag, 690)  # Ist 46 h, Soll 40 h
    familie = _id(kontext, S.FAMILIE)
    kontext.stammdaten.speichern(replace(kontext.stammdaten.bereich(familie), soll_stunden=0))
    _anlegen(kontext, S.FAMILIE, KW47, 1, 60)
    seite = _dashboard(qtbot, kontext, zustand)
    assert seite.abweichung_labels[bewegung].text() == "−1,5 h"
    assert seite.abweichung_labels[arbeit].text() == "+6 h"
    assert seite.abweichung_labels[familie].text() == "–"
    kopf = [sichtbar(seite._raster.itemAtPosition(0, s).widget()) for s in range(6)]
    assert "Ist − Soll" in kopf


def test_b5_zu_wenig_daten_sichtbar_in_score_spalte(qtbot, kontext, zustand):
    bid = _anlegen(kontext, S.BEWEGUNG, KW47, 0, 60)
    seite = _dashboard(qtbot, kontext, zustand)
    assert seite.score_labels[bid].text() == "zu wenig Daten"
    seite.resize(1000, 700)
    seite.grab()
    label = seite.score_labels[bid]
    assert label.width() >= label.sizeHint().width()


# --- C2: einheitliche Stundenrundung ----------------------------------------------------


def test_c2_balken_rundet_kaufmaennisch(qtbot):
    from balanceos.praesentation.widgets.soll_ist_balken import SollIstBalken

    b = SollIstBalken()
    qtbot.addWidget(b)
    b.setze(Bereichsbewertung(1, 1.25, 3, 0.4, None, 42, -1.75), Bereichstyp.MINDESTZIEL, "#000")
    assert b.text() == "1,3 / 3 h"


# --- C3: Einzahl im WHO-5-Dialog --------------------------------------------------------


def test_c3_who5_noch_offen_einzahl_und_mehrzahl(qtbot, kontext, zustand):
    from balanceos.praesentation.dialoge.who5 import Who5Dialog

    d = Who5Dialog(kontext, zustand)
    qtbot.addWidget(d)
    assert d.offen_label.text() == "Noch offen: 5 Aussagen."
    for zeile in d.optionen[:4]:
        zeile[2].setChecked(True)
    assert d.offen_label.text() == "Noch offen: 1 Aussage."


# --- C4: abgelehnter Wert im Wunschprofil ----------------------------------------------


def test_c4_wunschprofil_verwirft_abgelehnten_wert_beim_wiederanzeigen(qtbot, kontext, zustand):
    from balanceos.praesentation.seiten.einstellungen import EinstellungenSeite

    seite = EinstellungenSeite(kontext, zustand)
    qtbot.addWidget(seite)
    seite.show()
    freizeit = _id(kontext, S.FREIZEIT)
    gespeichert = kontext.repos.bereiche.nach_id(freizeit).soll_stunden
    feld = seite.soll_felder[freizeit]
    feld.setValue(40)
    assert not seite.wunsch_fehler.isHidden()
    assert kontext.repos.bereiche.nach_id(freizeit).soll_stunden == gespeichert
    seite.hide()
    seite.show()
    assert feld.value() == gespeichert
    assert seite.wunsch_fehler.isHidden()
    assert feld.property("fehler") == "false"
