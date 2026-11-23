"""Anwendungskontext: verdrahtet Datenbank, Repositories und Services."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from balanceos.anwendung.aktivitaet_service import AktivitaetService
from balanceos.anwendung.auswertung_service import AuswertungService
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
    aktivitaeten: AktivitaetService
    auswertung: AuswertungService

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
        kontext = cls(
            db=db,
            heute=heute,
            repos=r,
            stammdaten=StammdatenService(r.bereiche, r.einstellungen),
            aktivitaeten=AktivitaetService(r.aktivitaeten, r.serien, r.bereiche, db, heute),
            auswertung=AuswertungService(
                r.aktivitaeten,
                r.bereiche,
                r.einstellungen,
                r.regeln,
                r.kompass,
                r.ausblendungen,
                db,
            ),
        )
        kontext.aktivitaeten.horizont_fortschreiben()
        return kontext
