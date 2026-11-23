"""Repositories für Lebensbereiche und Einstellungen."""

import sqlite3

from balanceos.domaene.modell import Einstellungen, Lebensbereich
from balanceos.domaene.typen import Bereichstyp, StandardSchluessel
from balanceos.persistenz.datenbank import Datenbank


def _bereich(zeile: sqlite3.Row) -> Lebensbereich:
    schluessel = zeile["standard_schluessel"]
    return Lebensbereich(
        name=zeile["name"],
        typ=Bereichstyp(zeile["typ"]),
        farbe=zeile["farbe"],
        soll_stunden=zeile["soll_stunden"],
        gewicht=zeile["gewicht"],
        aktiv=bool(zeile["aktiv"]),
        standard_schluessel=StandardSchluessel(schluessel) if schluessel else None,
        id=zeile["id"],
    )


class LebensbereichRepository:
    """Lesen und Schreiben von Lebensbereichen."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    def alle(self) -> list[Lebensbereich]:
        """Alle Bereiche: Standardbereiche in fester Reihenfolge, dann eigene nach Name."""
        zeilen = self._db.abfrage(
            "SELECT * FROM lebensbereich ORDER BY reihenfolge, name COLLATE NOCASE"
        )
        return [_bereich(z) for z in zeilen]

    def nach_id(self, bereich_id: int) -> Lebensbereich | None:
        """Bereich mit der angegebenen ID oder ``None``."""
        zeilen = self._db.abfrage("SELECT * FROM lebensbereich WHERE id = ?", (bereich_id,))
        return _bereich(zeilen[0]) if zeilen else None

    def nach_schluessel(self, schluessel: StandardSchluessel) -> Lebensbereich | None:
        """Standardbereich mit dem angegebenen Schlüssel (auch wenn er umbenannt wurde)."""
        zeilen = self._db.abfrage(
            "SELECT * FROM lebensbereich WHERE standard_schluessel = ?", (schluessel,)
        )
        return _bereich(zeilen[0]) if zeilen else None

    def speichern(self, b: Lebensbereich) -> Lebensbereich:
        """Fügt einen neuen Bereich ein oder aktualisiert einen bestehenden."""
        werte = (b.name, b.typ, b.farbe, b.soll_stunden, b.gewicht, int(b.aktiv))
        with self._db.transaktion() as con:
            if b.id is None:
                cur = con.execute(
                    "INSERT INTO lebensbereich (name, typ, farbe, soll_stunden, gewicht, aktiv,"
                    " standard_schluessel) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (*werte, b.standard_schluessel),
                )
                b.id = cur.lastrowid
            else:
                con.execute(
                    "UPDATE lebensbereich SET name = ?, typ = ?, farbe = ?, soll_stunden = ?,"
                    " gewicht = ?, aktiv = ? WHERE id = ?",
                    (*werte, b.id),
                )
        return b

    def loeschen(self, bereich_id: int) -> None:
        """Löscht einen Bereich endgültig."""
        self._db.ausfuehren("DELETE FROM lebensbereich WHERE id = ?", (bereich_id,))

    def hat_zuordnungen(self, bereich_id: int) -> bool:
        """``True``, wenn dem Bereich Aktivitäten oder Serien zugeordnet sind (GR04)."""
        zeilen = self._db.abfrage(
            "SELECT EXISTS(SELECT 1 FROM aktivitaet WHERE lebensbereich_id = ?)"
            " OR EXISTS(SELECT 1 FROM wiederholungsserie WHERE lebensbereich_id = ?)",
            (bereich_id, bereich_id),
        )
        return bool(zeilen[0][0])


class EinstellungenRepository:
    """Lesen und Schreiben der einmaligen Einstellungen."""

    def __init__(self, db: Datenbank) -> None:
        """Erzeugt das Repository für die übergebene Datenbank."""
        self._db = db

    def laden(self) -> Einstellungen:
        """Aktuelle Einstellungen."""
        zeile = self._db.abfrage("SELECT * FROM einstellungen WHERE id = 1")[0]
        return Einstellungen(zeile["alpha"], bool(zeile["gesamtscore_anzeigen"]))

    def speichern(self, e: Einstellungen) -> None:
        """Speichert die Einstellungen."""
        self._db.ausfuehren(
            "UPDATE einstellungen SET alpha = ?, gesamtscore_anzeigen = ? WHERE id = 1",
            (e.alpha, int(e.gesamtscore_anzeigen)),
        )
