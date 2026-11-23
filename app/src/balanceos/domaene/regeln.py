"""Regelwerk R01–R10: Hinweise mit Begründung und Evidenzkennzeichnung (GP04).

Die Regeln übertragen die Modelle des Balance-Kompasses in feste, prüfbare
Bedingungen (Spezifikation, Tabellen „Regelkatalog“ und „Beispieltexte“).
Jede Regel ist eine eigene Funktion; ``pruefe_regeln`` ruft die aktiven
Regeln auf und sortiert die Hinweise.
"""

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from statistics import fmean

from balanceos.domaene.kalender import KW, zahl_text
from balanceos.domaene.modell import (
    Aktivitaet,
    Begruendung,
    Hinweis,
    KompassModell,
    Lebensbereich,
    Regel,
    Wochenbewertung,
)
from balanceos.domaene.typen import (
    Aktivitaetsstatus,
    Bereichstyp,
    Bewegungsart,
    Hinweisart,
    StandardSchluessel,
)

GRENZE_STANDARD = (
    "Nur erfasste Aktivitäten werden berücksichtigt; der Hinweis ersetzt keine ärztliche Beratung."
)
ART_REIHENFOLGE = [Hinweisart.WARNUNG, Hinweisart.POSITIV, Hinweisart.SYSTEM]

KURZBELEG = {
    "WHO_BEWEGUNG": "WHO-Bewegungsleitlinie (Bull et al., 2020, S. 1451)",
    "SCHLAF": "Schlafempfehlung (Watson et al., 2015, S. 843)",
    "LBM": "Lifestyle Balance Model (Matuska & Christiansen, 2008, S. 11)",
    "ERM": "Effort-Recovery-Modell (Meijman & Mulder, 1998, S. 5–33)",
    "JDR": "Job-Demands-Resources-Theorie (Bakker & Demerouti, 2017, S. 274)",
    "SYSTEM": "BalanceOS-Systemregeln (programmeigen)",
}
"""Kurzbelege der Quellen je Modell im Format der Spezifikation."""

EVIDENZ = {
    "R01": "Empfehlung",
    "R02": "Empfehlung",
    "R03": "Empfehlung",
    "R04": "Theorie; Soll als persönliche Regel",
    "R05": "Theorie; Skalen programmeigen, theoriegeleitet",
    "R06": "Theorie; Regel programmeigen, theoriegeleitet",
    "R07": "Theorie; Skala programmeigen, theoriegeleitet",
    "R08": "Theorie; Soll als persönliche Regel",
    "R09": "Theorie; Skala programmeigen, theoriegeleitet",
    "R10": "programmeigen",
}
"""Evidenzkennzeichnung je Regel (Spalte „Evidenzkennzeichnung“ der Spezifikation)."""

HOHE_BELASTUNG = 4
GERINGE_ERHOLUNG = 2
MIN_SCHLAFTAGE = 4


@dataclass
class RegelKontext:
    """Eingangsdaten der Regelprüfung für eine Kalenderwoche.

    ``aktivitaeten`` umfasst mindestens die Woche ``kw`` und die zwei
    vorherigen; ``bewertungen`` enthält die Bewertungen dieser drei Wochen.
    """

    kw: KW
    bereiche: list[Lebensbereich]
    aktivitaeten: list[Aktivitaet]
    bewertungen: dict[KW, Wochenbewertung]
    regeln: dict[str, Regel]
    modelle: dict[str, KompassModell]


# --- Hilfsfunktionen -----------------------------------------------------------------------


def _h(stunden: float) -> str:
    """Stunden mit höchstens einer Nachkommastelle, ohne „,0“ (z. B. „12“, „1,5“)."""
    text = zahl_text(stunden)
    return text[:-2] if text.endswith(",0") else text


def _schwelle(k: RegelKontext, kennung: str) -> float:
    return k.regeln[kennung].schwelle


def _standard(k: RegelKontext, schluessel: StandardSchluessel) -> Lebensbereich | None:
    """Aktiver Standardbereich, auch wenn er umbenannt wurde; sonst ``None``."""
    return next((b for b in k.bereiche if b.standard_schluessel is schluessel and b.aktiv), None)


def _durchgefuehrt(k: RegelKontext, kw: KW, bereich_id: int | None = None) -> list[Aktivitaet]:
    montag, sonntag = kw.montag(), kw.sonntag()
    return [
        a
        for a in k.aktivitaeten
        if a.status is Aktivitaetsstatus.DURCHGEFUEHRT
        and montag <= a.datum <= sonntag
        and (bereich_id is None or a.lebensbereich_id == bereich_id)
    ]


def _wochen(k: RegelKontext, anzahl: int) -> list[KW]:
    """Die letzten ``anzahl`` Wochen bis einschließlich ``k.kw``, älteste zuerst."""
    return [k.kw.verschoben(-i) for i in range(anzahl - 1, -1, -1)]


def _alle_ausreichend(k: RegelKontext, wochen: list[KW]) -> bool:
    return all(w in k.bewertungen and k.bewertungen[w].ausreichende_daten for w in wochen)


def zeitraum_mehrerer_wochen(von: KW, bis: KW) -> str:
    """Zeitraum über mehrere Wochen, z. B. „KW 44–46/2026“ oder „KW 52/2026–KW 1/2027“."""
    if von.jahr == bis.jahr:
        return f"KW {von.woche}–{bis.woche}/{bis.jahr}"
    return f"{von.label()}–{bis.label()}"


def _hinweis(
    k: RegelKontext,
    kennung: str,
    art: Hinweisart,
    text: str,
    *,
    datenbasis: str,
    schwelle: str,
    wert: str,
    zeitraum: str | None = None,
    bereich_id: int | None = None,
    grenzen: str = GRENZE_STANDARD,
) -> Hinweis:
    regel = k.regeln[kennung]
    modell = k.modelle[regel.modell_schluessel]
    begruendung = Begruendung(
        regel=f"{kennung} – {regel.bezeichnung}",
        modell=modell.name,
        datenbasis=datenbasis,
        zeitraum=zeitraum or k.kw.zeitraum_text(),
        schwelle=schwelle,
        wert=wert,
        quelle=KURZBELEG.get(regel.modell_schluessel, modell.quelle),
        evidenzart=EVIDENZ[kennung],
        grenzen=grenzen,
    )
    return Hinweis(kennung, art, text, begruendung, k.kw, bereich_id)


# --- Regeln --------------------------------------------------------------------------------


def _r01(k: RegelKontext) -> list[Hinweis]:
    """Ausdauerbewegung: moderate Minuten plus doppelte intensive Minuten unter 150."""
    bewegung = _standard(k, StandardSchluessel.BEWEGUNG)
    if bewegung is None:
        return []
    faktor = {Bewegungsart.AUSDAUER_MODERAT: 1, Bewegungsart.AUSDAUER_INTENSIV: 2}
    minuten = sum(
        a.dauer_minuten * faktor.get(a.bewegungsart, 0)
        for a in _durchgefuehrt(k, k.kw, bewegung.id)
    )
    schwelle = _schwelle(k, "R01")
    if minuten >= schwelle:
        return []
    return [
        _hinweis(
            k,
            "R01",
            Hinweisart.WARNUNG,
            f"Ausdauerbewegung in KW {k.kw.woche}: {minuten} von {_h(schwelle)} Minuten"
            " – unter dem WHO-Richtwert.",
            datenbasis=f"durchgeführte Aktivitäten im Bereich {bewegung.name} mit Bewegungsart",
            schwelle=f"{_h(schwelle)} min (intensive Minuten zählen doppelt)",
            wert=f"{minuten} min",
        )
    ]


def _r02(k: RegelKontext) -> list[Hinweis]:
    """Muskelkräftigung an weniger als zwei Tagen."""
    bewegung = _standard(k, StandardSchluessel.BEWEGUNG)
    if bewegung is None:
        return []
    tage = len(
        {
            a.datum
            for a in _durchgefuehrt(k, k.kw, bewegung.id)
            if a.bewegungsart is Bewegungsart.KRAFT
        }
    )
    schwelle = _schwelle(k, "R02")
    if tage >= schwelle:
        return []
    return [
        _hinweis(
            k,
            "R02",
            Hinweisart.WARNUNG,
            f"Muskelkräftigende Aktivität in KW {k.kw.woche} an {tage} von {_h(schwelle)}"
            " empfohlenen Tagen.",
            datenbasis=f"durchgeführte Aktivitäten im Bereich {bewegung.name}"
            " mit Bewegungsart Kraft",
            schwelle=f"{_h(schwelle)} Tage mit muskelkräftigender Aktivität",
            wert=f"{tage} Tage",
        )
    ]


def _r03(k: RegelKontext) -> list[Hinweis]:
    """Durchschnittliche Schlafdauer je Tag mit Eintrag unter 7 h (ab vier Tagen)."""
    schlaf = _standard(k, StandardSchluessel.SCHLAF)
    if schlaf is None:
        return []
    je_tag: dict[date, int] = defaultdict(int)
    for a in _durchgefuehrt(k, k.kw, schlaf.id):
        je_tag[a.datum] += a.dauer_minuten
    if len(je_tag) < MIN_SCHLAFTAGE:
        return []
    mittel = fmean(je_tag.values()) / 60
    schwelle = _schwelle(k, "R03")
    if mittel >= schwelle:
        return []
    return [
        _hinweis(
            k,
            "R03",
            Hinweisart.WARNUNG,
            f"Durchschnittliche Schlafdauer in KW {k.kw.woche}: {_h(mittel)} h an {len(je_tag)}"
            f" Tagen mit Eintrag – unter der Empfehlung von mindestens {_h(schwelle)} h.",
            datenbasis=f"durchgeführte Aktivitäten im Bereich {schlaf.name}, Summe je Tag,"
            f" gemittelt über die Tage mit Eintrag (mindestens {MIN_SCHLAFTAGE})",
            schwelle=f"{_h(schwelle)} h pro Tag",
            wert=f"{_h(mittel)} h an {len(je_tag)} Tagen",
        )
    ]


def _r04(k: RegelKontext) -> list[Hinweis]:
    """Mindestziel-Bereich drei Wochen in Folge unter der Hälfte des Solls."""
    wochen = _wochen(k, 3)
    if not _alle_ausreichend(k, wochen):
        return []
    anteil = _schwelle(k, "R04")
    hinweise = []
    for b in k.bereiche:
        if not b.aktiv or b.typ is not Bereichstyp.MINDESTZIEL or b.soll_stunden <= 0:
            continue
        ist = [k.bewertungen[w].bereich(b.id).ist_stunden for w in wochen]
        if all(i < anteil * b.soll_stunden for i in ist):
            hinweise.append(
                _hinweis(
                    k,
                    "R04",
                    Hinweisart.WARNUNG,
                    f"Im Bereich {b.name} liegt die Zeit seit 3 Wochen unter der Hälfte des"
                    f" eigenen Wunsches (zuletzt {_h(ist[-1])} von {_h(b.soll_stunden)} h).",
                    datenbasis=f"durchgeführte Aktivitäten im Bereich {b.name} und dessen Soll",
                    zeitraum=zeitraum_mehrerer_wochen(wochen[0], wochen[-1]),
                    schwelle=f"weniger als {zahl_text(anteil * 100, 0)} % des Solls"
                    f" ({_h(anteil * b.soll_stunden)} h) in 3 Wochen in Folge",
                    wert=" · ".join(
                        f"{w.label()}: {_h(i)} h" for w, i in zip(wochen, ist, strict=True)
                    ),
                    bereich_id=b.id,
                )
            )
    return hinweise


def _r05(k: RegelKontext) -> list[Hinweis]:
    """Tage mit hoher Belastung bei geringer Erholung."""
    belastung: dict[date, list[int]] = defaultdict(list)
    erholung: dict[date, list[int]] = defaultdict(list)
    for a in _durchgefuehrt(k, k.kw):
        if a.belastung is not None:
            belastung[a.datum].append(a.belastung)
        if a.erholung is not None:
            erholung[a.datum].append(a.erholung)
    tage = sum(
        1
        for tag in belastung.keys() & erholung.keys()
        if fmean(belastung[tag]) >= HOHE_BELASTUNG and fmean(erholung[tag]) <= GERINGE_ERHOLUNG
    )
    schwelle = _schwelle(k, "R05")
    if tage < schwelle:
        return []
    return [
        _hinweis(
            k,
            "R05",
            Hinweisart.WARNUNG,
            f"An {tage} von 7 Tagen hohe Belastung bei geringer Erholung.",
            datenbasis="Belastungs- und Erholungswerte aller durchgeführten Aktivitäten,"
            " gemittelt je Tag",
            schwelle=f"mindestens {_h(schwelle)} Tage mit Ø Belastung ≥ {HOHE_BELASTUNG}"
            f" und Ø Erholung ≤ {GERINGE_ERHOLUNG}",
            wert=f"{tage} Tage",
        )
    ]


def _r06(k: RegelKontext) -> list[Hinweis]:
    """Wochenende ohne Erholung bei viel Zeit in Bereichen mit Obergrenze."""
    erholung = _standard(k, StandardSchluessel.ERHOLUNG)
    if erholung is None:
        return []
    wochenende = [a for a in _durchgefuehrt(k, k.kw) if a.datum.weekday() >= 5]
    erholt = sum(a.dauer_minuten for a in wochenende if a.lebensbereich_id == erholung.id)
    obergrenzen = [b for b in k.bereiche if b.aktiv and b.typ is Bereichstyp.OBERGRENZE]
    ids = {b.id for b in obergrenzen}
    belastet = sum(a.dauer_minuten for a in wochenende if a.lebensbereich_id in ids) / 60
    schwelle = _schwelle(k, "R06")
    if erholt > 0 or belastet < schwelle or not obergrenzen:
        return []
    namen = [b.name for b in obergrenzen]
    aufzaehlung = namen[0] if len(namen) == 1 else ", ".join(namen[:-1]) + " und " + namen[-1]
    return [
        _hinweis(
            k,
            "R06",
            Hinweisart.WARNUNG,
            f"Wochenende ohne Erholung bei {_h(belastet)} h für {aufzaehlung}.",
            datenbasis=f"durchgeführte Aktivitäten am Samstag und Sonntag im Bereich"
            f" {erholung.name} und in allen Bereichen mit Obergrenze",
            schwelle=f"0 h {erholung.name} bei mindestens {_h(schwelle)} h in Bereichen"
            " mit Obergrenze",
            wert=f"0 h {erholung.name}, {_h(belastet)} h in Bereichen mit Obergrenze",
        )
    ]


def _r07(k: RegelKontext) -> list[Hinweis]:
    """Arbeit in mindestens 2 von 3 Wochen über Soll bei hoher Belastung."""
    arbeit = _standard(k, StandardSchluessel.ARBEIT)
    wochen = _wochen(k, 3)
    if arbeit is None or not _alle_ausreichend(k, wochen):
        return []
    ueber = sum(
        1 for w in wochen if k.bewertungen[w].bereich(arbeit.id).ist_stunden > arbeit.soll_stunden
    )
    werte = [
        a.belastung
        for w in wochen
        for a in _durchgefuehrt(k, w, arbeit.id)
        if a.belastung is not None
    ]
    schwelle = _schwelle(k, "R07")
    if ueber < 2 or not werte or fmean(werte) < schwelle:
        return []
    mittel = zahl_text(fmean(werte))
    return [
        _hinweis(
            k,
            "R07",
            Hinweisart.WARNUNG,
            f"{arbeit.name} in {ueber} der letzten 3 Wochen über dem Soll bei hoher Belastung"
            f" (Ø {mittel}) – Anforderungen und Ressourcen prüfen.",
            datenbasis=f"durchgeführte Aktivitäten im Bereich {arbeit.name}, Soll und"
            " Belastungswerte",
            zeitraum=zeitraum_mehrerer_wochen(wochen[0], wochen[-1]),
            schwelle=f"Ist über Soll ({_h(arbeit.soll_stunden)} h) in mindestens 2 von 3 Wochen"
            f" und Ø Belastung ≥ {_h(schwelle)}",
            wert=f"{ueber} Wochen über Soll, Ø Belastung {mittel}",
        )
    ]


def _r08(k: RegelKontext) -> list[Hinweis]:
    """Mindestziel-Bereich hat das Soll erreicht."""
    bewertung = k.bewertungen[k.kw]
    hinweise = []
    for b in k.bereiche:
        bw = bewertung.bereich(b.id)
        if (
            bw is None
            or b.typ is not Bereichstyp.MINDESTZIEL
            or bw.zielerfuellung is None
            or bw.zielerfuellung < _schwelle(k, "R08")
        ):
            continue
        hinweise.append(
            _hinweis(
                k,
                "R08",
                Hinweisart.POSITIV,
                f"Wunsch im Bereich {b.name} in KW {k.kw.woche} erreicht:"
                f" {_h(bw.ist_stunden)} von {_h(b.soll_stunden)} h.",
                datenbasis=f"durchgeführte Aktivitäten im Bereich {b.name} und dessen Soll",
                schwelle=f"Zielerfüllung 100 % (mindestens {_h(b.soll_stunden)} h)",
                wert=f"{_h(bw.ist_stunden)} h",
                bereich_id=b.id,
            )
        )
    return hinweise


def _r09(k: RegelKontext) -> list[Hinweis]:
    """Durchschnittliche Zufriedenheit gegenüber der Vorwoche um mindestens 1 Punkt gestiegen."""
    vorwoche = k.kw.verschoben(-1)
    if not _alle_ausreichend(k, [vorwoche, k.kw]):
        return []
    schwelle = _schwelle(k, "R09")
    hinweise = []
    for b in k.bereiche:
        if not b.aktiv:
            continue
        mittel = []
        for w in (vorwoche, k.kw):
            werte = [
                a.zufriedenheit for a in _durchgefuehrt(k, w, b.id) if a.zufriedenheit is not None
            ]
            mittel.append(fmean(werte) if werte else None)
        alt, neu = mittel
        if alt is None or neu is None or neu - alt < schwelle:
            continue
        hinweise.append(
            _hinweis(
                k,
                "R09",
                Hinweisart.POSITIV,
                f"Zufriedenheit im Bereich {b.name} gegenüber KW {vorwoche.woche} gestiegen"
                f" (von {zahl_text(alt)} auf {zahl_text(neu)}).",
                datenbasis=f"Zufriedenheitswerte der durchgeführten Aktivitäten im Bereich"
                f" {b.name}",
                zeitraum=zeitraum_mehrerer_wochen(vorwoche, k.kw),
                schwelle=f"Anstieg des Mittelwerts um mindestens {_h(schwelle)} Punkt",
                wert=f"{zahl_text(alt)} → {zahl_text(neu)}",
                bereich_id=b.id,
            )
        )
    return hinweise


def _r10(k: RegelKontext) -> list[Hinweis]:
    """Zu wenige erfasste Tage für eine Bewertung."""
    tage = k.bewertungen[k.kw].vollstaendigkeit_tage
    schwelle = _schwelle(k, "R10")
    if tage >= schwelle:
        return []
    return [
        _hinweis(
            k,
            "R10",
            Hinweisart.SYSTEM,
            f"Für KW {k.kw.woche} liegen Einträge an {tage} von 7 Tagen vor"
            " – zu wenig Daten für eine Bewertung.",
            datenbasis="Tage mit mindestens einer durchgeführten Aktivität in aktiven Bereichen",
            schwelle=f"mindestens {_h(schwelle)} von 7 Tagen",
            wert=f"{tage} von 7 Tagen",
            grenzen=k.modelle["SYSTEM"].grenzen,
        )
    ]


REGELFUNKTIONEN: dict[str, Callable[[RegelKontext], list[Hinweis]]] = {
    "R01": _r01,
    "R02": _r02,
    "R03": _r03,
    "R04": _r04,
    "R05": _r05,
    "R06": _r06,
    "R07": _r07,
    "R08": _r08,
    "R09": _r09,
}


def pruefe_regeln(k: RegelKontext) -> list[Hinweis]:
    """Prüft alle aktiven Regeln für ``k.kw`` und liefert die sortierten Hinweise.

    Bei unzureichenden Daten entsteht nur der Systemhinweis R10; R01–R09 werden
    dann nicht geprüft (GR21). Deaktivierte Regeln werden übersprungen (GR25).
    Sortiert wird nach Hinweisart (Warnung, positiv, System), dann nach
    Regelkennung und dann nach der Reihenfolge der Lebensbereiche.
    """
    aktiv = {kennung for kennung, r in k.regeln.items() if r.aktiv}
    if not k.bewertungen[k.kw].ausreichende_daten:
        return _r10(k) if "R10" in aktiv else []
    hinweise = [
        h for kennung, regel in REGELFUNKTIONEN.items() if kennung in aktiv for h in regel(k)
    ]
    position = {b.id: nr for nr, b in enumerate(k.bereiche)}
    hinweise.sort(
        key=lambda h: (
            ART_REIHENFOLGE.index(h.art),
            h.regel,
            position.get(h.lebensbereich_id, -1),
        )
    )
    return hinweise
