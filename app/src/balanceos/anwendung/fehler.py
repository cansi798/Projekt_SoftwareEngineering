"""Fehlerklassen der Anwendungsschicht."""

from balanceos.domaene.validierung import Fehler


class ValidierungsFehler(Exception):
    """Eingaben verletzen Gültigkeitsregeln; enthält je Feld eine Meldung."""

    def __init__(self, fehler: list[Fehler]) -> None:
        """Erzeugt den Fehler aus einer nicht leeren Liste von Feldfehlern."""
        super().__init__("; ".join(f.meldung for f in fehler))
        self.fehler = fehler

    def meldung_fuer(self, feld: str) -> str | None:
        """Meldung zu einem Feld oder ``None``."""
        return next((f.meldung for f in self.fehler if f.feld == feld), None)


class RegelVerletzung(Exception):
    """Eine Aktion verletzt eine Geschäftsregel ohne Bezug zu einem Eingabefeld."""
