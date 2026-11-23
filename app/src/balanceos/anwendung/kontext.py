"""Anwendungskontext: verdrahtet Datenbank, Repositories und Services."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from balanceos.anwendung.stammdaten_service import StammdatenService
from balanceos.persistenz.datenbank import Datenbank
from balanceos.persistenz.repo_aktivitaeten import AktivitaetRepository, SerieRepository
from balanceos.persistenz.repo_bereiche import EinstellungenRepository, LebensbereichRepository
from balanceos.persistenz.repo_wissen import (
    AusblendungRepository,
    KompassRepository,
    ReflexionRepository,
    RegelRepository,
    Who5Repository,
)
from balanceos.persistenz.stammdaten import initialisiere


@dataclass
class Repositories:
    """Alle Repositories einer Datenbank."""

    bereiche: LebensbereichRepository
    einstellungen: EinstellungenRepository
    aktivitaeten: AktivitaetRepository
    serien: SerieRepository
    regeln: RegelRepository
    kompass: KompassRepository
    ausblendungen: AusblendungRepository
    who5: Who5Repository
    reflexionen: ReflexionRepository

    @classmethod
    def fuer(cls, db: Datenbank) -> "Repositories":
        """Erzeugt alle Repositories für eine Datenbank."""
        return cls(
            LebensbereichRepository(db),
            EinstellungenRepository(db),
            AktivitaetRepository(db),
            SerieRepository(db),
            RegelRepository(db),
            KompassRepository(db),
            AusblendungRepository(db),
            Who5Repository(db),
            ReflexionRepository(db),
        )


@dataclass
class AppKontext:
    """Bündelt Datenbank, Repositories und Services.

    Die Oberfläche verwendet ausschließlich die Services; die Repositories sind
    für Tests und für die Verdrahtung zugänglich.
    """

    db: Datenbank
    heute: Callable[[], date]
    repos: Repositories
    stammdaten: StammdatenService

    @classmethod
    def erstellen(cls, pfad: Path | str, heute: Callable[[], date] = date.today) -> "AppKontext":
        """Öffnet die Datenbank, legt Stammdaten an und erzeugt alle Services.

        Args:
            pfad: Datenbankdatei oder ``":memory:"``.
            heute: Liefert das aktuelle Datum; in Tests fest vorgegeben.
        """
        db = Datenbank(pfad)
        initialisiere(db)
        r = Repositories.fuer(db)
        return cls(
            db=db,
            heute=heute,
            repos=r,
            stammdaten=StammdatenService(r.bereiche, r.einstellungen),
        )
