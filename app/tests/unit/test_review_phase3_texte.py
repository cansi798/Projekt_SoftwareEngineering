"""Regressionstests zu Befunden des Phase-3-Reviews: Hinweis- und Meldungstexte (GP04, GR22)."""

from dataclasses import replace
from datetime import timedelta

from balanceos.domaene.bewertung import bewerte_woche
from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet, Einstellungen
from balanceos.domaene.regeln import RegelKontext, pruefe_regeln
from balanceos.domaene.typen import Aktivitaetsstatus
from balanceos.domaene.typen import StandardSchluessel as S
from balanceos.persistenz.stammdaten import KOMPASSMODELLE, REGELN, STANDARDBEREICHE

KW46 = KW(2026, 46)
D = Aktivitaetsstatus.DURCHGEFUEHRT
BEREICHE = [replace(b, id=nr) for nr, b in enumerate(STANDARDBEREICHE, start=1)]
ID = {b.standard_schluessel: b.id for b in BEREICHE}


def _akt(schluessel, kw, tag, minuten) -> Aktivitaet:
    return Aktivitaet("x", ID[schluessel], kw.montag() + timedelta(days=tag), minuten, D)


def _fuellen(kw) -> list[Aktivitaet]:
    return [_akt(S.VERPFLICHTUNGEN, kw, tag, 60) for tag in range(5)]


def _hinweis(aktivitaeten, regel, kw=KW46, bereich=None):
    wochen = [kw, kw.verschoben(-1), kw.verschoben(-2)]
    kontext = RegelKontext(
        kw=kw,
        bereiche=BEREICHE,
        aktivitaeten=aktivitaeten,
        bewertungen={w: bewerte_woche(w, BEREICHE, aktivitaeten, Einstellungen()) for w in wochen},
        regeln={r.kennung: r for r in REGELN},
        modelle={m.schluessel: m for m in KOMPASSMODELLE},
    )
    treffer = [
        h
        for h in pruefe_regeln(kontext)
        if h.regel == regel and (bereich is None or h.lebensbereich_id == ID[bereich])
    ]
    assert len(treffer) == 1, [h.regel for h in pruefe_regeln(kontext)]
    return treffer[0]


# --- C1: Werte knapp unter der Schwelle nicht auf die Schwelle runden -----------------------


def test_r03_knapp_unter_sieben_stunden_nicht_als_sieben_angezeigt():
    # Ø 418,75 min = 6,979 h: kaufmännisch gerundet wären das „7 h“.
    daten = _fuellen(KW46) + [
        _akt(S.SCHLAF, KW46, tag, minuten) for tag, minuten in enumerate([419, 419, 419, 418])
    ]
    h = _hinweis(daten, "R03")
    assert h.text == (
        "Durchschnittliche Schlafdauer in KW 46: 6,9 h an 4 Tagen mit Eintrag"
        " – unter der Empfehlung von mindestens 7 h."
    )
    assert h.begruendung.wert == "6,9 h an 4 Tagen"


def test_r04_knapp_unter_der_haelfte_nicht_als_haelfte_angezeigt():
    daten = []
    for i, minuten in enumerate([60, 60, 119]):  # zuletzt 1,98 h bei Soll 4 h
        w = KW46.verschoben(i - 2)
        daten += _fuellen(w) + [_akt(S.SOZIALE_KONTAKTE, w, 5, minuten)]
    h = _hinweis(daten, "R04", bereich=S.SOZIALE_KONTAKTE)
    assert h.text == (
        "Im Bereich Soziale Kontakte liegt die Zeit seit 3 Wochen unter der Hälfte"
        " des eigenen Wunsches (zuletzt 1,9 von 4 h)."
    )
    assert h.begruendung.wert.endswith("KW 46/2026: 1,9 h")


def test_r03_rundung_unveraendert_wenn_schwelle_nicht_erreicht_wird():
    # Ø 6,45 h wird weiterhin kaufmännisch auf 6,5 h gerundet (Spezifikationsbeispiel 6,5 h).
    daten = _fuellen(KW46) + [_akt(S.SCHLAF, KW46, tag, 387) for tag in range(4)]
    assert "Schlafdauer in KW 46: 6,5 h" in _hinweis(daten, "R03").text


# --- C3: Singular und Plural in der WHO-5-Meldung -------------------------------------------


def test_who5_meldung_singular_bei_einer_offenen_aussage():
    from datetime import date

    from balanceos.domaene.validierung import pruefe_who5

    tag = date(2026, 11, 18)
    assert pruefe_who5(tag, [3, 3, 3, 3, None], tag)[0].meldung == "Noch offen: 1 Aussage."
    assert pruefe_who5(tag, [3, 3, 3, None, None], tag)[0].meldung == "Noch offen: 2 Aussagen."
    assert pruefe_who5(tag, [], tag)[0].meldung == "Noch offen: 5 Aussagen."
