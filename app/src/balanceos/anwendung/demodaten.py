"""Demodaten: acht Wochen aus dem Alltag der Persona Sarah Keller (US18, GP09).

Die Daten sind deterministisch (fester Zufallsstartwert) und so gewählt, dass
mit dem Standard-Wunschprofil jede Regel R01–R10 mindestens einmal auslöst:

=====  =======================  ===========================================
Woche  Abschnitt                Hinweise mit Standard-Wunschprofil
=====  =======================  ===========================================
1      Rückkehr aus dem Urlaub  R10 (Einträge an nur drei Tagen)
2      normale Woche            R08
3      Projektphase, Beginn     R01, R02, R05, R06 (Wochenendarbeit), R09
4      Projektphase, Höhepunkt  R01, R02, R05 (Belastung hoch), R09
5      Projektabschluss         R01, R02, R03 (wenig Schlaf), R04, R07
6      Erholungswoche           R04, R08, R09 (Hobbys zufriedener)
7      Vorwoche                 R01 „90 von 150“, R02, R04, R08, R09
8      aktuelle Woche           R04 (Soziale Kontakte), R08
=====  =======================  ===========================================

Ausgewertet mit ``heute = 22.11.2026``; der Test
``test_demodaten_decken_alle_regeln_ab`` sichert die Abdeckung ab.
"""

import random
from dataclasses import dataclass
from datetime import date, time, timedelta

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Aktivitaet, Lebensbereich
from balanceos.domaene.typen import Aktivitaetsstatus, Bewegungsart
from balanceos.domaene.typen import StandardSchluessel as S

STARTWERT = 46
WOCHEN = 8

MOD = Bewegungsart.AUSDAUER_MODERAT
INT = Bewegungsart.AUSDAUER_INTENSIV
KRAFT = Bewegungsart.KRAFT


@dataclass(frozen=True)
class _Profil:
    """Merkmale einer Demowoche."""

    projekt: bool = False
    hohe_belastung: bool = False
    schlaf_minuten: int = 450
    soziale_minuten: int = 180
    hobby_zufriedenheit: int | None = None
    wochenendarbeit: bool = False
    familie_extra: int = 0
    vorwoche: bool = False


PROFILE = [
    _Profil(),
    _Profil(),
    _Profil(projekt=True, wochenendarbeit=True, soziale_minuten=0),
    _Profil(projekt=True, hohe_belastung=True, soziale_minuten=0),
    _Profil(projekt=True, schlaf_minuten=360, soziale_minuten=0, hobby_zufriedenheit=3),
    _Profil(soziale_minuten=60, hobby_zufriedenheit=5, familie_extra=75),
    _Profil(soziale_minuten=60, vorwoche=True),
    _Profil(soziale_minuten=60),
]


class _Woche:
    """Sammelt die Aktivitäten einer Demowoche."""

    def __init__(
        self,
        kw: KW,
        bereiche: dict[S, Lebensbereich],
        heute: date,
        rng: random.Random,
    ) -> None:
        self.kw = kw
        self.bereiche = bereiche
        self.heute = heute
        self.rng = rng
        self.liste: list[Aktivitaet] = []

    def neu(
        self,
        schluessel: S,
        tag: int,
        titel: str,
        beginn: time | None,
        minuten: int,
        **bewertung,
    ) -> None:
        datum = self.kw.montag() + timedelta(days=tag)
        geplant = datum > self.heute
        bewegungsart = bewertung.pop("bewegungsart", None)
        if geplant:
            bewertung = {}
        ende = None
        if beginn is not None:
            start = timedelta(hours=beginn.hour, minutes=beginn.minute)
            rest = (start + timedelta(minutes=minuten)).seconds
            ende = time(rest // 3600, rest % 3600 // 60)
        self.liste.append(
            Aktivitaet(
                titel=titel,
                lebensbereich_id=self.bereiche[schluessel].id,
                datum=datum,
                dauer_minuten=minuten,
                status=Aktivitaetsstatus.GEPLANT if geplant else Aktivitaetsstatus.DURCHGEFUEHRT,
                beginn=beginn,
                ende=ende,
                bewegungsart=bewegungsart,
                ist_demo=True,
                **bewertung,
            )
        )

    def zufrieden(self, von: int = 3, bis: int = 5) -> int:
        return self.rng.randint(von, bis)


def _verkuerzte_woche(w: _Woche) -> None:
    """Älteste Woche: Einträge nur an drei Tagen (Rückkehr aus dem Urlaub)."""
    for tag in range(3):
        w.neu(S.ARBEIT, tag, "Arbeit im Büro", time(9), 480, belastung=3, erholung=2)
        w.neu(S.SCHLAF, tag, "Schlaf", time(23), 450 + w.rng.randint(-15, 15))
    w.neu(S.FAMILIE, 1, "Abendessen mit der Familie", time(19), 90, zufriedenheit=5)


def _volle_woche(w: _Woche, p: _Profil) -> None:
    rng = w.rng
    for tag in range(7):
        w.neu(S.SCHLAF, tag, "Schlaf", time(23), p.schlaf_minuten + rng.randint(-10, 15))

    # Arbeit und Verpflichtungen
    for tag in range(5):
        if p.projekt:
            belastung = rng.choice([4, 5])
            erholung = rng.choice([1, 2]) if p.hohe_belastung else 2
            minuten = 510 if p.hohe_belastung or p.wochenendarbeit else 480
            w.neu(
                S.ARBEIT,
                tag,
                "Projektarbeit",
                time(8, 30),
                minuten,
                belastung=belastung,
                erholung=erholung,
            )
        else:
            w.neu(
                S.ARBEIT,
                tag,
                "Arbeit im Büro",
                time(9),
                450 + rng.choice([0, 15, 30]),
                belastung=rng.choice([2, 3]),
                erholung=rng.choice([2, 3]),
            )
        w.neu(S.VERPFLICHTUNGEN, tag, "Einkaufen und Haushalt", time(17, 45), 45)
    if p.wochenendarbeit:
        w.neu(
            S.ARBEIT,
            5,
            "Wochenendarbeit für die Projektabgabe",
            time(9),
            300,
            belastung=5,
            erholung=1,
        )
        w.neu(S.VERPFLICHTUNGEN, 6, "Wäsche und Wochenplanung", time(10), 120)
    else:
        w.neu(S.VERPFLICHTUNGEN, 5, "Wocheneinkauf", time(9), 90)

    # Bewegung
    if p.vorwoche:
        w.neu(S.BEWEGUNG, 1, "Joggen im Park", time(18, 30), 45, bewegungsart=MOD, zufriedenheit=4)
        w.neu(S.BEWEGUNG, 3, "Joggen im Park", time(18, 30), 45, bewegungsart=MOD, zufriedenheit=5)
    elif p.projekt:
        w.neu(
            S.BEWEGUNG,
            2,
            "Kurze Laufrunde",
            time(19),
            30,
            bewegungsart=MOD,
            zufriedenheit=w.zufrieden(3, 4),
        )
        w.neu(S.BEWEGUNG, 6, "Radtour", time(14), 50, bewegungsart=INT, zufriedenheit=w.zufrieden())
    else:
        w.neu(
            S.BEWEGUNG,
            0,
            "Krafttraining",
            time(18, 30),
            30,
            bewegungsart=KRAFT,
            zufriedenheit=w.zufrieden(),
        )
        w.neu(
            S.BEWEGUNG,
            1,
            "Joggen im Park",
            time(18, 30),
            45,
            bewegungsart=MOD,
            zufriedenheit=w.zufrieden(),
        )
        w.neu(
            S.BEWEGUNG,
            3,
            "Krafttraining",
            time(18, 30),
            40,
            bewegungsart=KRAFT,
            zufriedenheit=w.zufrieden(),
        )
        w.neu(
            S.BEWEGUNG,
            5,
            "Radtour",
            time(13),
            60,
            bewegungsart=INT,
            zufriedenheit=w.zufrieden(4, 5),
        )

    # Familie
    abend = 45 if p.projekt else 75
    for tag in range(5):
        w.neu(
            S.FAMILIE,
            tag,
            "Abendessen mit der Familie",
            time(19, 15),
            abend,
            zufriedenheit=w.zufrieden(4, 5) if not p.hohe_belastung else None,
        )
    w.neu(
        S.FAMILIE,
        6,
        "Ausflug mit der Familie",
        time(14),
        150 + p.familie_extra * 2,
        zufriedenheit=w.zufrieden(4, 5),
    )
    if not p.projekt:
        w.neu(S.FAMILIE, 5, "Spieleabend", time(19), 120, zufriedenheit=w.zufrieden(4, 5))

    # Hobbys, Freizeit, soziale Kontakte, Entwicklung
    hobby = p.hobby_zufriedenheit
    w.neu(
        S.HOBBYS,
        2,
        "Gitarre üben",
        time(20, 30),
        60,
        zufriedenheit=hobby if hobby else w.zufrieden(),
    )
    w.neu(
        S.HOBBYS,
        6,
        "Fotografieren",
        time(10),
        90 if p.projekt else 120,
        zufriedenheit=hobby if hobby else w.zufrieden(),
    )
    w.neu(S.FREIZEIT, 6, "Filmabend", time(20), 120, zufriedenheit=w.zufrieden())
    w.neu(S.FREIZEIT, 4, "Serienabend", time(21), 60)
    if p.soziale_minuten:
        w.neu(
            S.SOZIALE_KONTAKTE,
            4,
            "Treffen mit Freundinnen",
            time(19, 30),
            p.soziale_minuten,
            zufriedenheit=w.zufrieden(4, 5),
        )
    if not p.hohe_belastung:
        w.neu(
            S.PERSOENLICHE_ENTWICKLUNG,
            1,
            "Online-Kurs Englisch",
            time(20, 30),
            60,
            zufriedenheit=w.zufrieden(3, 4),
        )
    w.neu(S.PERSOENLICHE_ENTWICKLUNG, 6, "Lesen", time(17), 60)

    # Erholung
    if not p.hohe_belastung:
        for tag in (1, 3):
            w.neu(
                S.ERHOLUNG,
                tag,
                "Abendspaziergang",
                time(21, 30),
                30,
                belastung=1,
                erholung=w.zufrieden(4, 5),
            )
    if not p.wochenendarbeit:
        w.neu(
            S.ERHOLUNG,
            5,
            "Sauna",
            time(16),
            120,
            belastung=1,
            erholung=5,
            zufriedenheit=w.zufrieden(4, 5),
        )
        w.neu(
            S.ERHOLUNG,
            6,
            "Ausschlafen und Spaziergang",
            time(9),
            90,
            belastung=1,
            erholung=w.zufrieden(4, 5),
        )


def erzeuge_demodaten(heute: date, bereiche: dict[S, Lebensbereich]) -> list[Aktivitaet]:
    """Erzeugt acht Wochen Demodaten bis einschließlich der aktuellen Woche.

    Args:
        heute: Aktuelles Datum; spätere Tage erhalten nur geplante Aktivitäten
            ohne Bewertungen.
        bereiche: Die zehn Standardbereiche nach Standardschlüssel.

    Returns:
        Aktivitäten mit ``ist_demo = True`` in zeitlicher Reihenfolge.
    """
    rng = random.Random(STARTWERT)
    aktuell = KW.heute(heute)
    ergebnis: list[Aktivitaet] = []
    for nr, profil in enumerate(PROFILE):
        woche = _Woche(aktuell.verschoben(nr - (WOCHEN - 1)), bereiche, heute, rng)
        if nr == 0:
            _verkuerzte_woche(woche)
        else:
            _volle_woche(woche, profil)
        ergebnis += woche.liste
    ergebnis.sort(key=lambda a: (a.datum, a.beginn or time(0), a.titel))
    return ergebnis
