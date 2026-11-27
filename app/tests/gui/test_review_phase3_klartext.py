"""Regressionstests: Titel mit spitzen Klammern erscheinen in Rückfragen und Tooltips wörtlich."""

from datetime import date, time

import pytest
from PySide6.QtWidgets import QMessageBox

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel

pytestmark = pytest.mark.gui
HEUTE = date(2026, 11, 22)
TITEL = "<b>Yoga</b> & Co"


@pytest.fixture
def kontext22():
    from balanceos.anwendung.kontext import AppKontext

    k = AppKontext.erstellen(":memory:", heute=lambda: HEUTE)
    yield k
    k.db.schliessen()


@pytest.fixture
def aktivitaet(kontext22):
    """Eine geplante Aktivität mit HTML-ähnlichem Titel am 20.11.2026."""
    bid = kontext22.repos.bereiche.nach_schluessel(StandardSchluessel.BEWEGUNG).id
    return kontext22.aktivitaeten.speichern(
        Aktivitaet(
            titel=TITEL,
            lebensbereich_id=bid,
            datum=date(2026, 11, 20),
            dauer_minuten=60,
            status=Aktivitaetsstatus.GEPLANT,
            beginn=time(18, 0),
            ende=time(19, 0),
        )
    )


def _fragen_mitschneiden(monkeypatch):
    fragen = []

    def ersatz(_parent, _titel, text, *_, **__):
        fragen.append(text)
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "question", ersatz)
    return fragen


def test_als_html_maskiert_zeichen_und_erhaelt_zeilenumbrueche():
    from balanceos.praesentation.texte import als_html

    assert als_html("a <b>&\nc") == "<p>a &lt;b&gt;&amp;<br>c</p>"


def test_loeschfrage_der_seite_zeigt_titel_woertlich(qtbot, kontext22, aktivitaet, monkeypatch):
    from balanceos.praesentation.seiten.aktivitaeten import AktivitaetenSeite
    from balanceos.praesentation.zustand import Zustand

    seite = AktivitaetenSeite(kontext22, Zustand(KW.heute(HEUTE)))
    qtbot.addWidget(seite)
    seite.aktualisieren()
    seite.tabelle.selectRow(0)
    fragen = _fragen_mitschneiden(monkeypatch)
    seite.loeschen_knopf.click()
    assert len(fragen) == 1
    assert "&lt;b&gt;Yoga&lt;/b&gt; &amp; Co" in fragen[0]
    assert "<b>" not in fragen[0]


def test_loeschfrage_des_dialogs_zeigt_titel_woertlich(qtbot, kontext22, aktivitaet, monkeypatch):
    from balanceos.praesentation.dialoge.aktivitaet import AktivitaetDialog
    from balanceos.praesentation.zustand import Zustand

    d = AktivitaetDialog(kontext22, Zustand(KW.heute(HEUTE)), aktivitaet)
    qtbot.addWidget(d)
    fragen = _fragen_mitschneiden(monkeypatch)
    d._loeschen()
    assert len(fragen) == 1
    assert "&lt;b&gt;Yoga&lt;/b&gt;" in fragen[0]
    assert "<b>" not in fragen[0]


def test_kalender_tooltip_zeigt_titel_woertlich(qtbot, aktivitaet):
    from balanceos.praesentation.widgets.wochenkalender import Wochenkalender

    k = Wochenkalender()
    qtbot.addWidget(k)
    text = k._tooltip(aktivitaet)
    assert "&lt;b&gt;Yoga&lt;/b&gt; &amp; Co" in text
    assert "<b>" not in text and "<br>" in text
