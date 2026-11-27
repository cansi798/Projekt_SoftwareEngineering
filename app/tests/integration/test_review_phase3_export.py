"""Regressionstest: Der CSV-Export schützt Textfelder vor der Auswertung als Formel."""

import csv
from dataclasses import replace
from datetime import date

from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus
from balanceos.domaene.typen import StandardSchluessel as S


def test_csv_textfelder_mit_formelzeichen_erhalten_apostroph(kontext, tmp_path):
    bereich = kontext.repos.bereiche.nach_schluessel(S.HOBBYS)
    kontext.repos.bereiche.speichern(replace(bereich, name="=Hobby"))
    titel = ["=SUMME(1;2)", "+49 Anruf", "-Joggen", "@Termin", "Joggen"]
    for i, t in enumerate(titel):
        kontext.repos.aktivitaeten.speichern(
            Aktivitaet(
                titel=t,
                lebensbereich_id=bereich.id,
                datum=date(2026, 11, 10 + i),
                dauer_minuten=30,
                status=Aktivitaetsstatus.DURCHGEFUEHRT,
                notiz="\tTabulator" if i == 0 else None,
            )
        )
    pfad = tmp_path / "formel.csv"
    kontext.export.csv_exportieren(pfad, date(2026, 11, 9), date(2026, 11, 15))
    with pfad.open(encoding="utf-8-sig", newline="") as f:
        zeilen = list(csv.reader(f, delimiter=";"))[1:]
    assert [z[4] for z in zeilen] == [
        "'=SUMME(1;2)",
        "'+49 Anruf",
        "'-Joggen",
        "'@Termin",
        "Joggen",
    ]
    assert {z[2] for z in zeilen} == {"'=Hobby"}
    assert zeilen[0][13] == "'\tTabulator"
    assert zeilen[1][13] == ""
