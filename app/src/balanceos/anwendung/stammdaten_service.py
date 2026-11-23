"""Service für Lebensbereiche, Wunschprofil und Einstellungen (US01–US04, US19)."""

from balanceos.anwendung.fehler import RegelVerletzung, ValidierungsFehler
from balanceos.domaene.modell import Einstellungen, Lebensbereich
from balanceos.domaene.validierung import pruefe_alpha, pruefe_lebensbereich
from balanceos.persistenz.repo_bereiche import EinstellungenRepository, LebensbereichRepository
from balanceos.persistenz.stammdaten import FARBPALETTE

M_STANDARD_LOESCHEN = "Standardbereiche können nicht gelöscht, nur deaktiviert werden."
M_GENUTZT_LOESCHEN = "Dieser Bereich wird verwendet und kann nur deaktiviert werden."


class StammdatenService:
    """Pflege der Lebensbereiche und der Bewertungseinstellungen."""

    def __init__(
        self, bereiche: LebensbereichRepository, einstellungen: EinstellungenRepository
    ) -> None:
        """Erzeugt den Service mit seinen Repositories."""
        self._bereiche = bereiche
        self._einstellungen = einstellungen

    def alle_bereiche(self) -> list[Lebensbereich]:
        """Alle Lebensbereiche in Anzeigereihenfolge."""
        return self._bereiche.alle()

    def aktive_bereiche(self) -> list[Lebensbereich]:
        """Nur aktive Lebensbereiche (Auswahl für neue Aktivitäten, GR05)."""
        return [b for b in self._bereiche.alle() if b.aktiv]

    def bereich(self, bereich_id: int) -> Lebensbereich | None:
        """Lebensbereich mit der angegebenen ID."""
        return self._bereiche.nach_id(bereich_id)

    def speichern(self, b: Lebensbereich) -> Lebensbereich:
        """Speichert einen neuen oder geänderten Bereich nach Prüfung der Regeln.

        Raises:
            ValidierungsFehler: bei Verstößen gegen GR01, GR02, GR06 oder GR07.
        """
        b.name = b.name.strip()
        fehler = pruefe_lebensbereich(b, self._bereiche.alle())
        if fehler:
            raise ValidierungsFehler(fehler)
        return self._bereiche.speichern(b)

    def loeschen(self, bereich_id: int) -> None:
        """Löscht einen eigenen, nicht verwendeten Bereich.

        Raises:
            RegelVerletzung: bei Standardbereichen (GR03) oder verwendeten Bereichen (GR04).
        """
        if self._bereiche.nach_id(bereich_id) is None:
            return
        self.loeschen_pruefen(bereich_id)
        self._bereiche.loeschen(bereich_id)

    def loeschen_pruefen(self, bereich_id: int) -> None:
        """Prüft, ob ein Bereich gelöscht werden darf, ohne ihn zu löschen.

        Raises:
            RegelVerletzung: mit derselben Meldung wie :meth:`loeschen`.
        """
        b = self._bereiche.nach_id(bereich_id)
        if b is None:
            return
        if b.ist_standard:
            raise RegelVerletzung(M_STANDARD_LOESCHEN)
        if self._bereiche.hat_zuordnungen(bereich_id):
            raise RegelVerletzung(M_GENUTZT_LOESCHEN)
        rest = [x for x in self._bereiche.alle() if x.id != bereich_id]
        if not any(x.aktiv and x.soll_stunden > 0 for x in rest):
            raise RegelVerletzung("Mindestens ein aktiver Bereich braucht ein Soll.")

    @staticmethod
    def farbpalette() -> list[str]:
        """Die zwölf Auswahlfarben für Lebensbereiche."""
        return list(FARBPALETTE)

    def verplante_stunden(self) -> float:
        """Summe der Soll-Stunden aller aktiven Bereiche."""
        return sum(b.soll_stunden for b in self._bereiche.alle() if b.aktiv)

    def einstellungen(self) -> Einstellungen:
        """Aktuelle Bewertungseinstellungen."""
        return self._einstellungen.laden()

    def einstellungen_speichern(self, e: Einstellungen) -> None:
        """Speichert die Einstellungen nach Prüfung von GR08."""
        fehler = pruefe_alpha(e.alpha)
        if fehler:
            raise ValidierungsFehler(fehler)
        self._einstellungen.speichern(e)
