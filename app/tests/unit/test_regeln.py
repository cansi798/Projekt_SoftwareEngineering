"""Tests des Regelwerks R01–R10 (GP04) mit Texten aus Spez Tab. „Beispieltexte“."""

from dataclasses import replace
from datetime import timedelta

from balanceos.domaene.bewertung import bewerte_woche
from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet, Einstellungen
from balanceos.domaene.regeln import RegelKontext, pruefe_regeln
from balanceos.domaene.typen import Aktivitaetsstatus, Bewegungsart, Hinweisart
from balanceos.domaene.typen import StandardSchluessel as S
from balanceos.persistenz.stammdaten import KOMPASSMODELLE, REGELN, STANDARDBEREICHE

KW46 = KW(2026, 46)
D = Aktivitaetsstatus.DURCHGEFUEHRT
BEREICHE = [replace(b, id=nr) for nr, b in enumerate(STANDARDBEREICHE, start=1)]
ID = {b.standard_schluessel: b.id for b in BEREICHE}


def akt(schluessel, kw, tag, minuten, **k) -> Aktivitaet:
    """Durchgeführte Aktivität am Wochentag ``tag`` (0 = Montag) der Woche ``kw``."""
    return Aktivitaet("x", ID[schluessel], kw.montag() + timedelta(days=tag), minuten, D, **k)


def fuellen(kw) -> list[Aktivitaet]:
    """Eine Stunde Verpflichtungen Mo–Fr, damit die Woche ausreichende Daten hat."""
    return [akt(S.VERPFLICHTUNGEN, kw, tag, 60) for tag in range(5)]


def kontext_mit(aktivitaeten, kw=KW46, bereiche=None, regeln=None) -> RegelKontext:
    bereiche = bereiche or BEREICHE
    wochen = [kw, kw.verschoben(-1), kw.verschoben(-2)]
    return RegelKontext(
        kw=kw,
        bereiche=bereiche,
        aktivitaeten=aktivitaeten,
        bewertungen={w: bewerte_woche(w, bereiche, aktivitaeten, Einstellungen()) for w in wochen},
        regeln={r.kennung: r for r in (regeln or REGELN)},
        modelle={m.schluessel: m for m in KOMPASSMODELLE},
    )


def hinweise_fuer(aktivitaeten, **k):
    return pruefe_regeln(kontext_mit(aktivitaeten, **k))


def einziger(hinweise, regel, bereich=None):
    treffer = [
        h
        for h in hinweise
        if h.regel == regel and (bereich is None or h.lebensbereich_id == ID[bereich])
    ]
    assert len(treffer) == 1, [h.regel for h in hinweise]
    return treffer[0]


def keiner(hinweise, regel, bereich=None) -> bool:
    return not any(
        h.regel == regel and (bereich is None or h.lebensbereich_id == ID[bereich])
        for h in hinweise
    )


MOD, INT, KRAFT = Bewegungsart.AUSDAUER_MODERAT, Bewegungsart.AUSDAUER_INTENSIV, Bewegungsart.KRAFT


# --- R01, R02: WHO-Bewegungsleitlinie -------------------------------------------------------


def _r01_daten():
    return fuellen(KW46) + [
        akt(S.BEWEGUNG, KW46, 0, 60, bewegungsart=MOD),
        akt(S.BEWEGUNG, KW46, 1, 15, bewegungsart=INT),
    ]


def test_r01_text_und_begruendung():
    h = einziger(hinweise_fuer(_r01_daten()), "R01")
    assert h.art is Hinweisart.WARNUNG
    assert h.text == "Ausdauerbewegung in KW 46: 90 von 150 Minuten – unter dem WHO-Richtwert."
    b = h.begruendung
    assert b.zeitraum == "KW 46/2026 (09.11.–15.11.2026)"
    assert b.wert == "90 min" and b.schwelle.startswith("150 min")
    assert b.regel == "R01 – Ausdauerbewegung unter Richtwert"
    assert b.quelle == "WHO-Bewegungsleitlinie (Bull et al., 2020, S. 1451)"
    assert b.evidenzart == "Empfehlung"
    assert "keine ärztliche Beratung" in b.grenzen


def test_r01_genau_150_kein_hinweis():
    daten = fuellen(KW46) + [akt(S.BEWEGUNG, KW46, 0, 150, bewegungsart=MOD)]
    assert keiner(hinweise_fuer(daten), "R01")


def test_r01_ohne_bewegungsart_zaehlt_nicht():
    daten = fuellen(KW46) + [akt(S.BEWEGUNG, KW46, 0, 200)]
    assert einziger(hinweise_fuer(daten), "R01").begruendung.wert == "0 min"


def test_r02_loest_aus_bei_einem_krafttag():
    daten = fuellen(KW46) + [akt(S.BEWEGUNG, KW46, 0, 30, bewegungsart=KRAFT)] * 2
    h = einziger(hinweise_fuer(daten), "R02")
    assert h.text == "Muskelkräftigende Aktivität in KW 46 an 1 von 2 empfohlenen Tagen."


def test_r02_zwei_krafttage_kein_hinweis():
    daten = fuellen(KW46) + [
        akt(S.BEWEGUNG, KW46, 0, 30, bewegungsart=KRAFT),
        akt(S.BEWEGUNG, KW46, 2, 30, bewegungsart=KRAFT),
    ]
    assert keiner(hinweise_fuer(daten), "R02")


# --- R03: Schlaf ----------------------------------------------------------------------------


def test_r03_nur_ab_vier_tagen_mit_eintrag():
    daten = fuellen(KW46) + [akt(S.SCHLAF, KW46, tag, 360) for tag in range(3)]
    assert keiner(hinweise_fuer(daten), "R03")


def test_r03_loest_aus():
    daten = fuellen(KW46) + [akt(S.SCHLAF, KW46, tag, 390) for tag in range(4)]
    h = einziger(hinweise_fuer(daten), "R03")
    assert h.text == (
        "Durchschnittliche Schlafdauer in KW 46: 6,5 h an 4 Tagen mit Eintrag"
        " – unter der Empfehlung von mindestens 7 h."
    )


def test_r03_summe_je_tag_genau_sieben_kein_hinweis():
    daten = fuellen(KW46)
    for tag in range(4):
        daten += [akt(S.SCHLAF, KW46, tag, 360), akt(S.SCHLAF, KW46, tag, 60)]
    assert keiner(hinweise_fuer(daten), "R03")


# --- R04: dauerhaft unter Wunsch ------------------------------------------------------------


def _drei_wochen(kw, stunden: list[float]) -> list[Aktivitaet]:
    daten = []
    for i, h in enumerate(stunden):
        w = kw.verschoben(i - 2)
        daten += fuellen(w) + [akt(S.SOZIALE_KONTAKTE, w, 5, round(h * 60))]
    return daten


def test_r04_loest_aus():
    h = einziger(hinweise_fuer(_drei_wochen(KW46, [1, 1, 1.5])), "R04", S.SOZIALE_KONTAKTE)
    assert h.text == (
        "Im Bereich Soziale Kontakte liegt die Zeit seit 3 Wochen unter der Hälfte"
        " des eigenen Wunsches (zuletzt 1,5 von 4 h)."
    )
    assert h.begruendung.zeitraum == "KW 44–46/2026"


def test_r04_an_der_schwelle_kein_hinweis():
    assert keiner(hinweise_fuer(_drei_wochen(KW46, [1, 2, 1])), "R04", S.SOZIALE_KONTAKTE)


def test_r04_nicht_bei_unvollstaendiger_vorwoche():
    daten = [a for a in _drei_wochen(KW46, [1, 1, 1]) if KW.aus_datum(a.datum) != KW(2026, 44)]
    assert keiner(hinweise_fuer(daten), "R04")


def test_r04_ueber_jahreswechsel():
    kw1 = KW(2027, 1)
    h = einziger(hinweise_fuer(_drei_wochen(kw1, [1, 1, 1]), kw=kw1), "R04", S.SOZIALE_KONTAKTE)
    assert h.begruendung.zeitraum == "KW 52/2026–KW 1/2027"
    assert kw1.verschoben(-1) == KW(2026, 53)


# --- R05, R06: Effort-Recovery-Modell -------------------------------------------------------


def _belastete_tage(anzahl: int) -> list[Aktivitaet]:
    return fuellen(KW46) + [
        akt(S.ARBEIT, KW46, tag, 480, belastung=5, erholung=1)
        if tag % 2
        else akt(S.ARBEIT, KW46, tag, 480, belastung=4, erholung=2)
        for tag in range(anzahl)
    ]


def test_r05_loest_aus():
    h = einziger(hinweise_fuer(_belastete_tage(4)), "R05")
    assert h.text == "An 4 von 7 Tagen hohe Belastung bei geringer Erholung."


def test_r05_drei_tage_kein_hinweis():
    assert keiner(hinweise_fuer(_belastete_tage(3)), "R05")


def test_r05_ignoriert_deaktivierten_bereich():
    """GR14: Aktivitäten deaktivierter Bereiche zählen auch für R05 nicht."""
    bereiche = [replace(b, aktiv=False) if b.id == ID[S.ARBEIT] else b for b in BEREICHE]
    assert keiner(hinweise_fuer(_belastete_tage(5), bereiche=bereiche), "R05")


def test_r05_tag_ohne_erholungswert_zaehlt_nicht():
    daten = fuellen(KW46) + [akt(S.ARBEIT, KW46, t, 480, belastung=5) for t in range(5)]
    assert keiner(hinweise_fuer(daten), "R05")


def _wochenende(erholung_minuten: int) -> list[Aktivitaet]:
    daten = fuellen(KW46) + [
        akt(S.ARBEIT, KW46, 5, 240),
        akt(S.VERPFLICHTUNGEN, KW46, 6, 120),
    ]
    if erholung_minuten:
        daten.append(akt(S.ERHOLUNG, KW46, 6, erholung_minuten))
    return daten


def test_r06_loest_aus():
    h = einziger(hinweise_fuer(_wochenende(0)), "R06")
    assert h.text == "Wochenende ohne Erholung bei 6 h für Arbeit und Alltägliche Verpflichtungen."


def test_r06_mit_erholung_kein_hinweis():
    assert keiner(hinweise_fuer(_wochenende(60)), "R06")


# --- R07: Job-Demands-Resources -------------------------------------------------------------


def _arbeit(belastung: int) -> list[Aktivitaet]:
    daten = []
    for i, minuten in enumerate([400, 492, 492]):  # 33,3 h; 41 h; 41 h
        w = KW46.verschoben(i - 2)
        daten += fuellen(w)
        daten += [akt(S.ARBEIT, w, t, minuten, belastung=belastung) for t in range(5)]
    return daten


def test_r07_loest_aus():
    h = einziger(hinweise_fuer(_arbeit(5)), "R07")
    assert h.text == (
        "Arbeit in 2 der letzten 3 Wochen über dem Soll bei hoher Belastung (Ø 5,0)"
        " – Anforderungen und Ressourcen prüfen."
    )


def test_r07_geringe_belastung_kein_hinweis():
    assert keiner(hinweise_fuer(_arbeit(3)), "R07")


def test_r07_ohne_soll_kein_hinweis():
    """GR22: Soll 0 heißt „kein Soll festgelegt“, also gibt es kein „über dem Soll“."""
    bereiche = [replace(b, soll_stunden=0) if b.id == ID[S.ARBEIT] else b for b in BEREICHE]
    assert keiner(hinweise_fuer(_arbeit(5), bereiche=bereiche), "R07")


# --- R08, R09: positive Hinweise ------------------------------------------------------------


def test_r08_positiv_bei_erreichtem_wunsch():
    h = einziger(hinweise_fuer(fuellen(KW46) + [akt(S.FAMILIE, KW46, 5, 720)]), "R08", S.FAMILIE)
    assert h.art is Hinweisart.POSITIV
    assert h.text == "Wunsch im Bereich Familie in KW 46 erreicht: 12 von 10 h."


def test_r08_knapp_darunter_kein_hinweis():
    assert keiner(hinweise_fuer(fuellen(KW46) + [akt(S.FAMILIE, KW46, 5, 570)]), "R08", S.FAMILIE)


def _zufriedenheit(neu: list[int]) -> list[Aktivitaet]:
    kw45 = KW46.verschoben(-1)
    daten = fuellen(kw45) + fuellen(KW46) + [akt(S.HOBBYS, kw45, 5, 60, zufriedenheit=3)]
    return daten + [akt(S.HOBBYS, KW46, 5, 60, zufriedenheit=z) for z in neu]


def test_r09_loest_aus():
    h = einziger(hinweise_fuer(_zufriedenheit([4, 5])), "R09", S.HOBBYS)
    assert h.text == "Zufriedenheit im Bereich Hobbys gegenüber KW 45 gestiegen (von 3,0 auf 4,5)."
    assert h.begruendung.zeitraum == "KW 45–46/2026"


def test_r09_halber_punkt_kein_hinweis():
    assert keiner(hinweise_fuer(_zufriedenheit([3, 4])), "R09")


# --- R10, Sortierung, Steuerung -------------------------------------------------------------


def test_r10_einziger_hinweis_bei_drei_tagen():
    daten = [akt(S.BEWEGUNG, KW46, t, 30) for t in range(3)]
    hinweise = hinweise_fuer(daten)
    assert [h.regel for h in hinweise] == ["R10"]
    assert hinweise[0].art is Hinweisart.SYSTEM
    assert hinweise[0].text == (
        "Für KW 46 liegen Einträge an 3 von 7 Tagen vor – zu wenig Daten für eine Bewertung."
    )


def test_r10_deaktiviert_keine_hinweise():
    regeln = [replace(r, aktiv=r.kennung != "R10") for r in REGELN]
    assert hinweise_fuer([], regeln=regeln) == []


def test_sortierung_warnung_positiv_system():
    daten = _r01_daten() + [akt(S.FAMILIE, KW46, 5, 720), akt(S.HOBBYS, KW46, 6, 300)]
    hinweise = hinweise_fuer(daten)
    reihenfolge = [Hinweisart.WARNUNG, Hinweisart.POSITIV, Hinweisart.SYSTEM]
    schluessel = [(reihenfolge.index(h.art), h.regel) for h in hinweise]
    assert schluessel == sorted(schluessel)
    assert hinweise[0].art is Hinweisart.WARNUNG and hinweise[-1].art is Hinweisart.POSITIV
    r08 = [h.lebensbereich_id for h in hinweise if h.regel == "R08"]
    assert r08 == sorted(r08)


def test_deaktivierte_regel_erzeugt_nichts():
    regeln = [replace(r, aktiv=r.kennung != "R01") for r in REGELN]
    assert keiner(hinweise_fuer(_r01_daten(), regeln=regeln), "R01")


def test_regeln_finden_umbenannten_standardbereich():
    bereiche = [replace(b, name="Sport") if b.id == ID[S.BEWEGUNG] else b for b in BEREICHE]
    h = einziger(hinweise_fuer(_r01_daten(), bereiche=bereiche), "R01")
    assert "Sport" in h.begruendung.datenbasis


def test_regel_bei_deaktiviertem_bereich_ausgelassen():
    bereiche = [replace(b, aktiv=False) if b.id == ID[S.SCHLAF] else b for b in BEREICHE]
    daten = fuellen(KW46) + [akt(S.SCHLAF, KW46, tag, 300) for tag in range(5)]
    assert keiner(hinweise_fuer(daten, bereiche=bereiche), "R03")


def test_regel_bei_fehlendem_standardbereich_ausgelassen():
    bereiche = [b for b in BEREICHE if b.id != ID[S.ERHOLUNG]]
    assert keiner(hinweise_fuer(_wochenende(0), bereiche=bereiche), "R06")


def test_jeder_hinweis_vollstaendig_begruendet():
    szenarien = [
        _r01_daten(),
        _drei_wochen(KW46, [1, 1, 1]),
        _belastete_tage(5),
        _wochenende(0),
        _arbeit(5),
        _zufriedenheit([5]),
        [akt(S.SCHLAF, KW46, tag, 300) for tag in range(4)] + fuellen(KW46),
        fuellen(KW46) + [akt(S.FAMILIE, KW46, 5, 720)],
        [akt(S.FAMILIE, KW46, 1, 60)],
    ]
    alle = [h for daten in szenarien for h in hinweise_fuer(daten)]
    assert {h.regel for h in alle} == {f"R{n:02d}" for n in range(1, 11)}
    for h in alle:
        assert h.kw == KW46
        for beschriftung, inhalt in h.begruendung.zeilen():
            assert inhalt.strip(), (h.regel, beschriftung)
