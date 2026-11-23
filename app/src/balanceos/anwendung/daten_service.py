"""Service für Demodaten und das Löschen aller Daten (US17, US18; GR28, GR29)."""

from collections.abc import Callable
from datetime import date

from balanceos.anwendung.demodaten import erzeuge_demodaten
from balanceos.anwendung.fehler import RegelVerletzung, ValidierungsFehler
from balanceos.domaene.typen import StandardSchluessel
from balanceos.domaene.validierung import pruefe_loeschbestaetigung
from balanceos.persistenz.datenbank import Datenbank, alle_nutzdaten_loeschen
from balanceos.persistenz.repo_aktivitaeten import AktivitaetRepository
from balanceos.persistenz.repo_bereiche import LebensbereichRepository

M_DEMO_VORHANDEN = "Demodaten sind bereits geladen."


class DatenService:
    """Laden und Entfernen der Demodaten sowie Zurücksetzen auf den ersten Start."""

    def __init__(
        self,
        db: Datenbank,
        aktivitaeten: AktivitaetRepository,
        bereiche: LebensbereichRepository,
        heute: Callable[[], date],
    ) -> None:
        """Erzeugt den Service."""
        self._db = db
        self._aktivitaeten = aktivitaeten
        self._bereiche = bereiche
        self._heute = heute

    @property
    def datenbankpfad(self) -> str:
        """Speicherort der Datenbank für die Anzeige in den Einstellungen."""
        return str(self._db.pfad)

    def demodaten_vorhanden(self) -> bool:
        """``True``, wenn Demodaten geladen sind."""
        return self._aktivitaeten.gibt_demo()

    def demodaten_laden(self) -> int:
        """Lädt acht Wochen Demodaten zusätzlich zu den vorhandenen Daten (GR28).

        Returns:
            Anzahl der geladenen Aktivitäten.

        Raises:
            RegelVerletzung: wenn bereits Demodaten geladen sind.
        """
        if self.demodaten_vorhanden():
            raise RegelVerletzung(M_DEMO_VORHANDEN)
        bereiche = {s: self._bereiche.nach_schluessel(s) for s in StandardSchluessel}
        daten = erzeuge_demodaten(self._heute(), bereiche)
        self._aktivitaeten.einfuegen_viele(daten)
        return len(daten)

    def demodaten_entfernen(self) -> int:
        """Entfernt ausschließlich Demodaten und liefert deren Anzahl (GR28)."""
        return self._aktivitaeten.loesche_demo()

    def alle_daten_loeschen(self, bestaetigung: str) -> None:
        """Löscht alle Nutzdaten und stellt den Zustand des ersten Starts her (GR29).

        Raises:
            ValidierungsFehler: wenn ``bestaetigung`` nicht genau „LÖSCHEN“ lautet.
        """
        fehler = pruefe_loeschbestaetigung(bestaetigung)
        if fehler:
            raise ValidierungsFehler(fehler)
        alle_nutzdaten_loeschen(self._db)
