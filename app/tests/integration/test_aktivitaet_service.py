"""Integrationstests des Aktivitäten-Services mit Wiederholungsserien (US05–US08)."""

from dataclasses import replace
from datetime import date, time, timedelta

import pytest

from balanceos.anwendung.fehler import RegelVerletzung, ValidierungsFehler
from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet, Lebensbereich
from balanceos.domaene.typen import (
    Aktivitaetsstatus,
    Bereichstyp,
    Bewegungsart,
    StandardSchluessel,
    Wochentag,
)

HEUTE = date(2026, 11, 18)  # Mittwoch
G, D = Aktivitaetsstatus.GEPLANT, Aktivitaetsstatus.DURCHGEFUEHRT


def _bid(kontext, schluessel=StandardSchluessel.BEWEGUNG) -> int:
    return kontext.repos.bereiche.nach_schluessel(schluessel).id


def _akt(kontext, **k) -> Aktivitaet:
    basis = dict(
        titel="Joggen", lebensbereich_id=_bid(kontext), datum=HEUTE, dauer_minuten=45, status=D
    )
    basis.update(k)
    return Aktivitaet(**basis)


def test_vorbelegung_status_nach_datum(kontext):
    assert kontext.aktivitaeten.vorbelegung(HEUTE).status is D
    assert kontext.aktivitaeten.vorbelegung(HEUTE + timedelta(days=1)).status is G
    v = kontext.aktivitaeten.vorbelegung(HEUTE, time(7, 30))
    assert (v.beginn, v.dauer_minuten) == (time(7, 30), 60)


def test_speichern_berechnet_dauer_ueber_mitternacht(kontext):
    schlaf = _bid(kontext, StandardSchluessel.SCHLAF)
    a = kontext.aktivitaeten.speichern(
        _akt(
            kontext,
            titel="Schlaf",
            lebensbereich_id=schlaf,
            beginn=time(23, 0),
            ende=time(6, 30),
            dauer_minuten=1,
        )
    )
    assert kontext.repos.aktivitaeten.nach_id(a.id).dauer_minuten == 450


def test_statuswechsel_entfernt_bewertungen(kontext):
    a = kontext.aktivitaeten.speichern(_akt(kontext, zufriedenheit=4, belastung=2, erholung=5))
    kontext.aktivitaeten.speichern(replace(a, status=Aktivitaetsstatus.AUSGEFALLEN))
    gelesen = kontext.repos.aktivitaeten.nach_id(a.id)
    assert (gelesen.zufriedenheit, gelesen.belastung, gelesen.erholung) == (None, None, None)


def test_bewegungsart_ausserhalb_bewegung_wird_entfernt(kontext):
    a = kontext.aktivitaeten.speichern(
        _akt(
            kontext,
            lebensbereich_id=_bid(kontext, StandardSchluessel.ARBEIT),
            bewegungsart=Bewegungsart.KRAFT,
        )
    )
    assert kontext.repos.aktivitaeten.nach_id(a.id).bewegungsart is None


def test_durchgefuehrt_in_zukunft_abgewiesen(kontext):
    with pytest.raises(ValidierungsFehler) as info:
        kontext.aktivitaeten.speichern(_akt(kontext, datum=HEUTE + timedelta(days=1)))
    assert (
        info.value.meldung_fuer("status") == "Zukünftige Aktivitäten sind noch nicht durchgeführt."
    )
    assert kontext.repos.aktivitaeten.alle() == []


def test_neue_aktivitaet_nur_in_aktivem_bereich(kontext):
    hobbys = kontext.repos.bereiche.nach_schluessel(StandardSchluessel.HOBBYS)
    kontext.stammdaten.speichern(replace(hobbys, aktiv=False))
    with pytest.raises(ValidierungsFehler):
        kontext.aktivitaeten.speichern(_akt(kontext, lebensbereich_id=hobbys.id))


def test_fuer_woche_und_loeschen(kontext):
    a = kontext.aktivitaeten.speichern(_akt(kontext))
    kontext.aktivitaeten.speichern(_akt(kontext, datum=date(2026, 11, 9)))
    assert [x.id for x in kontext.aktivitaeten.fuer_woche(KW(2026, 47))] == [a.id]
    kontext.aktivitaeten.loeschen(a.id)
    assert kontext.aktivitaeten.fuer_woche(KW(2026, 47)) == []


def _serie_anlegen(kontext, **k):
    vorlage = _akt(
        kontext,
        datum=date(2026, 11, 17),
        beginn=time(18, 0),
        ende=time(18, 45),
        zufriedenheit=4,
        bewegungsart=Bewegungsart.AUSDAUER_MODERAT,
    )
    return kontext.aktivitaeten.serie_anlegen(
        vorlage, k.get("tage", frozenset({Wochentag.DI, Wochentag.DO})), k.get("ende")
    )


def test_serie_erzeugt_termine_bis_horizont(kontext):
    serie = _serie_anlegen(kontext)
    termine = kontext.repos.aktivitaeten.termine_der_serie(serie.id)
    assert termine[0].datum == date(2026, 11, 17)
    assert termine[0].status is D and termine[0].zufriedenheit == 4  # Vorlage übernommen
    assert all(t.status is G for t in termine[1:])
    assert all(t.bewegungsart is Bewegungsart.AUSDAUER_MODERAT for t in termine)
    assert max(t.datum for t in termine) <= HEUTE + timedelta(weeks=52)
    assert len(termine) == 105
    assert kontext.repos.serien.nach_id(serie.id).generiert_bis == HEUTE + timedelta(weeks=52)


def test_serie_mit_enddatum(kontext):
    serie = _serie_anlegen(kontext, ende=date(2026, 11, 26))
    tage = [t.datum for t in kontext.repos.aktivitaeten.termine_der_serie(serie.id)]
    assert tage == [date(2026, 11, 17), date(2026, 11, 19), date(2026, 11, 24), date(2026, 11, 26)]


def test_serie_ohne_wochentag_abgewiesen(kontext):
    with pytest.raises(ValidierungsFehler) as info:
        _serie_anlegen(kontext, tage=frozenset())
    assert info.value.meldung_fuer("wochentage") == "Bitte mindestens einen Wochentag wählen."
    assert kontext.repos.serien.alle() == []


def test_termin_ueberspringen_legt_ausnahme_an(kontext):
    serie = _serie_anlegen(kontext)
    termin = next(
        t
        for t in kontext.repos.aktivitaeten.termine_der_serie(serie.id)
        if t.datum == date(2026, 11, 19)
    )
    kontext.aktivitaeten.termin_ueberspringen(termin.id)
    assert date(2026, 11, 19) in kontext.repos.serien.nach_id(serie.id).ausnahmen
    assert kontext.repos.aktivitaeten.nach_id(termin.id) is None
    s = kontext.repos.serien.nach_id(serie.id)
    s.generiert_bis = None  # Horizont neu aufbauen erzwingen
    kontext.repos.serien.speichern(s)
    for t in kontext.repos.aktivitaeten.termine_der_serie(serie.id):
        kontext.repos.aktivitaeten.loeschen(t.id)
    kontext.aktivitaeten.horizont_fortschreiben()
    tage = [t.datum for t in kontext.repos.aktivitaeten.termine_der_serie(serie.id)]
    assert date(2026, 11, 19) not in tage and date(2026, 11, 24) in tage


def test_ueberspringen_ohne_serie_abgewiesen(kontext):
    a = kontext.aktivitaeten.speichern(_akt(kontext))
    with pytest.raises(RegelVerletzung):
        kontext.aktivitaeten.termin_ueberspringen(a.id)


def test_bearbeiteter_termin_wird_einzeln_markiert(kontext):
    serie = _serie_anlegen(kontext)
    termin = kontext.repos.aktivitaeten.termine_der_serie(serie.id)[2]
    kontext.aktivitaeten.speichern(replace(termin, titel="Intervalllauf"))
    assert kontext.repos.aktivitaeten.nach_id(termin.id).einzeln_bearbeitet


def test_serie_aendern_schont_bearbeitete_termine(kontext):
    serie = _serie_anlegen(kontext)
    termine = kontext.repos.aktivitaeten.termine_der_serie(serie.id)
    bearbeitet = kontext.aktivitaeten.speichern(replace(termine[3], titel="Sonderlauf"))
    s = kontext.repos.serien.nach_id(serie.id)
    s.titel, s.beginn, s.dauer_minuten = "Laufen", time(7, 0), 30
    kontext.aktivitaeten.serie_aendern(s)
    neu = kontext.repos.aktivitaeten.termine_der_serie(serie.id)
    assert next(t for t in neu if t.id == bearbeitet.id).titel == "Sonderlauf"
    assert next(t for t in neu if t.datum == date(2026, 11, 17)).titel == "Joggen"  # Vergangenheit
    zukunft = [t for t in neu if t.datum > HEUTE and t.id != bearbeitet.id]
    assert zukunft and all(
        (t.titel, t.beginn, t.dauer_minuten) == ("Laufen", time(7, 0), 30) for t in zukunft
    )
    assert len({t.datum for t in neu}) == len(neu)  # keine doppelten Termine


def _termin_am(kontext, serie, tag):
    return next(t for t in kontext.repos.aktivitaeten.termine_der_serie(serie.id) if t.datum == tag)


def _serie_neu_beschriften(kontext, serie):
    s = kontext.repos.serien.nach_id(serie.id)
    s.titel = "Laufen"
    kontext.aktivitaeten.serie_aendern(s)
    return kontext.repos.aktivitaeten.termine_der_serie(serie.id)


def test_serie_aendern_erzeugt_verschobenen_termin_nicht_neu(kontext):
    """GR19: Ein auf Mittwoch verschobener Dienstagstermin taucht nicht doppelt auf."""
    serie = _serie_anlegen(kontext)
    termin = _termin_am(kontext, serie, date(2026, 12, 1))
    kontext.aktivitaeten.speichern(replace(termin, datum=date(2026, 12, 2)))
    tage = [t.datum for t in _serie_neu_beschriften(kontext, serie)]
    assert date(2026, 12, 2) in tage and date(2026, 12, 1) not in tage


def test_serie_aendern_erzeugt_geloeschten_termin_nicht_neu(kontext):
    serie = _serie_anlegen(kontext)
    kontext.aktivitaeten.loeschen(_termin_am(kontext, serie, date(2026, 11, 26)).id)
    tage = [t.datum for t in _serie_neu_beschriften(kontext, serie)]
    assert date(2026, 11, 26) not in tage and date(2026, 12, 1) in tage


def test_verschobenen_termin_ueberspringen(kontext):
    serie = _serie_anlegen(kontext)
    termin = _termin_am(kontext, serie, date(2026, 12, 1))
    verschoben = kontext.aktivitaeten.speichern(replace(termin, datum=date(2026, 12, 2)))
    kontext.aktivitaeten.termin_ueberspringen(verschoben.id)
    assert kontext.repos.aktivitaeten.nach_id(verschoben.id) is None
    tage = [t.datum for t in _serie_neu_beschriften(kontext, serie)]
    assert date(2026, 12, 1) not in tage and date(2026, 12, 2) not in tage


def test_serie_loeschen_behaelt_vergangene_und_durchgefuehrte(kontext):
    serie = _serie_anlegen(kontext)
    termine = kontext.repos.aktivitaeten.termine_der_serie(serie.id)
    bearbeitet = kontext.aktivitaeten.speichern(replace(termine[4], titel="Sonderlauf"))
    kontext.aktivitaeten.serie_loeschen(serie.id)
    rest = kontext.repos.aktivitaeten.alle()
    assert {a.datum for a in rest} == {date(2026, 11, 17), bearbeitet.datum}
    assert all(a.serie_id is None for a in rest)
    assert kontext.repos.serien.alle() == []


def test_horizont_fortschreiben_ergaenzt_neue_termine(kontext):
    serie = _serie_anlegen(kontext)
    vorher = len(kontext.repos.aktivitaeten.termine_der_serie(serie.id))
    kontext.heute = lambda: HEUTE + timedelta(weeks=1)
    kontext.aktivitaeten._heute = kontext.heute
    assert kontext.aktivitaeten.horizont_fortschreiben() == 2
    assert len(kontext.repos.aktivitaeten.termine_der_serie(serie.id)) == vorher + 2


def test_eigener_bereich_mit_serie(kontext):
    garten = kontext.stammdaten.speichern(
        Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", 2)
    )
    vorlage = _akt(kontext, lebensbereich_id=garten.id, status=G, datum=date(2026, 11, 21))
    serie = kontext.aktivitaeten.serie_anlegen(
        vorlage, frozenset({Wochentag.SA}), date(2026, 12, 5)
    )
    assert len(kontext.repos.aktivitaeten.termine_der_serie(serie.id)) == 3
