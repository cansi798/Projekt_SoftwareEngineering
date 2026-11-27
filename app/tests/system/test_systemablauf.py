"""Systemtests: Ende-zu-Ende-Abläufe über die echte Oberfläche (offscreen).

Jeder Test startet auf einer frischen Datenbankdatei und bedient das
Hauptfenster wie ein Mensch: Seiten in der Seitenleiste anklicken, Knöpfe
drücken, Felder per Tastatur füllen. Modale Dialoge laufen nicht in einer
eigenen Ereignisschleife; ``QDialog.exec`` wird durch einen „Bediener“ ersetzt,
der den Dialog anzeigt, ihn mit einer vorbereiteten Aktion bedient und das
Ergebnis zurückgibt. Meldungsfenster und Dateidialoge werden wie in den
übrigen Oberflächentests ersetzt.
"""

import csv
import json
import os
import socket
import sqlite3
import subprocess
import sys
import time
from collections import deque
from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QPoint, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTextEdit,
    QWidget,
)

from balanceos.domaene.kalender import KW
from balanceos.domaene.typen import StandardSchluessel
from balanceos.domaene.validierung import LOESCHWORT, M_DAUER, M_TITEL

pytestmark = [pytest.mark.system, pytest.mark.gui]

HEUTE = date(2026, 11, 18)
"""Festes Tagesdatum (Mittwoch, KW 47/2026), wie in ``tests/conftest.py``."""

APP_ORDNER = Path(__file__).resolve().parents[2]
QUELLEN = APP_ORDNER / "src"

SEITENTITEL = [
    "Dashboard",
    "Woche",
    "Aktivitäten",
    "Statistik",
    "Reflexion",
    "Kompass",
    "Einstellungen",
]
ENGLISCHE_STANDARDTEXTE = {
    "ok",
    "cancel",
    "save",
    "open",
    "yes",
    "no",
    "close",
    "apply",
    "reset",
    "help",
    "discard",
    "abort",
    "retry",
    "ignore",
}
EINGABEFELDER = (QLineEdit, QAbstractSpinBox, QComboBox, QTextEdit, QPlainTextEdit)
"""Eingabefelder für NFA01; ``QAbstractSpinBox`` umfasst Spin-, Datums- und Zeitfelder."""

TABELLEN_NUTZDATEN = (
    "aktivitaet",
    "wiederholungsserie",
    "ausnahme",
    "who5_erhebung",
    "wochenreflexion",
    "hinweis_ausblendung",
)


# --- Hilfsmittel -----------------------------------------------------------------------------


class Bediener:
    """Ersetzt modale Ereignisschleifen durch vorbereitete Bedienschritte.

    Für jeden erwarteten Dialog wird mit ``erwarte`` eine Aktion hinterlegt. Öffnet
    die Anwendung einen Dialog mit ``exec()``, zeigt der Bediener ihn an, führt die
    nächste Aktion aus und schließt ihn mit „Abbrechen“, falls die Aktion ihn offen
    gelassen hat. Ein unerwarteter Dialog führt zu einem Testfehler statt zu einem
    Hänger.
    """

    def __init__(self) -> None:
        self.aktionen: deque[Callable[[QDialog], None]] = deque()
        self.dialoge: list[QDialog] = []
        self.meldungen: list[tuple[str, str, str]] = []
        self.speicherorte: deque[Path] = deque()

    def erwarte(self, aktion: Callable[[QDialog], None]) -> None:
        self.aktionen.append(aktion)

    def exec(self, dialog: QDialog) -> int:
        assert self.aktionen, f"Unerwarteter modaler Dialog: {dialog.windowTitle()}"
        aktion = self.aktionen.popleft()
        self.dialoge.append(dialog)
        dialog.show()
        QApplication.processEvents()
        try:
            aktion(dialog)
        finally:
            if dialog.isVisible():
                dialog.reject()
        return dialog.result()

    def meldung(self, art: str) -> Callable[..., QMessageBox.StandardButton]:
        def ersatz(_parent, titel, text, *_, **__):
            self.meldungen.append((art, titel, text))
            return (
                QMessageBox.StandardButton.No
                if art == "question"
                else QMessageBox.StandardButton.Ok
            )

        return ersatz

    def speichern_unter(self, _parent, _titel, vorschlag, filter_, *_, **__):
        assert self.speicherorte, f"Unerwarteter Dateidialog für {vorschlag}"
        return str(self.speicherorte.popleft()), filter_


@pytest.fixture
def bediener(monkeypatch) -> Bediener:
    b = Bediener()
    monkeypatch.setattr(QDialog, "exec", lambda self: b.exec(self))
    for art in ("information", "warning", "critical", "question"):
        monkeypatch.setattr(QMessageBox, art, b.meldung(art))
    monkeypatch.setattr(QFileDialog, "getSaveFileName", b.speichern_unter)
    return b


@pytest.fixture
def db_pfad(tmp_path) -> Path:
    pfad = tmp_path / "balanceos.db"
    assert not pfad.exists()
    return pfad


@pytest.fixture
def kontext_datei(db_pfad):
    """Frische Datei-Datenbank, wie beim ersten Start der Anwendung."""
    from balanceos.anwendung.kontext import AppKontext

    k = AppKontext.erstellen(db_pfad, heute=lambda: HEUTE)
    yield k
    k.db.schliessen()


@pytest.fixture
def fenster(qtbot, kontext_datei, bediener):
    from balanceos.praesentation.hauptfenster import Hauptfenster
    from balanceos.praesentation.stil import STYLESHEET
    from balanceos.praesentation.zustand import Zustand

    QApplication.instance().setStyleSheet(STYLESHEET)
    f = Hauptfenster(kontext_datei, Zustand(KW.heute(HEUTE)))
    qtbot.addWidget(f)
    f.resize(1280, 800)
    f.show()
    qtbot.waitExposed(f)
    yield f
    QApplication.instance().setStyleSheet("")


def ereignisse() -> None:
    """Arbeitet anstehende Ereignisse ab, z. B. das verzögerte Anzeigen neuer Widgets."""
    QApplication.processEvents()


def klicken(qtbot, knopf: QWidget) -> None:
    """Klickt mit der linken Maustaste in die Mitte des Widgets."""
    assert knopf.isVisible(), f"Knopf nicht sichtbar: {getattr(knopf, 'text', lambda: '')()}"
    if isinstance(knopf, QCheckBox | QRadioButton):
        # Nur Kästchen und Beschriftung sind anklickbar, nicht die ganze Zeilenbreite.
        punkt = QPoint(min(8, knopf.width() // 2), knopf.height() // 2)
        qtbot.mouseClick(knopf, Qt.MouseButton.LeftButton, pos=punkt)
    else:
        qtbot.mouseClick(knopf, Qt.MouseButton.LeftButton)
    ereignisse()


def zeichen_eingeben(qtbot, ziel: QWidget, text: str) -> None:
    """Tippt ``text`` Zeichen für Zeichen.

    ``QTest.keyClicks`` bricht in Qt 6.12 bei Zeichen ohne eigene Qt-Taste (z. B. „ü“,
    „„“) den Prozess ab. Solche Zeichen gehen deshalb als Tastendruck mit Text an das
    Feld, so wie ihn eine Tastatur mit deutschem Layout erzeugt.
    """
    for zeichen in text:
        if zeichen.isascii():
            qtbot.keyClicks(ziel, zeichen)
            continue
        for art in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            ereignis = QKeyEvent(art, Qt.Key.Key_unknown, Qt.KeyboardModifier.NoModifier, zeichen)
            QApplication.sendEvent(ziel, ereignis)
    ereignisse()


def tippen(qtbot, feld: QWidget, text: str) -> None:
    """Ersetzt den Inhalt eines Eingabefelds durch Tastatureingabe."""
    ziel = feld.lineEdit() if isinstance(feld, QAbstractSpinBox) else feld
    ziel.setFocus()
    qtbot.keyClick(ziel, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    qtbot.keyClick(ziel, Qt.Key.Key_Delete)
    zeichen_eingeben(qtbot, ziel, text)


def seite_waehlen(qtbot, fenster, index: int) -> QWidget:
    """Klickt den Eintrag ``index`` der Seitenleiste an und liefert die Seite."""
    leiste = fenster.seitenleiste
    rechteck = leiste.visualItemRect(leiste.item(index))
    qtbot.mouseClick(leiste.viewport(), Qt.MouseButton.LeftButton, pos=rechteck.center())
    ereignisse()
    assert fenster.stapel.currentIndex() == index
    assert fenster.titel_label.text() == SEITENTITEL[index]
    seite = fenster.stapel.currentWidget()
    assert seite.isVisible()
    return seite


def knopf_mit_text(wurzel: QWidget, text: str) -> QPushButton:
    """Sucht den sichtbaren Knopf mit genau diesem Text."""
    treffer = [k for k in wurzel.findChildren(QPushButton) if k.text() == text and k.isVisible()]
    assert len(treffer) == 1, f"Knopf „{text}“ {len(treffer)}-mal gefunden"
    return treffer[0]


def bereich_id(kontext, schluessel: StandardSchluessel) -> int:
    return kontext.repos.bereiche.nach_schluessel(schluessel).id


def bereich_waehlen(qtbot, dialog, name: str) -> None:
    """Wählt den Lebensbereich per Tastatur in der Auswahlliste."""
    feld = dialog.bereich_feld
    index = feld.findText(name)
    assert index >= 0
    feld.setFocus()
    while feld.currentIndex() != index:
        taste = Qt.Key.Key_Down if feld.currentIndex() < index else Qt.Key.Key_Up
        qtbot.keyClick(feld, taste)


def aktivitaet_eingeben(qtbot, dialog, titel: str, bereich: str, minuten: int) -> None:
    """Füllt den Erfassungsdialog gültig aus (Modus „Dauer“, Zufriedenheit 4)."""
    tippen(qtbot, dialog.titel_feld, titel)
    bereich_waehlen(qtbot, dialog, bereich)
    klicken(qtbot, dialog.modus_dauer)
    tippen(qtbot, dialog.dauer_feld, str(minuten))
    klicken(qtbot, knopf_mit_text(dialog.skalen["zufriedenheit"], "4"))


def speichern_und_pruefen(qtbot, dialog) -> None:
    assert dialog.speichern_knopf.isEnabled(), dialog.speichern_knopf.toolTip()
    with qtbot.waitSignal(dialog._zustand.daten_geaendert, timeout=2000):
        klicken(qtbot, dialog.speichern_knopf)
    assert dialog.result() == QDialog.DialogCode.Accepted


def neue_aktivitaet_ueber_kopfzeile(qtbot, fenster, bediener, titel, bereich, minuten) -> None:
    """Öffnet „+ Aktivität“ in der Kopfzeile, füllt den Dialog aus und speichert."""
    from balanceos.praesentation.dialoge.aktivitaet import AktivitaetDialog

    def ausfuellen(dialog):
        assert isinstance(dialog, AktivitaetDialog)
        aktivitaet_eingeben(qtbot, dialog, titel, bereich, minuten)
        speichern_und_pruefen(qtbot, dialog)

    bediener.erwarte(ausfuellen)
    klicken(qtbot, fenster.neu_knopf)
    assert not bediener.aktionen


def demodaten_ueber_dashboard(qtbot, fenster, bediener) -> None:
    """Lädt die Demodaten mit dem Knopf im Startzustand des Dashboards."""
    dashboard = seite_waehlen(qtbot, fenster, 0)
    assert dashboard.stapel.currentWidget() is dashboard.leer_ansicht
    klicken(qtbot, dashboard.demodaten_knopf)
    assert bediener.meldungen[-1][0] == "information"
    assert bediener.meldungen[-1][2].startswith("Demodaten geladen.")


def daten_reiter(qtbot, fenster):
    """Öffnet Einstellungen → Daten und liefert die Seite."""
    seite = seite_waehlen(qtbot, fenster, 6)
    leiste = seite.reiter.tabBar()
    index = [seite.reiter.tabText(i) for i in range(seite.reiter.count())].index("Daten")
    qtbot.mouseClick(leiste, Qt.MouseButton.LeftButton, pos=leiste.tabRect(index).center())
    ereignisse()
    assert seite.reiter.currentIndex() == index
    return seite


def exportieren(qtbot, fenster, bediener, ziel: Path, art: str) -> None:
    """Exportiert über Einstellungen → Daten → „Exportieren …“ nach ``ziel``."""
    seite = daten_reiter(qtbot, fenster)

    def bedienen(dialog):
        option = dialog.csv_option if art == "csv" else dialog.json_option
        klicken(qtbot, option)
        assert option.isChecked()
        bediener.speicherorte.append(ziel)
        klicken(qtbot, dialog.exportieren_knopf)

    bediener.erwarte(bedienen)
    klicken(qtbot, knopf_mit_text(seite, "Exportieren …"))
    assert not bediener.aktionen and not bediener.speicherorte
    art_, _, text = bediener.meldungen[-1]
    assert art_ == "information" and ziel.name in text
    assert ziel.exists()


def zaehle(db_pfad: Path, tabelle: str) -> int:
    """Zählt Zeilen über eine eigene Verbindung, also so, wie sie auf der Platte stehen."""
    con = sqlite3.connect(db_pfad)
    try:
        return con.execute(f"SELECT COUNT(*) FROM {tabelle}").fetchone()[0]  # noqa: S608
    finally:
        con.close()


def unterprozess(skript: str, *argumente: str, timeout: float = 60) -> subprocess.CompletedProcess:
    """Startet einen frischen Python-Prozess mit ``PYTHONPATH=src`` und Qt offscreen."""
    umgebung = os.environ.copy()
    umgebung["PYTHONPATH"] = str(QUELLEN)
    umgebung["QT_QPA_PLATFORM"] = "offscreen"
    return subprocess.run(
        [sys.executable, "-c", skript, *argumente],
        cwd=APP_ORDNER,
        env=umgebung,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


# --- NFA01: Beschriftung ---------------------------------------------------------------------


def _hat_beschriftung(feld: QWidget, wurzel: QWidget) -> bool:
    if feld.accessibleName().strip():
        return True
    if hasattr(feld, "placeholderText") and feld.placeholderText().strip():
        return True
    for label in wurzel.findChildren(QLabel):
        if label.buddy() is feld and label.text().strip():
            return True
    formulare = wurzel.findChildren(QFormLayout)
    if wurzel.layout() is not None and isinstance(wurzel.layout(), QFormLayout):
        formulare.append(wurzel.layout())
    w = feld
    while w is not None and w is not wurzel:
        for formular in formulare:
            label = formular.labelForField(w)
            if isinstance(label, QLabel) and label.text().strip():
                return True
        w = w.parentWidget()
    return False


def _ist_internes_feld(feld: QWidget) -> bool:
    """Eingebettete Zeilen von Spin- und Auswahlfeldern zählen nicht als eigenes Feld."""
    return isinstance(feld, QLineEdit) and isinstance(
        feld.parentWidget(), QAbstractSpinBox | QComboBox
    )


def pruefe_beschriftungen(wurzel: QWidget, ort: str) -> list[str]:
    """Liefert alle Verstöße gegen NFA01 unter ``wurzel`` als lesbare Texte."""
    probleme = []
    for knopf in wurzel.findChildren(QPushButton):
        if not knopf.isVisible():
            continue
        text = knopf.text().replace("&", "").strip()
        if not text and not knopf.toolTip().strip():
            probleme.append(f"{ort}: Knopf ohne Text und Tooltip ({knopf.objectName()!r})")
        if text.lower() in ENGLISCHE_STANDARDTEXTE:
            probleme.append(f"{ort}: englischer Standardtext „{text}“")
    for feld in wurzel.findChildren(QWidget):
        if not isinstance(feld, EINGABEFELDER) or not feld.isVisible():
            continue
        if _ist_internes_feld(feld):
            continue
        if not _hat_beschriftung(feld, wurzel):
            probleme.append(f"{ort}: {type(feld).__name__} ohne Beschriftung")
    return probleme


def _alle_seiten_pruefen(qtbot, fenster) -> list[str]:
    probleme = []
    for index, titel in enumerate(SEITENTITEL):
        seite = seite_waehlen(qtbot, fenster, index)
        if titel == "Einstellungen":
            leiste = seite.reiter.tabBar()
            for reiter in range(seite.reiter.count()):
                qtbot.mouseClick(
                    leiste, Qt.MouseButton.LeftButton, pos=leiste.tabRect(reiter).center()
                )
                ereignisse()
                assert seite.reiter.currentIndex() == reiter
                probleme += pruefe_beschriftungen(
                    fenster, f"{titel}/{seite.reiter.tabText(reiter)}"
                )
        else:
            probleme += pruefe_beschriftungen(fenster, titel)
    return probleme


# --- Systemtests -----------------------------------------------------------------------------


def test_ts01_erster_start_mit_demodaten(qtbot, fenster, bediener, kontext_datei, db_pfad):
    """TS01: Erster Start mit leerer Datenbank, Demodaten über das Dashboard laden (US18)."""
    from balanceos.praesentation.widgets.soll_ist_balken import SollIstBalken

    assert db_pfad.exists()
    assert zaehle(db_pfad, "aktivitaet") == 0
    dashboard = seite_waehlen(qtbot, fenster, 0)
    assert dashboard.stapel.currentWidget() is dashboard.leer_ansicht
    assert dashboard.demodaten_knopf.isVisible()
    assert dashboard.erste_aktivitaet_knopf.isVisible()
    assert "Willkommen bei BalanceOS" in [lbl.text() for lbl in dashboard.findChildren(QLabel)]

    demodaten_ueber_dashboard(qtbot, fenster, bediener)

    assert zaehle(db_pfad, "aktivitaet") > 0
    assert kontext_datei.daten.demodaten_vorhanden()
    assert dashboard.stapel.currentWidget() is dashboard.inhalt
    assert fenster.zustand.kw == KW(2026, 46)
    balken = [b for b in dashboard.findChildren(SollIstBalken) if b.isVisible()]
    assert len(balken) >= 1
    assert len(dashboard.hinweis_zeilen) >= 1
    assert all(z.isVisible() for z in dashboard.hinweis_zeilen)
    assert dashboard.vollstaendigkeit_label.text() == "7/7"

    woche = seite_waehlen(qtbot, fenster, 1)
    assert len(woche.kalender.bloecke()) > 0
    assert not woche.summe_label.text().startswith("0 Aktivitäten")


def test_ts02_aktivitaet_erfassen_und_auswerten(qtbot, fenster, bediener, kontext_datei, db_pfad):
    """TS02: Aktivität über „+ Aktivität“ erfassen; Liste, Woche und Dashboard zeigen sie (US05)."""
    dashboard = seite_waehlen(qtbot, fenster, 0)
    assert dashboard.stapel.currentWidget() is dashboard.leer_ansicht

    neue_aktivitaet_ueber_kopfzeile(qtbot, fenster, bediener, "Joggen im Park", "Bewegung", 45)

    # Datenbank: genau eine Aktivität, auf der Platte geschrieben.
    assert zaehle(db_pfad, "aktivitaet") == 1
    (a,) = kontext_datei.repos.aktivitaeten.alle()
    assert (a.titel, a.datum, a.dauer_minuten, a.zufriedenheit) == ("Joggen im Park", HEUTE, 45, 4)
    assert a.lebensbereich_id == bereich_id(kontext_datei, StandardSchluessel.BEWEGUNG)

    # Dashboard hat sich ohne Neustart aktualisiert.
    assert dashboard.stapel.currentWidget() is dashboard.inhalt
    assert dashboard.vollstaendigkeit_label.text() == "1/7"

    # Seite „Aktivitäten“ zeigt die neue Zeile.
    liste = seite_waehlen(qtbot, fenster, 2)
    assert liste.tabelle.rowCount() == 1
    assert liste.tabelle.item(0, 3).text() == "Joggen im Park"
    assert liste.tabelle.item(0, 2).text() == "Bewegung"
    assert liste.tabelle.item(0, 4).text().startswith("45 min")
    assert liste.anzahl_label.text() == "1 von 1 Aktivitäten"

    # Wochenansicht zeigt einen Block für die Aktivität.
    woche = seite_waehlen(qtbot, fenster, 1)
    assert [i for i, _ in woche.kalender.bloecke()] == [a.id]
    assert woche.summe_label.text().startswith("1 Aktivität ·")


def test_ts03_ungueltige_eingabe_wird_abgewiesen(qtbot, fenster, bediener, db_pfad):
    """TS03 (NFA02): Leerer Titel und Dauer 1.441 min erscheinen am Feld, nichts gespeichert."""
    beobachtet = {}

    def falsch_ausfuellen(dialog):
        # 1. Titel leer lassen (Feld berühren), Dauer gültig.
        tippen(qtbot, dialog.titel_feld, "x")
        tippen(qtbot, dialog.titel_feld, "")
        qtbot.keyClick(dialog.titel_feld, Qt.Key.Key_Tab)
        assert dialog.fehlerlabels["titel"].isVisible()
        assert dialog.fehlerlabels["titel"].text() == M_TITEL
        assert dialog.titel_feld.property("fehler") == "true"
        assert not dialog.speichern_knopf.isEnabled()
        assert "Titel" in dialog.speichern_knopf.toolTip()
        qtbot.mouseClick(dialog.speichern_knopf, Qt.MouseButton.LeftButton)
        qtbot.keyClick(dialog, Qt.Key.Key_Return)
        assert dialog.isVisible()

        # 2. Titel gültig, Dauer außerhalb 1–1.440 min.
        tippen(qtbot, dialog.titel_feld, "Lesen")
        klicken(qtbot, dialog.modus_dauer)
        tippen(qtbot, dialog.dauer_feld, "1441")
        assert dialog.dauer_feld.value() == 1441
        assert not dialog.fehlerlabels["titel"].isVisible()
        assert dialog.fehlerlabels["dauer"].isVisible()
        assert dialog.fehlerlabels["dauer"].text() == M_DAUER
        assert dialog.dauer_feld.property("fehler") == "true"
        assert not dialog.speichern_knopf.isEnabled()
        qtbot.mouseClick(dialog.speichern_knopf, Qt.MouseButton.LeftButton)
        qtbot.keyClick(dialog, Qt.Key.Key_Return)
        assert dialog.isVisible()

        # 3. Dauer 0 min ist ebenfalls ungültig.
        tippen(qtbot, dialog.dauer_feld, "0")
        assert dialog.fehlerlabels["dauer"].text() == M_DAUER
        assert not dialog.speichern_knopf.isEnabled()
        beobachtet["geprueft"] = True

    vorher = zaehle(db_pfad, "aktivitaet")
    with qtbot.assertNotEmitted(fenster.zustand.daten_geaendert):
        bediener.erwarte(falsch_ausfuellen)
        klicken(qtbot, fenster.neu_knopf)
    assert beobachtet.get("geprueft")
    assert bediener.dialoge[-1].result() == QDialog.DialogCode.Rejected
    assert zaehle(db_pfad, "aktivitaet") == vorher == 0
    assert bediener.meldungen == []


def test_ts04_export_csv_und_json(qtbot, fenster, bediener, kontext_datei, tmp_path):
    """TS04 (NFA10): CSV- und JSON-Export über Einstellungen → Daten mit Umlauten prüfen."""
    demodaten_ueber_dashboard(qtbot, fenster, bediener)
    klicken(qtbot, fenster.heute_knopf)
    assert fenster.zustand.kw == KW(2026, 47)
    titel = "Rückenübung für Jörg; Größe „groß“"
    neue_aktivitaet_ueber_kopfzeile(qtbot, fenster, bediener, titel, "Bewegung", 30)

    csv_datei = tmp_path / "export.csv"
    exportieren(qtbot, fenster, bediener, csv_datei, "csv")
    roh = csv_datei.read_bytes()
    assert roh.startswith(b"\xef\xbb\xbf"), "CSV muss mit UTF-8-BOM beginnen"
    with csv_datei.open(encoding="utf-8-sig", newline="") as datei:
        zeilen = list(csv.reader(datei, delimiter=";"))
    assert zeilen[0][:3] == ["datum", "kalenderwoche", "lebensbereich"]
    assert len(zeilen) > 2
    for nr, zeile in enumerate(zeilen):
        assert len(zeile) == 16, f"Zeile {nr} hat {len(zeile)} Spalten"
    eigene = [z for z in zeilen if z[4] == titel]
    assert len(eigene) == 1
    assert eigene[0][0] == HEUTE.isoformat() and eigene[0][2] == "Bewegung"
    assert eigene[0][7] == "30"
    text = roh.decode("utf-8-sig")
    assert ";" in text.splitlines()[0] and "," not in text.splitlines()[0]
    assert "Rückenübung für Jörg" in text and "�" not in text

    json_datei = tmp_path / "export.json"
    exportieren(qtbot, fenster, bediener, json_datei, "json")
    daten = json.loads(json_datei.read_text(encoding="utf-8"))
    assert daten["version"] == 1
    assert titel in [a["titel"] for a in daten["aktivitaeten"]]
    assert len(daten["aktivitaeten"]) == len(kontext_datei.repos.aktivitaeten.alle())
    assert "Rückenübung" in json_datei.read_text(encoding="utf-8")


def test_ts05_alle_daten_loeschen(qtbot, fenster, bediener, kontext_datei, db_pfad):
    """TS05 (NFA05): „Alle Daten löschen“ mit Eingabe „LÖSCHEN“ entfernt alle Nutzdaten."""
    from PySide6.QtCore import QDate

    demodaten_ueber_dashboard(qtbot, fenster, bediener)

    # Wiederholungsserie über den Erfassungsdialog anlegen.
    def serie_anlegen(dialog):
        aktivitaet_eingeben(qtbot, dialog, "Yogakurs", "Bewegung", 60)
        klicken(qtbot, dialog.wiederholen_feld)
        klicken(qtbot, dialog.enddatum_aktiv)
        dialog.enddatum_feld.setDate(QDate(2026, 12, 9))
        speichern_und_pruefen(qtbot, dialog)

    bediener.erwarte(serie_anlegen)
    klicken(qtbot, fenster.neu_knopf)

    # Wochenreflexion und WHO-5 über die Seite „Reflexion“.
    reflexion = seite_waehlen(qtbot, fenster, 4)
    zeichen_eingeben(qtbot, reflexion.antwort_felder[0], "Viel Bewegung")
    klicken(qtbot, reflexion.speichern_knopf)

    def who5_ausfuellen(dialog):
        for zeile in dialog.optionen:
            klicken(qtbot, zeile[3])
        klicken(qtbot, dialog.auswerten_knopf)
        assert dialog.ergebnis_label.text().startswith("Rohwert 15 von 25")

    bediener.erwarte(who5_ausfuellen)
    klicken(qtbot, reflexion.who5_knopf)

    for tabelle in ("aktivitaet", "wiederholungsserie", "who5_erhebung", "wochenreflexion"):
        assert zaehle(db_pfad, tabelle) > 0, tabelle

    seite = daten_reiter(qtbot, fenster)

    def loeschen(dialog):
        assert not dialog.loeschen_knopf.isEnabled()
        zeichen_eingeben(qtbot, dialog.eingabe, "löschen")
        assert not dialog.loeschen_knopf.isEnabled()
        tippen(qtbot, dialog.eingabe, LOESCHWORT)
        assert dialog.loeschen_knopf.isEnabled()
        klicken(qtbot, dialog.loeschen_knopf)

    bediener.erwarte(loeschen)
    klicken(qtbot, knopf_mit_text(seite, "Alle Daten löschen …"))

    assert bediener.dialoge[-1].result() == QDialog.DialogCode.Accepted
    for tabelle in TABELLEN_NUTZDATEN:
        assert zaehle(db_pfad, tabelle) == 0, tabelle
    assert not kontext_datei.daten.demodaten_vorhanden()
    # Zustand wie beim ersten Start: Standardbereiche vorhanden, Dashboard im Startzustand.
    assert zaehle(db_pfad, "lebensbereich") > 0
    assert fenster.stapel.currentIndex() == 0
    dashboard = fenster.stapel.currentWidget()
    assert dashboard.stapel.currentWidget() is dashboard.leer_ansicht


def test_ts06_kein_netzwerkzugriff(qtbot, fenster, bediener, kontext_datei, tmp_path, monkeypatch):
    """TS06 (NFA05): Kompletter Ablauf ohne Netzwerkzugriff (Socket-Aufrufe schlagen Alarm)."""
    versuche = []

    def verboten(name):
        def ersatz(*args, **kwargs):
            versuche.append((name, args))
            raise AssertionError(f"Netzwerkzugriff über socket.{name}: {args!r}")

        return ersatz

    monkeypatch.setattr(socket.socket, "connect", verboten("socket.connect"))
    monkeypatch.setattr(socket.socket, "connect_ex", verboten("socket.connect_ex"))
    monkeypatch.setattr(socket, "create_connection", verboten("create_connection"))
    monkeypatch.setattr(socket, "getaddrinfo", verboten("getaddrinfo"))
    with pytest.raises(AssertionError):
        socket.create_connection(("example.org", 80))
    versuche.clear()

    demodaten_ueber_dashboard(qtbot, fenster, bediener)
    for index in range(len(SEITENTITEL)):
        seite = seite_waehlen(qtbot, fenster, index)
        if index == 6:
            leiste = seite.reiter.tabBar()
            for reiter in range(seite.reiter.count()):
                qtbot.mouseClick(
                    leiste, Qt.MouseButton.LeftButton, pos=leiste.tabRect(reiter).center()
                )
        QApplication.processEvents()
    neue_aktivitaet_ueber_kopfzeile(qtbot, fenster, bediener, "Spaziergang", "Bewegung", 40)
    exportieren(qtbot, fenster, bediener, tmp_path / "offline.csv", "csv")
    exportieren(qtbot, fenster, bediener, tmp_path / "offline.json", "json")

    assert versuche == []
    assert "Spaziergang" in [a.titel for a in kontext_datei.repos.aktivitaeten.alle()]


SKRIPT_ABSTURZ = """
import os
import sys
from datetime import date
from pathlib import Path

from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel

nr = int(sys.argv[2])
k = AppKontext.erstellen(Path(sys.argv[1]), heute=lambda: date(2026, 11, 18))
bereich = k.repos.bereiche.nach_schluessel(StandardSchluessel.ARBEIT).id
k.aktivitaeten.speichern(
    Aktivitaet(f"Absturztest {nr}", bereich, date(2026, 11, 18), 30,
               Aktivitaetsstatus.DURCHGEFUEHRT)
)
print("GESPEICHERT", flush=True)
os._exit(1)
"""


def test_ts07_zwangsbeenden_nach_speichern(db_pfad):
    """TS07 (NFA04): Zehn Zwangsbeendigungen direkt nach dem Speichern verlieren nichts."""
    from balanceos.anwendung.kontext import AppKontext

    for nr in range(10):
        ergebnis = unterprozess(SKRIPT_ABSTURZ, str(db_pfad), str(nr))
        assert ergebnis.returncode == 1, ergebnis.stderr
        assert "GESPEICHERT" in ergebnis.stdout, ergebnis.stderr

    k = AppKontext.erstellen(db_pfad, heute=lambda: HEUTE)
    try:
        titel = sorted(a.titel for a in k.repos.aktivitaeten.alle())
        pruefung = k.db.abfrage("PRAGMA integrity_check")[0][0]
    finally:
        k.db.schliessen()
    assert len(titel) == 10
    assert titel == sorted(f"Absturztest {nr}" for nr in range(10))
    assert pruefung == "ok"


SKRIPT_START = """
import sys
import time
from pathlib import Path

prozessstart = float(sys.argv[2])

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

app = QApplication([])
import balanceos.praesentation.app as start
from balanceos.praesentation.hauptfenster import Hauptfenster

start.standardpfad = lambda: Path(sys.argv[1])
messung = {}


def messen():
    app.processEvents()
    messung["sekunden"] = time.time() - prozessstart
    messung["sichtbar"] = any(
        isinstance(w, Hauptfenster) and w.isVisible() for w in app.topLevelWidgets()
    )
    app.quit()


QTimer.singleShot(0, messen)
rueckgabe = start.starte([])
print(f"STARTZEIT={messung['sekunden']:.3f}")
print(f"SICHTBAR={messung['sichtbar']}")
print(f"RUECKGABE={rueckgabe}")
"""


def test_ts08_startzeit(db_pfad):
    """TS08 (NFA03): Kaltstart bis zum sichtbaren Hauptfenster dauert höchstens 5,0 s."""
    prozessstart = time.time()
    ergebnis = unterprozess(SKRIPT_START, str(db_pfad), repr(prozessstart))
    assert ergebnis.returncode == 0, ergebnis.stderr
    werte = dict(z.split("=", 1) for z in ergebnis.stdout.split() if "=" in z)
    sekunden = float(werte["STARTZEIT"])
    print(f"\nTS08 Startzeit (Prozessstart bis Hauptfenster sichtbar): {sekunden:.2f} s")
    assert werte["SICHTBAR"] == "True"
    assert werte["RUECKGABE"] == "0"
    assert db_pfad.exists(), "Start muss die frische Datenbank anlegen"
    assert sekunden <= 5.0


def test_ts09_oberflaeche_deutsch_und_beschriftet(qtbot, fenster, bediener):
    """TS09 (NFA01): Alle Seiten und der Erfassungsdialog sind deutsch beschriftet."""
    from balanceos.praesentation.dialoge.aktivitaet import AktivitaetDialog

    # Alle Seiten im Startzustand (leere Datenbank) und mit Demodaten.
    probleme = _alle_seiten_pruefen(qtbot, fenster)
    demodaten_ueber_dashboard(qtbot, fenster, bediener)
    probleme += _alle_seiten_pruefen(qtbot, fenster)

    # Erfassungsdialog in allen Ausprägungen: Dauer, Uhrzeit, Bewegung, Wiederholung.
    def dialog_pruefen(dialog):
        assert isinstance(dialog, AktivitaetDialog)
        probleme.extend(pruefe_beschriftungen(dialog, "Erfassungsdialog"))
        bereich_waehlen(qtbot, dialog, "Bewegung")
        klicken(qtbot, dialog.modus_zeit)
        klicken(qtbot, dialog.wiederholen_feld)
        klicken(qtbot, dialog.enddatum_aktiv)
        probleme.extend(pruefe_beschriftungen(dialog, "Erfassungsdialog (erweitert)"))

    bediener.erwarte(dialog_pruefen)
    klicken(qtbot, fenster.neu_knopf)
    assert not probleme, "\n".join(probleme)

    # Der Erfassungsdialog ist von jeder Seite mit einem Klick erreichbar.
    for index in range(len(SEITENTITEL)):
        seite_waehlen(qtbot, fenster, index)
        assert fenster.neu_knopf.isEnabled()
        anzahl = len(bediener.dialoge)
        bediener.erwarte(lambda d: None)
        klicken(qtbot, fenster.neu_knopf)
        assert len(bediener.dialoge) == anzahl + 1
        assert isinstance(bediener.dialoge[-1], AktivitaetDialog)
        assert bediener.dialoge[-1].windowTitle() == "Aktivität erfassen"
