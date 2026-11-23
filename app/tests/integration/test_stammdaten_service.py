"""Integrationstests des Stammdaten-Services (US01–US04)."""

from dataclasses import replace
from datetime import date

import pytest

from balanceos.anwendung.fehler import RegelVerletzung, ValidierungsFehler
from balanceos.domaene.modell import Aktivitaet, Einstellungen, Lebensbereich
from balanceos.domaene.typen import Aktivitaetsstatus, Bereichstyp, StandardSchluessel


def _standard(kontext, schluessel):
    return next(
        b for b in kontext.stammdaten.alle_bereiche() if b.standard_schluessel is schluessel
    )


def test_erststart_zehn_standardbereiche(kontext):
    bereiche = kontext.stammdaten.alle_bereiche()
    assert len(bereiche) == 10 and all(b.ist_standard and b.aktiv for b in bereiche)
    assert kontext.stammdaten.verplante_stunden() == pytest.approx(143)


def test_standardbereich_nicht_loeschbar(kontext):
    with pytest.raises(RegelVerletzung, match="nur deaktiviert"):
        kontext.stammdaten.loeschen(_standard(kontext, StandardSchluessel.HOBBYS).id)


def test_genutzter_eigener_bereich_nicht_loeschbar(kontext):
    garten = kontext.stammdaten.speichern(
        Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", 2)
    )
    kontext.repos.aktivitaeten.speichern(
        Aktivitaet("Beet", garten.id, date(2026, 11, 17), 30, Aktivitaetsstatus.DURCHGEFUEHRT)
    )
    with pytest.raises(RegelVerletzung, match="verwendet"):
        kontext.stammdaten.loeschen(garten.id)


def test_eigener_ungenutzter_bereich_loeschbar(kontext):
    garten = kontext.stammdaten.speichern(
        Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", 2)
    )
    kontext.stammdaten.loeschen(garten.id)
    assert len(kontext.stammdaten.alle_bereiche()) == 10


def test_umbenennen_und_typ_aendern(kontext):
    hobbys = _standard(kontext, StandardSchluessel.HOBBYS)
    kontext.stammdaten.speichern(replace(hobbys, name="Musik", typ=Bereichstyp.OBERGRENZE))
    geaendert = _standard(kontext, StandardSchluessel.HOBBYS)
    assert (geaendert.name, geaendert.typ) == ("Musik", Bereichstyp.OBERGRENZE)


def test_deaktivieren_und_aktive_liste(kontext):
    hobbys = _standard(kontext, StandardSchluessel.HOBBYS)
    kontext.stammdaten.speichern(replace(hobbys, aktiv=False))
    assert hobbys.id not in [b.id for b in kontext.stammdaten.aktive_bereiche()]
    assert kontext.stammdaten.verplante_stunden() == pytest.approx(139)


def test_soll_summe_ueber_168_abgewiesen(kontext):
    schlaf = _standard(kontext, StandardSchluessel.SCHLAF)
    with pytest.raises(ValidierungsFehler) as info:
        kontext.stammdaten.speichern(replace(schlaf, soll_stunden=82))
    assert info.value.meldung_fuer("summe") == "Summe übersteigt 168 h pro Woche."
    assert _standard(kontext, StandardSchluessel.SCHLAF).soll_stunden == 56


def test_alpha_ausserhalb_abgewiesen(kontext):
    with pytest.raises(ValidierungsFehler):
        kontext.stammdaten.einstellungen_speichern(Einstellungen(alpha=1.5))
    kontext.stammdaten.einstellungen_speichern(Einstellungen(alpha=0.3, gesamtscore_anzeigen=True))
    assert kontext.stammdaten.einstellungen() == Einstellungen(0.3, True)
