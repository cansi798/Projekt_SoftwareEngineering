"""Anwendungskontext: verdrahtet Datenbank, Repositories und Services."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from balanceos.persistenz.datenbank import Datenbank
from balanceos.persistenz.stammdaten import initialisiere


@dataclass
class AppKontext:
    """Bündelt alle Services; die Oberfläche greift nur über diesen Kontext zu."""

    db: Datenbank
    heute: Callable[[], date]
    stammdaten: Any = None
    aktivitaeten: Any = None
    auswertung: Any = None
    export: Any = None
    daten: Any = None
    reflexion: Any = None

    @classmethod
    def erstellen(cls, pfad: Path | str, heute: Callable[[], date] = date.today) -> "AppKontext":
        """Öffnet die Datenbank, legt Stammdaten an und erzeugt alle Services.

        Args:
            pfad: Datenbankdatei oder ``":memory:"``.
            heute: Liefert das aktuelle Datum; in Tests fest vorgegeben.
        """
        db = Datenbank(pfad)
        initialisiere(db)
        return cls(db=db, heute=heute)
