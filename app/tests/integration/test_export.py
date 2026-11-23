"""Integrationstests des CSV- und JSON-Exports (US16, NFA10; Spez Kap. 4.3)."""

import csv
import json
from datetime import date, datetime, time

import pytest

from balanceos.anwendung.fehler import RegelVerletzung
from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet, Who5Erhebung, Wochenreflexion
from balanceos.domaene.typen import Aktivitaetsstatus, Bewegungsart, Wochentag
from balanceos.domaene.typen import StandardSchluessel as S

D = Aktivitaetsstatus.DURCHGEFUEHRT


def _bid(kontext, schluessel=S.BEWEGUNG) -> int:
    return kontext.repos.bereiche.nach_schluessel(schluessel).id


def _speichern(kontext, **k) -> Aktivitaet:
    basis = dict(
        titel="Joggen",
        lebensbereich_id=_bid(kontext),
        datum=date(2026, 11, 10),
        dauer_minuten=45,
        status=D,
    )
    basis.update(k)
    return kontext.repos.aktivitaeten.speichern(Aktivitaet(**basis))


def _csv_zeilen(pfad) -> list[list[str]]:
    with pfad.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f, delimiter=";"))


def test_dateinamen(kontext):
    e = kontext.export
    assert e.dateiname_csv(date(2026, 11, 9), date(2026, 11, 15)) == (
        "BalanceOS_Aktivitaeten_2026-11-09_2026-11-15.csv"
    )
    assert e.dateiname_json(date(2026, 11, 16)) == "BalanceOS_Export_2026-11-16.json"


def test_csv_bom_semikolon_crlf_kopfzeile(kontext, tmp_path):
    _speichern(
        kontext,
        beginn=time(18),
        ende=time(18, 45),
        zufriedenheit=4,
        bewegungsart=Bewegungsart.AUSDAUER_MODERAT,
    )
    pfad = tmp_path / "a.csv"
    assert kontext.export.csv_exportieren(pfad, date(2026, 11, 9), date(2026, 11, 15)) == 1
    roh = pfad.read_bytes()
    assert roh.startswith(b"\xef\xbb\xbfdatum;kalenderwoche;")
    assert roh.count(b"\r\n") == 2 and roh.endswith(b"\r\n")
    kopf, zeile = _csv_zeilen(pfad)
    assert tuple(kopf) == kontext.export.CSV_SPALTEN
    werte = dict(zip(kopf, zeile, strict=True))
    assert werte == {
        "datum": "2026-11-10",
        "kalenderwoche": "2026-W46",
        "lebensbereich": "Bewegung",
        "bereichstyp": "MINDESTZIEL",
        "titel": "Joggen",
        "beginn": "18:00",
        "ende": "18:45",
        "dauerMinuten": "45",
        "status": "DURCHGEFUEHRT",
        "zufriedenheit": "4",
        "belastung": "",
        "erholung": "",
        "bewegungsart": "AUSDAUER_MODERAT",
        "notiz": "",
        "ausSerie": "nein",
        "istDemo": "nein",
    }


def test_csv_quoting(kontext, tmp_path):
    _speichern(kontext, notiz='a;b "c"', titel="Zeile\numbruch")
    pfad = tmp_path / "q.csv"
    kontext.export.csv_exportieren(pfad, date(2026, 11, 9), date(2026, 11, 15))
    text = pfad.read_text(encoding="utf-8-sig")
    assert ';"a;b ""c""";' in text
    assert _csv_zeilen(pfad)[1][4] == "Zeile\numbruch"


def test_csv_zeitraum_und_sortierung(kontext, tmp_path):
    _speichern(kontext, titel="spät", datum=date(2026, 11, 12), beginn=time(20), ende=time(21))
    _speichern(kontext, titel="ohne Zeit", datum=date(2026, 11, 12))
    _speichern(kontext, titel="früh", datum=date(2026, 11, 12), beginn=time(7), ende=time(8))
    _speichern(kontext, titel="Montag", datum=date(2026, 11, 9))
    _speichern(kontext, titel="davor", datum=date(2026, 11, 8))
    _speichern(kontext, titel="danach", datum=date(2026, 11, 16))
    pfad = tmp_path / "z.csv"
    assert kontext.export.csv_exportieren(pfad, date(2026, 11, 9), date(2026, 11, 15)) == 4
    assert [z[4] for z in _csv_zeilen(pfad)[1:]] == ["Montag", "früh", "spät", "ohne Zeit"]


def test_csv_export_ohne_zeilen_nur_kopfzeile(kontext, tmp_path):
    pfad = tmp_path / "leer.csv"
    assert kontext.export.csv_exportieren(pfad, date(2026, 11, 9), date(2026, 11, 15)) == 0
    assert len(_csv_zeilen(pfad)) == 1


def test_json_struktur_und_schluessel(kontext, tmp_path):
    _speichern(kontext)
    kontext.repos.who5.speichern(Who5Erhebung(date(2026, 11, 15), [3, 4, 3, 2, 4]))
    kontext.repos.reflexionen.speichern(
        Wochenreflexion(KW(2026, 46), ("Mehr Zeit draußen verbracht.", "", ""), 4)
    )
    pfad = tmp_path / "e.json"
    kontext.export.json_exportieren(pfad, datetime(2026, 11, 16, 18, 30, 5))
    roh = pfad.read_bytes()
    assert not roh.startswith(b"\xef\xbb\xbf")
    assert "draußen".encode() in roh  # ensure_ascii=False
    daten = json.loads(roh.decode("utf-8"))
    assert list(daten) == [
        "format",
        "version",
        "exportiertAm",
        "einstellungen",
        "lebensbereiche",
        "aktivitaeten",
        "wiederholungsserien",
        "regeln",
        "who5Erhebungen",
        "wochenreflexionen",
    ]
    assert daten["format"] == "BalanceOS-Export" and daten["version"] == 1
    assert daten["exportiertAm"] == "2026-11-16T18:30:05"
    assert daten["einstellungen"] == {"alpha": 0.6, "gesamtScoreAnzeigen": False}
    assert len(daten["lebensbereiche"]) == 10
    assert set(daten["lebensbereiche"][0]) == {
        "name",
        "typ",
        "farbe",
        "aktiv",
        "istStandard",
        "sollStundenProWoche",
        "gewicht",
    }
    bewegung = next(b for b in daten["lebensbereiche"] if b["name"] == "Bewegung")
    assert bewegung["sollStundenProWoche"] == 3.0 and bewegung["istStandard"] is True
    a = daten["aktivitaeten"][0]
    assert a["lebensbereich"] == "Bewegung" and a["serie"] is None and a["notiz"] is None
    assert a["datum"] == "2026-11-10" and a["istDemo"] is False
    assert len(daten["regeln"]) == 10 and daten["regeln"][0] == {"kennung": "R01", "aktiv": True}
    assert daten["who5Erhebungen"] == [
        {"datum": "2026-11-15", "antworten": [3, 4, 3, 2, 4], "rohwert": 16, "prozentwert": 64}
    ]
    assert daten["wochenreflexionen"] == [
        {
            "jahr": 2026,
            "kalenderwoche": 46,
            "antworten": ["Mehr Zeit draußen verbracht.", "", ""],
            "stimmung": 4,
        }
    ]


def test_json_serienverweis_und_ausnahmen(kontext, tmp_path):
    vorlage = Aktivitaet(
        "Joggen",
        _bid(kontext),
        date(2026, 11, 3),
        45,
        Aktivitaetsstatus.DURCHGEFUEHRT,
        beginn=time(18),
        ende=time(18, 45),
    )
    serie = kontext.aktivitaeten.serie_anlegen(
        vorlage, frozenset({Wochentag.DI, Wochentag.DO}), date(2026, 11, 26)
    )
    termin = next(
        t
        for t in kontext.repos.aktivitaeten.termine_der_serie(serie.id)
        if t.datum == date(2026, 11, 19)
    )
    kontext.aktivitaeten.termin_ueberspringen(termin.id)
    _speichern(kontext, titel="einzeln")
    pfad = tmp_path / "s.json"
    kontext.export.json_exportieren(pfad, datetime(2026, 11, 16, 18, 30))
    daten = json.loads(pfad.read_text(encoding="utf-8"))
    assert daten["wiederholungsserien"] == [
        {
            "nr": 1,
            "titel": "Joggen",
            "lebensbereich": "Bewegung",
            "wochentage": ["DI", "DO"],
            "startdatum": "2026-11-03",
            "enddatum": "2026-11-26",
            "beginn": "18:00",
            "dauerMinuten": 45,
            "bewegungsart": None,
            "ausnahmen": ["2026-11-19"],
        }
    ]
    serien = {a["titel"]: a["serie"] for a in daten["aktivitaeten"]}
    assert serien == {"Joggen": 1, "einzeln": None}
    assert sum(1 for a in daten["aktivitaeten"] if a["serie"] == 1) == 7


def test_export_nicht_beschreibbar(kontext, tmp_path):
    with pytest.raises(RegelVerletzung, match="Hier kann nicht gespeichert werden."):
        kontext.export.csv_exportieren(tmp_path, date(2026, 11, 9), date(2026, 11, 15))
    with pytest.raises(RegelVerletzung, match="Hier kann nicht gespeichert werden."):
        kontext.export.json_exportieren(tmp_path, datetime(2026, 11, 16))
