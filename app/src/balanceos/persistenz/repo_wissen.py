"""Repositories für Regeln, Kompass-Modelle, ausgeblendete Hinweise, WHO-5 und Reflexionen."""

import json
from datetime import date

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import KompassModell, Regel, Who5Erhebung, Wochenreflexion
from balanceos.domaene.typen import Evidenzart
from balanceos.persistenz.datenbank import Datenbank


class RegelRepository:
    """Lesen der Regeln und Schalten ihres Aktivzustands (US14)."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    def alle(self) -> list[Regel]:
        """Alle Regeln nach Kennung."""
        return [
            Regel(
                z["kennung"],
                z["bezeichnung"],
                z["modell_schluessel"],
                z["schwelle"],
                z["zeitraum"],
                bool(z["aktiv"]),
            )
            for z in self._db.abfrage("SELECT * FROM regel ORDER BY kennung")
        ]

    def aktiv_setzen(self, kennung: str, aktiv: bool) -> None:
        """Schaltet eine Regel ein oder aus."""
        self._db.ausfuehren("UPDATE regel SET aktiv = ? WHERE kennung = ?", (int(aktiv), kennung))


class KompassRepository:
    """Lesen der Kompass-Modelle (US15)."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    def alle(self) -> list[KompassModell]:
        """Alle Modelle in Anzeigereihenfolge."""
        return [
            KompassModell(
                z["schluessel"],
                z["name"],
                z["kurzbeschreibung"],
                Evidenzart(z["evidenzart"]),
                z["quelle"],
                z["grenzen"],
            )
            for z in self._db.abfrage("SELECT * FROM kompassmodell ORDER BY reihenfolge")
        ]


class AusblendungRepository:
    """Merkt sich weggeklickte Hinweise je Woche (GR24)."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    def ausblenden(self, regel: str, kw: KW, lebensbereich_id: int | None) -> None:
        """Blendet den Hinweis einer Regel für eine Woche (und ggf. einen Bereich) aus."""
        self._db.ausfuehren(
            "INSERT OR IGNORE INTO hinweis_ausblendung VALUES (?, ?, ?, ?)",
            (regel, kw.jahr, kw.woche, lebensbereich_id or 0),
        )

    def ausgeblendet(self, kw: KW) -> set[tuple[str, int | None]]:
        """Paare aus Regel und Lebensbereich, die in der Woche ausgeblendet sind."""
        zeilen = self._db.abfrage(
            "SELECT regel, lebensbereich_id FROM hinweis_ausblendung WHERE jahr = ? AND woche = ?",
            (kw.jahr, kw.woche),
        )
        return {(z["regel"], z["lebensbereich_id"] or None) for z in zeilen}


class Who5Repository:
    """Speichern und Lesen von WHO-5-Erhebungen."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    def speichern(self, e: Who5Erhebung) -> Who5Erhebung:
        """Speichert eine neue Erhebung."""
        cur = self._db.ausfuehren(
            "INSERT INTO who5_erhebung (datum, antworten) VALUES (?, ?)",
            (e.datum.isoformat(), json.dumps(list(e.antworten))),
        )
        e.id = cur.lastrowid
        return e

    def alle(self) -> list[Who5Erhebung]:
        """Alle Erhebungen, neueste zuerst."""
        return [
            Who5Erhebung(date.fromisoformat(z["datum"]), tuple(json.loads(z["antworten"])), z["id"])
            for z in self._db.abfrage("SELECT * FROM who5_erhebung ORDER BY datum DESC, id DESC")
        ]


class ReflexionRepository:
    """Speichern und Lesen von Wochenreflexionen (höchstens eine je Woche, GR27)."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    @staticmethod
    def _aus_zeile(z) -> Wochenreflexion:
        return Wochenreflexion(
            KW(z["jahr"], z["woche"]), tuple(json.loads(z["antworten"])), z["stimmung"], z["id"]
        )

    def fuer_kw(self, kw: KW) -> Wochenreflexion | None:
        """Reflexion der Woche oder ``None``."""
        zeilen = self._db.abfrage(
            "SELECT * FROM wochenreflexion WHERE jahr = ? AND woche = ?", (kw.jahr, kw.woche)
        )
        return self._aus_zeile(zeilen[0]) if zeilen else None

    def alle(self) -> list[Wochenreflexion]:
        """Alle Reflexionen nach Woche."""
        return [
            self._aus_zeile(z)
            for z in self._db.abfrage("SELECT * FROM wochenreflexion ORDER BY jahr, woche")
        ]

    def speichern(self, r: Wochenreflexion) -> None:
        """Legt die Reflexion der Woche an oder ersetzt sie."""
        self._db.ausfuehren(
            "INSERT INTO wochenreflexion (jahr, woche, antworten, stimmung) VALUES (?, ?, ?, ?)"
            " ON CONFLICT(jahr, woche) DO UPDATE SET antworten = excluded.antworten,"
            " stimmung = excluded.stimmung",
            (r.kw.jahr, r.kw.woche, json.dumps(list(r.antworten), ensure_ascii=False), r.stimmung),
        )
