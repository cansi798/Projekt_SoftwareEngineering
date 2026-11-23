"""Lasttests für NFA03 (3.000 Aktivitäten, etwa ein Jahr) und NFA12 (30.000 Aktivitäten).

Aufruf: ``pytest -m leistung -v -s``; die gemessenen Zeiten werden ausgegeben.
"""

import time
from datetime import date, timedelta

import pytest

from balanceos.anwendung.demodaten import erzeuge_demodaten
from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.kalender import KW
from balanceos.domaene.typen import StandardSchluessel

pytestmark = pytest.mark.leistung

HEUTE = date(2026, 11, 22)


def _kontext_mit(tmp_path, anzahl: int, wochen: int) -> AppKontext:
    """Datei-Datenbank mit ``anzahl`` Aktivitäten, verteilt über die letzten ``wochen`` Wochen.

    Die Demodaten (acht Wochen) werden blockweise um je acht Wochen zurückverschoben; reicht
    der Zeitraum nicht, beginnt die Verteilung von vorn und die Wochen werden dichter.
    """
    k = AppKontext.erstellen(tmp_path / "last.db", heute=lambda: HEUTE)
    bereiche = {s: k.repos.bereiche.nach_schluessel(s) for s in StandardSchluessel}
    bloecke = max(1, wochen // 8)
    daten = []
    nr = 0
    while len(daten) < anzahl:
        heute = HEUTE - timedelta(weeks=8 * (nr % bloecke))
        daten += erzeuge_demodaten(heute, bereiche)
        nr += 1
    k.repos.aktivitaeten.einfuegen_viele(daten[:anzahl])
    assert len(k.repos.aktivitaeten.alle()) == anzahl
    return k


def _dashboard_sekunden(k: AppKontext) -> float:
    kw = KW.heute(HEUTE).verschoben(-1)
    start = time.perf_counter()
    k.auswertung.wochenbewertung(kw)
    k.auswertung.hinweise(kw)
    return time.perf_counter() - start


def test_dashboard_3000_aktivitaeten_unter_1s(tmp_path):
    k = _kontext_mit(tmp_path, 3_000, 52)
    dauer = _dashboard_sekunden(k)
    print(f"\nNFA03 Dashboard, 3.000 Aktivitäten: {dauer * 1000:.0f} ms")
    assert dauer < 1.0


def test_dashboard_30000_aktivitaeten_unter_2s(tmp_path):
    k = _kontext_mit(tmp_path, 30_000, 520)
    dauer = _dashboard_sekunden(k)
    print(f"\nNFA12 Dashboard, 30.000 Aktivitäten: {dauer * 1000:.0f} ms")
    assert dauer < 2.0


def test_statistik_30000_unter_2s(tmp_path):
    k = _kontext_mit(tmp_path, 30_000, 520)
    start = time.perf_counter()
    k.auswertung.verlauf(KW.heute(HEUTE), 8)
    dauer = time.perf_counter() - start
    print(f"\nNFA12 Statistik (8 Wochen), 30.000 Aktivitäten: {dauer * 1000:.0f} ms")
    assert dauer < 2.0


def test_db_groesse_30000_unter_50mb(tmp_path):
    k = _kontext_mit(tmp_path, 30_000, 520)
    k.db.schliessen()
    groesse = (tmp_path / "last.db").stat().st_size / 1024**2
    print(f"\nNFA12 Datenbankgröße, 30.000 Aktivitäten: {groesse:.1f} MB")
    assert groesse < 50
