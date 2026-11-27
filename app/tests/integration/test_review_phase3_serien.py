"""Regressionstests zu Befunden des Phase-3-Reviews: Serien und Datenbank (GR18, GR19, GR29)."""

from dataclasses import replace
from datetime import date, time

import pytest

from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel, Wochentag

HEUTE = date(2026, 11, 22)  # Sonntag, KW 47/2026


@pytest.fixture
def kontext22():
    from balanceos.anwendung.kontext import AppKontext

    k = AppKontext.erstellen(":memory:", heute=lambda: HEUTE)
    yield k
    k.db.schliessen()


def _yoga_serie(kontext):
    bid = kontext.repos.bereiche.nach_schluessel(StandardSchluessel.BEWEGUNG).id
    vorlage = Aktivitaet(
        titel="Yoga",
        lebensbereich_id=bid,
        datum=date(2026, 11, 23),
        dauer_minuten=60,
        status=Aktivitaetsstatus.GEPLANT,
        beginn=time(18, 0),
        ende=time(19, 0),
    )
    return kontext.aktivitaeten.serie_anlegen(
        vorlage, frozenset({Wochentag.MO, Wochentag.MI}), date(2026, 12, 31)
    )


def _tage(kontext, serie):
    return [t.datum for t in kontext.repos.aktivitaeten.termine_der_serie(serie.id)]


def test_serie_aendern_mit_veralteter_serie_behaelt_ausnahme_des_verschobenen_termins(
    kontext22,
):
    """A1: Die vor dem Verschieben geladene Serie darf die neue Ausnahme nicht überschreiben."""
    serie = _yoga_serie(kontext22)
    veraltet = kontext22.aktivitaeten.serie(serie.id)  # wie beim Öffnen des Dialogs
    termin = next(
        t
        for t in kontext22.repos.aktivitaeten.termine_der_serie(serie.id)
        if t.datum == date(2026, 11, 30)
    )
    kontext22.aktivitaeten.speichern(replace(termin, datum=date(2026, 12, 1)))

    veraltet.titel = "Yoga am Abend"
    kontext22.aktivitaeten.serie_aendern(veraltet)

    tage = _tage(kontext22, serie)
    assert date(2026, 11, 30) not in tage
    assert tage.count(date(2026, 12, 1)) == 1
    assert date(2026, 11, 30) in kontext22.aktivitaeten.serie(serie.id).ausnahmen
    assert len(tage) == len(set(tage))


def test_serie_aendern_mit_veralteter_serie_behaelt_ausnahme_des_geloeschten_termins(
    kontext22,
):
    """A1: Auch ein zwischenzeitlich gelöschter Termin entsteht nicht neu (GR18)."""
    serie = _yoga_serie(kontext22)
    veraltet = kontext22.aktivitaeten.serie(serie.id)
    termin = next(
        t
        for t in kontext22.repos.aktivitaeten.termine_der_serie(serie.id)
        if t.datum == date(2026, 12, 2)
    )
    kontext22.aktivitaeten.loeschen(termin.id)

    kontext22.aktivitaeten.serie_aendern(veraltet)

    assert date(2026, 12, 2) not in _tage(kontext22, serie)
    assert date(2026, 12, 2) in kontext22.aktivitaeten.serie(serie.id).ausnahmen


# --- C9: „Alle Daten löschen“ hinterlässt keine Reste im Write-Ahead-Log --------------------


def test_alle_daten_loeschen_leert_write_ahead_log(tmp_path):
    from balanceos.anwendung.kontext import AppKontext

    pfad = tmp_path / "balanceos.db"
    k = AppKontext.erstellen(pfad, heute=lambda: HEUTE)
    try:
        bid = k.repos.bereiche.nach_schluessel(StandardSchluessel.BEWEGUNG).id
        k.aktivitaeten.speichern(
            Aktivitaet(
                "Joggen",
                bid,
                HEUTE,
                30,
                Aktivitaetsstatus.DURCHGEFUEHRT,
                notiz="GEHEIMNOTIZ-4711",
            )
        )
        k.daten.alle_daten_loeschen("LÖSCHEN")
        wal = tmp_path / "balanceos.db-wal"
        # Die Verbindung bleibt offen wie im laufenden Programm.
        assert not wal.exists() or wal.stat().st_size == 0
        assert b"GEHEIMNOTIZ-4711" not in pfad.read_bytes()
    finally:
        k.db.schliessen()


# --- C12: Verbindung wird geschlossen, wenn das Öffnen scheitert ----------------------------


def test_datenbank_schliesst_verbindung_bei_fehler_beim_oeffnen(tmp_path, monkeypatch):
    import sqlite3

    from balanceos.persistenz import datenbank

    pfad = tmp_path / "kaputt.db"
    pfad.write_bytes(b"Das ist keine SQLite-Datei" * 100)
    geoeffnet = []
    original = sqlite3.connect

    def merken(*a, **k):
        con = original(*a, **k)
        geoeffnet.append(con)
        return con

    monkeypatch.setattr(datenbank.sqlite3, "connect", merken)
    with pytest.raises(sqlite3.DatabaseError):
        datenbank.Datenbank(pfad)
    assert len(geoeffnet) == 1
    with pytest.raises(sqlite3.ProgrammingError):  # geschlossene Verbindung
        geoeffnet[0].execute("SELECT 1")
    pfad.unlink()  # unter Windows nur ohne offene Dateihandles möglich
