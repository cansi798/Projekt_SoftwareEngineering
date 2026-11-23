"""Tests der Demodaten der Persona Sarah Keller (US18, GP09, GR28)."""

from datetime import date

import pytest

from balanceos.anwendung.demodaten import erzeuge_demodaten
from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.kalender import KW
from balanceos.domaene.typen import Aktivitaetsstatus, Bewegungsart
from balanceos.domaene.typen import StandardSchluessel as S

SONNTAG = date(2026, 11, 22)


@pytest.fixture
def k22():
    kontext = AppKontext.erstellen(":memory:", heute=lambda: SONNTAG)
    yield kontext
    kontext.db.schliessen()


def _standard(kontext):
    return {s: kontext.repos.bereiche.nach_schluessel(s) for s in S}


def test_demodaten_deterministisch(k22):
    eins = erzeuge_demodaten(SONNTAG, _standard(k22))
    zwei = erzeuge_demodaten(SONNTAG, _standard(k22))
    assert eins == zwei and len(eins) > 200
    assert all(a.ist_demo for a in eins)


def test_demodaten_acht_wochen_bis_aktuelle_woche(k22):
    daten = erzeuge_demodaten(SONNTAG, _standard(k22))
    wochen = {KW.aus_datum(a.datum) for a in daten}
    assert wochen == {KW(2026, 47).verschoben(-i) for i in range(8)}
    aelteste = [a for a in daten if KW.aus_datum(a.datum) == KW(2026, 40)]
    assert len({a.datum for a in aelteste}) == 3


def test_demodaten_zukunft_nur_geplant():
    heute = date(2026, 11, 18)
    kontext = AppKontext.erstellen(":memory:", heute=lambda: heute)
    daten = erzeuge_demodaten(heute, _standard(kontext))
    zukunft = [a for a in daten if a.datum > heute]
    assert zukunft
    assert all(a.status is Aktivitaetsstatus.GEPLANT for a in zukunft)
    assert all(a.zufriedenheit is a.belastung is a.erholung is None for a in zukunft)
    assert all(a.status is not Aktivitaetsstatus.GEPLANT for a in daten if a.datum <= heute)


def test_demodaten_vorwoche_bewegung_65(k22):
    k22.daten.demodaten_laden()
    vorwoche = KW(2026, 46)
    bewegung = k22.repos.bereiche.nach_schluessel(S.BEWEGUNG).id
    eintraege = [a for a in k22.aktivitaeten.fuer_woche(vorwoche) if a.lebensbereich_id == bewegung]
    assert [(a.dauer_minuten, a.bewegungsart, a.zufriedenheit) for a in eintraege] == [
        (45, Bewegungsart.AUSDAUER_MODERAT, 4),
        (45, Bewegungsart.AUSDAUER_MODERAT, 5),
    ]
    assert k22.auswertung.wochenbewertung(vorwoche).bereich(bewegung).score == 65
    r01 = next(h for h in k22.auswertung.hinweise(vorwoche) if h.regel == "R01")
    assert "90 von 150" in r01.text


def test_demodaten_decken_alle_regeln_ab(k22):
    k22.daten.demodaten_laden()
    kennungen = set()
    for i in range(8):
        kennungen |= {h.regel for h in k22.auswertung.hinweise(KW(2026, 47).verschoben(-i))}
    assert kennungen == {f"R{n:02d}" for n in range(1, 11)}


def test_demodaten_nicht_doppelt_ladbar(k22):
    from balanceos.anwendung.fehler import RegelVerletzung

    anzahl = k22.daten.demodaten_laden()
    assert k22.daten.demodaten_vorhanden() and anzahl > 0
    with pytest.raises(RegelVerletzung):
        k22.daten.demodaten_laden()
    assert len(k22.repos.aktivitaeten.alle()) == anzahl


def test_demodaten_entfernen_laesst_eigene_daten(k22):
    from balanceos.domaene.modell import Aktivitaet

    bid = k22.repos.bereiche.nach_schluessel(S.HOBBYS).id
    eigene = k22.aktivitaeten.speichern(
        Aktivitaet("Malen", bid, date(2026, 11, 20), 60, Aktivitaetsstatus.DURCHGEFUEHRT)
    )
    anzahl = k22.daten.demodaten_laden()
    assert k22.daten.demodaten_entfernen() == anzahl
    assert [a.id for a in k22.repos.aktivitaeten.alle()] == [eigene.id]
    assert not k22.daten.demodaten_vorhanden()


def test_demodaten_aendern_wunschprofil_nicht(k22):
    vorher = (
        k22.stammdaten.alle_bereiche(),
        k22.stammdaten.einstellungen(),
        k22.auswertung.regeln(),
    )
    k22.daten.demodaten_laden()
    nachher = (
        k22.stammdaten.alle_bereiche(),
        k22.stammdaten.einstellungen(),
        k22.auswertung.regeln(),
    )
    assert vorher == nachher


def test_alle_loeschen_braucht_bestaetigung(k22):
    from balanceos.anwendung.fehler import ValidierungsFehler

    k22.daten.demodaten_laden()
    for falsch in ["", "löschen", "LÖSCHEN ", "LOESCHEN"]:
        with pytest.raises(ValidierungsFehler):
            k22.daten.alle_daten_loeschen(falsch)
    assert k22.repos.aktivitaeten.alle()


def test_nach_alle_loeschen_wie_erster_start(k22):
    from dataclasses import replace

    from balanceos.domaene.modell import Einstellungen
    from balanceos.persistenz.stammdaten import STANDARDBEREICHE

    k22.daten.demodaten_laden()
    hobbys = k22.repos.bereiche.nach_schluessel(S.HOBBYS)
    k22.stammdaten.speichern(replace(hobbys, name="Musik", soll_stunden=6))
    k22.stammdaten.einstellungen_speichern(Einstellungen(0.3, True))
    k22.auswertung.regel_setzen("R03", False)
    k22.daten.alle_daten_loeschen("LÖSCHEN")
    bereiche = k22.stammdaten.alle_bereiche()
    assert [(b.name, b.soll_stunden, b.aktiv) for b in bereiche] == [
        (b.name, b.soll_stunden, True) for b in STANDARDBEREICHE
    ]
    assert k22.stammdaten.einstellungen() == Einstellungen()
    assert all(r.aktiv for r in k22.auswertung.regeln())
    assert k22.repos.aktivitaeten.alle() == [] and k22.repos.serien.alle() == []
    assert not k22.auswertung.gibt_aktivitaeten()
