"""Repositories für Aktivitäten, Wiederholungsserien und Ausnahmen."""

import sqlite3
from datetime import date, time

from balanceos.domaene.modell import Aktivitaet, Wiederholungsserie
from balanceos.domaene.typen import Aktivitaetsstatus, Bewegungsart, Wochentag
from balanceos.persistenz.datenbank import Datenbank


def _zeit(text: str | None) -> time | None:
    return time.fromisoformat(text) if text else None


def _datum(text: str | None) -> date | None:
    return date.fromisoformat(text) if text else None


def _text(wert: date | time | None) -> str | None:
    if wert is None:
        return None
    return wert.strftime("%H:%M") if isinstance(wert, time) else wert.isoformat()


def _aktivitaet(z: sqlite3.Row) -> Aktivitaet:
    return Aktivitaet(
        titel=z["titel"],
        lebensbereich_id=z["lebensbereich_id"],
        datum=date.fromisoformat(z["datum"]),
        dauer_minuten=z["dauer_minuten"],
        status=Aktivitaetsstatus(z["status"]),
        beginn=_zeit(z["beginn"]),
        ende=_zeit(z["ende"]),
        zufriedenheit=z["zufriedenheit"],
        belastung=z["belastung"],
        erholung=z["erholung"],
        bewegungsart=Bewegungsart(z["bewegungsart"]) if z["bewegungsart"] else None,
        notiz=z["notiz"],
        ist_demo=bool(z["ist_demo"]),
        serie_id=z["serie_id"],
        einzeln_bearbeitet=bool(z["einzeln_bearbeitet"]),
        id=z["id"],
    )


_SPALTEN = (
    "titel, lebensbereich_id, datum, beginn, ende, dauer_minuten, status, zufriedenheit,"
    " belastung, erholung, bewegungsart, notiz, ist_demo, serie_id, einzeln_bearbeitet"
)
_SORTIERUNG = "ORDER BY datum, beginn IS NULL, beginn, id"


def _werte(a: Aktivitaet) -> tuple:
    return (
        a.titel,
        a.lebensbereich_id,
        a.datum.isoformat(),
        _text(a.beginn),
        _text(a.ende),
        a.dauer_minuten,
        a.status,
        a.zufriedenheit,
        a.belastung,
        a.erholung,
        a.bewegungsart,
        a.notiz,
        int(a.ist_demo),
        a.serie_id,
        int(a.einzeln_bearbeitet),
    )


class AktivitaetRepository:
    """Lesen und Schreiben von Aktivitäten."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    def im_zeitraum(self, von: date, bis: date) -> list[Aktivitaet]:
        """Aktivitäten mit Datum von ``von`` bis ``bis`` (jeweils einschließlich)."""
        zeilen = self._db.abfrage(
            f"SELECT * FROM aktivitaet WHERE datum BETWEEN ? AND ? {_SORTIERUNG}",
            (von.isoformat(), bis.isoformat()),
        )
        return [_aktivitaet(z) for z in zeilen]

    def alle(self) -> list[Aktivitaet]:
        """Alle Aktivitäten, sortiert nach Datum und Beginn."""
        return [_aktivitaet(z) for z in self._db.abfrage(f"SELECT * FROM aktivitaet {_SORTIERUNG}")]

    def nach_id(self, aktivitaet_id: int) -> Aktivitaet | None:
        """Aktivität mit der angegebenen ID oder ``None``."""
        zeilen = self._db.abfrage("SELECT * FROM aktivitaet WHERE id = ?", (aktivitaet_id,))
        return _aktivitaet(zeilen[0]) if zeilen else None

    def speichern(self, a: Aktivitaet) -> Aktivitaet:
        """Fügt eine Aktivität ein oder aktualisiert sie."""
        with self._db.transaktion() as con:
            if a.id is None:
                cur = con.execute(
                    f"INSERT INTO aktivitaet ({_SPALTEN}) VALUES ({', '.join('?' * 15)})",
                    _werte(a),
                )
                a.id = cur.lastrowid
            else:
                zuweisung = ", ".join(f"{s.strip()} = ?" for s in _SPALTEN.split(","))
                con.execute(f"UPDATE aktivitaet SET {zuweisung} WHERE id = ?", (*_werte(a), a.id))
        return a

    def einfuegen_viele(self, aktivitaeten: list[Aktivitaet]) -> None:
        """Fügt viele neue Aktivitäten in einer Transaktion ein (Demodaten, Serien)."""
        with self._db.transaktion() as con:
            for a in aktivitaeten:
                cur = con.execute(
                    f"INSERT INTO aktivitaet ({_SPALTEN}) VALUES ({', '.join('?' * 15)})",
                    _werte(a),
                )
                a.id = cur.lastrowid

    def loeschen(self, aktivitaet_id: int) -> None:
        """Löscht eine Aktivität."""
        self._db.ausfuehren("DELETE FROM aktivitaet WHERE id = ?", (aktivitaet_id,))

    def termine_der_serie(self, serie_id: int) -> list[Aktivitaet]:
        """Alle Termine einer Serie."""
        zeilen = self._db.abfrage(
            f"SELECT * FROM aktivitaet WHERE serie_id = ? {_SORTIERUNG}", (serie_id,)
        )
        return [_aktivitaet(z) for z in zeilen]

    def gibt_demo(self) -> bool:
        """``True``, wenn Demodaten geladen sind."""
        zeilen = self._db.abfrage("SELECT EXISTS(SELECT 1 FROM aktivitaet WHERE ist_demo)")
        return bool(zeilen[0][0])

    def loesche_demo(self) -> int:
        """Löscht alle Demo-Aktivitäten und liefert ihre Anzahl (GR28)."""
        return self._db.ausfuehren("DELETE FROM aktivitaet WHERE ist_demo = 1").rowcount


def _serie(z: sqlite3.Row, ausnahmen: set[date]) -> Wiederholungsserie:
    return Wiederholungsserie(
        titel=z["titel"],
        lebensbereich_id=z["lebensbereich_id"],
        wochentage=frozenset(Wochentag(t) for t in z["wochentage"].split(",") if t),
        startdatum=date.fromisoformat(z["startdatum"]),
        dauer_minuten=z["dauer_minuten"],
        enddatum=_datum(z["enddatum"]),
        beginn=_zeit(z["beginn"]),
        ausnahmen=ausnahmen,
        generiert_bis=_datum(z["generiert_bis"]),
        id=z["id"],
    )


class SerieRepository:
    """Lesen und Schreiben von Wiederholungsserien samt Ausnahmen."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    def _ausnahmen(self, serie_id: int) -> set[date]:
        zeilen = self._db.abfrage("SELECT datum FROM ausnahme WHERE serie_id = ?", (serie_id,))
        return {date.fromisoformat(z["datum"]) for z in zeilen}

    def alle(self) -> list[Wiederholungsserie]:
        """Alle Serien."""
        zeilen = self._db.abfrage("SELECT * FROM wiederholungsserie ORDER BY id")
        return [_serie(z, self._ausnahmen(z["id"])) for z in zeilen]

    def nach_id(self, serie_id: int) -> Wiederholungsserie | None:
        """Serie mit der angegebenen ID oder ``None``."""
        zeilen = self._db.abfrage("SELECT * FROM wiederholungsserie WHERE id = ?", (serie_id,))
        return _serie(zeilen[0], self._ausnahmen(serie_id)) if zeilen else None

    def speichern(self, s: Wiederholungsserie) -> Wiederholungsserie:
        """Fügt eine Serie ein oder aktualisiert sie; die Ausnahmen werden mitgeschrieben."""
        tage = ",".join(t.value for t in sorted(s.wochentage, key=lambda t: t.index))
        werte = (
            s.titel,
            s.lebensbereich_id,
            tage,
            s.startdatum.isoformat(),
            _text(s.enddatum),
            _text(s.beginn),
            s.dauer_minuten,
            _text(s.generiert_bis),
        )
        with self._db.transaktion() as con:
            if s.id is None:
                cur = con.execute(
                    "INSERT INTO wiederholungsserie (titel, lebensbereich_id, wochentage,"
                    " startdatum, enddatum, beginn, dauer_minuten, generiert_bis)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    werte,
                )
                s.id = cur.lastrowid
            else:
                con.execute(
                    "UPDATE wiederholungsserie SET titel = ?, lebensbereich_id = ?,"
                    " wochentage = ?, startdatum = ?, enddatum = ?, beginn = ?,"
                    " dauer_minuten = ?, generiert_bis = ? WHERE id = ?",
                    (*werte, s.id),
                )
                con.execute("DELETE FROM ausnahme WHERE serie_id = ?", (s.id,))
            con.executemany(
                "INSERT INTO ausnahme VALUES (?, ?)",
                [(s.id, d.isoformat()) for d in sorted(s.ausnahmen)],
            )
        return s

    def loeschen(self, serie_id: int) -> None:
        """Löscht eine Serie; ihre Ausnahmen werden mitgelöscht, Termine entkoppelt."""
        self._db.ausfuehren("DELETE FROM wiederholungsserie WHERE id = ?", (serie_id,))
