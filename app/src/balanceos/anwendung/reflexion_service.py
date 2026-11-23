"""Service für WHO-5-Erhebungen und Wochenreflexionen (US20–US22; GR26, GR27)."""

from collections.abc import Callable, Sequence
from datetime import date

from balanceos.anwendung.fehler import ValidierungsFehler
from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Who5Erhebung, Wochenreflexion
from balanceos.domaene.validierung import pruefe_reflexion, pruefe_who5
from balanceos.domaene.who5 import Who5Ergebnis, werte_aus
from balanceos.persistenz.repo_wissen import ReflexionRepository, Who5Repository


class ReflexionService:
    """Speichert WHO-5-Erhebungen und genau eine Reflexion je Kalenderwoche."""

    def __init__(
        self,
        who5: Who5Repository,
        reflexionen: ReflexionRepository,
        heute: Callable[[], date],
    ) -> None:
        """Erzeugt den Service."""
        self._who5 = who5
        self._reflexionen = reflexionen
        self._heute = heute

    def who5_speichern(self, datum: date, antworten: Sequence[int | None]) -> Who5Ergebnis:
        """Prüft, speichert und wertet eine WHO-5-Erhebung aus (GR26, GP06).

        Raises:
            ValidierungsFehler: bei offenen Antworten oder einem Datum in der Zukunft.
        """
        fehler = pruefe_who5(datum, antworten, self._heute())
        if fehler:
            raise ValidierungsFehler(fehler)
        werte = tuple(int(a) for a in antworten)
        self._who5.speichern(Who5Erhebung(datum, werte))
        return werte_aus(werte)

    def who5_verlauf(self) -> list[Who5Erhebung]:
        """Alle Erhebungen, älteste zuerst."""
        return sorted(self._who5.alle(), key=lambda e: (e.datum, e.id or 0))

    def reflexion(self, kw: KW) -> Wochenreflexion | None:
        """Reflexion der Woche oder ``None``."""
        return self._reflexionen.fuer_kw(kw)

    def reflexion_speichern(
        self, kw: KW, antworten: tuple[str, str, str], stimmung: int | None
    ) -> None:
        """Legt die Reflexion der Woche an oder überschreibt sie (GR27).

        Raises:
            ValidierungsFehler: bei Antworten über 1.000 Zeichen oder ungültiger Stimmung.
        """
        fehler = pruefe_reflexion(antworten, stimmung)
        if fehler:
            raise ValidierungsFehler(fehler)
        self._reflexionen.speichern(Wochenreflexion(kw, antworten, stimmung))
