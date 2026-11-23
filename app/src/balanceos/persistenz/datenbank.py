"""Verbindung zur SQLite-Datenbank, Transaktionen und Schema.

Jede bestätigte Änderung wird in einer eigenen Transaktion sofort
geschrieben (NFA04). ``synchronous=FULL`` sorgt dafür, dass eine
abgeschlossene Transaktion auch nach einem Absturz erhalten bleibt.
"""

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    schluessel TEXT PRIMARY KEY,
    wert TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS lebensbereich (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    typ TEXT NOT NULL,
    farbe TEXT NOT NULL,
    soll_stunden REAL NOT NULL,
    gewicht INTEGER NOT NULL DEFAULT 1,
    aktiv INTEGER NOT NULL DEFAULT 1,
    standard_schluessel TEXT UNIQUE,
    reihenfolge INTEGER NOT NULL DEFAULT 100
);
CREATE TABLE IF NOT EXISTS wiederholungsserie (
    id INTEGER PRIMARY KEY,
    titel TEXT NOT NULL,
    lebensbereich_id INTEGER NOT NULL REFERENCES lebensbereich(id),
    wochentage TEXT NOT NULL,
    startdatum TEXT NOT NULL,
    enddatum TEXT,
    beginn TEXT,
    dauer_minuten INTEGER NOT NULL,
    generiert_bis TEXT,
    bewegungsart TEXT
);
CREATE TABLE IF NOT EXISTS ausnahme (
    serie_id INTEGER NOT NULL REFERENCES wiederholungsserie(id) ON DELETE CASCADE,
    datum TEXT NOT NULL,
    UNIQUE (serie_id, datum)
);
CREATE TABLE IF NOT EXISTS aktivitaet (
    id INTEGER PRIMARY KEY,
    titel TEXT NOT NULL,
    lebensbereich_id INTEGER NOT NULL REFERENCES lebensbereich(id),
    datum TEXT NOT NULL,
    beginn TEXT,
    ende TEXT,
    dauer_minuten INTEGER NOT NULL,
    status TEXT NOT NULL,
    zufriedenheit INTEGER,
    belastung INTEGER,
    erholung INTEGER,
    bewegungsart TEXT,
    notiz TEXT,
    ist_demo INTEGER NOT NULL DEFAULT 0,
    serie_id INTEGER REFERENCES wiederholungsserie(id) ON DELETE SET NULL,
    einzeln_bearbeitet INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_aktivitaet_datum ON aktivitaet(datum);
CREATE INDEX IF NOT EXISTS ix_aktivitaet_serie ON aktivitaet(serie_id);
CREATE TABLE IF NOT EXISTS kompassmodell (
    schluessel TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kurzbeschreibung TEXT NOT NULL,
    evidenzart TEXT NOT NULL,
    quelle TEXT NOT NULL,
    grenzen TEXT NOT NULL,
    reihenfolge INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS regel (
    kennung TEXT PRIMARY KEY,
    bezeichnung TEXT NOT NULL,
    modell_schluessel TEXT NOT NULL REFERENCES kompassmodell(schluessel),
    schwelle REAL NOT NULL,
    zeitraum INTEGER NOT NULL,
    aktiv INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS einstellungen (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    alpha REAL NOT NULL,
    gesamtscore_anzeigen INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS hinweis_ausblendung (
    regel TEXT NOT NULL,
    jahr INTEGER NOT NULL,
    woche INTEGER NOT NULL,
    lebensbereich_id INTEGER NOT NULL DEFAULT 0,
    UNIQUE (regel, jahr, woche, lebensbereich_id)
);
CREATE TABLE IF NOT EXISTS who5_erhebung (
    id INTEGER PRIMARY KEY,
    datum TEXT NOT NULL,
    antworten TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS wochenreflexion (
    id INTEGER PRIMARY KEY,
    jahr INTEGER NOT NULL,
    woche INTEGER NOT NULL,
    antworten TEXT NOT NULL,
    stimmung INTEGER,
    UNIQUE (jahr, woche)
);
"""

NUTZTABELLEN = (
    "aktivitaet",
    "ausnahme",
    "wiederholungsserie",
    "hinweis_ausblendung",
    "who5_erhebung",
    "wochenreflexion",
    "regel",
    "kompassmodell",
    "einstellungen",
    "lebensbereich",
)
"""Alle Tabellen außer ``meta`` in einer Reihenfolge, die Fremdschlüssel respektiert."""


def standardpfad() -> Path:
    """Pfad der Datenbankdatei im Benutzerprofil (Ordner ``BalanceOS`` unter ``%APPDATA%``).

    Der Ordner wird bei Bedarf angelegt.
    """
    basis = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    ordner = Path(basis) / "BalanceOS"
    ordner.mkdir(parents=True, exist_ok=True)
    return ordner / "balanceos.db"


class Datenbank:
    """Verbindung zur Datenbank mit Transaktionssteuerung."""

    def __init__(self, pfad: Path | str) -> None:
        """Öffnet die Datenbank und legt bei Bedarf das Schema an.

        Args:
            pfad: Dateipfad oder ``":memory:"`` für eine flüchtige Datenbank (Tests).
        """
        self.pfad = str(pfad)
        self.verbindung = sqlite3.connect(self.pfad, isolation_level=None)
        self.verbindung.row_factory = sqlite3.Row
        self.verbindung.execute("PRAGMA foreign_keys = ON")
        if self.pfad != ":memory:":
            self.verbindung.execute("PRAGMA journal_mode = WAL")
        self.verbindung.execute("PRAGMA synchronous = FULL")
        self._tiefe = 0
        # Bewusst kein executescript(): es würde eine laufende Transaktion committen.
        with self.transaktion() as con:
            for anweisung in SCHEMA.split(";"):
                if anweisung.strip():
                    con.execute(anweisung)
            con.execute(
                "INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),)
            )

    @contextmanager
    def transaktion(self) -> Iterator[sqlite3.Connection]:
        """Führt den Block in einer Transaktion aus (Commit bei Erfolg, sonst Rollback).

        Verschachtelte Aufrufe werden in die äußere Transaktion eingebunden.
        """
        aussen = self._tiefe == 0
        if aussen:
            self.verbindung.execute("BEGIN IMMEDIATE")
        self._tiefe += 1
        try:
            yield self.verbindung
        except BaseException:
            self._tiefe -= 1
            if aussen:
                self.verbindung.execute("ROLLBACK")
            raise
        self._tiefe -= 1
        if aussen:
            self.verbindung.execute("COMMIT")

    def abfrage(self, sql: str, parameter: tuple = ()) -> list[sqlite3.Row]:
        """Führt eine lesende Abfrage aus und liefert alle Zeilen."""
        return self.verbindung.execute(sql, parameter).fetchall()

    def ausfuehren(self, sql: str, parameter: tuple = ()) -> sqlite3.Cursor:
        """Führt eine schreibende Anweisung in einer Transaktion aus."""
        with self.transaktion() as con:
            return con.execute(sql, parameter)

    def schliessen(self) -> None:
        """Schließt die Verbindung."""
        self.verbindung.close()


def alle_nutzdaten_loeschen(db: Datenbank) -> None:
    """Entfernt alle Daten und stellt den Zustand des ersten Starts her (GR29)."""
    from balanceos.persistenz.stammdaten import initialisiere

    with db.transaktion() as con:
        for tabelle in NUTZTABELLEN:
            con.execute(f"DELETE FROM {tabelle}")  # noqa: S608 – feste Tabellennamen
        initialisiere(db)
    if db.pfad != ":memory:":
        db.verbindung.execute("VACUUM")
