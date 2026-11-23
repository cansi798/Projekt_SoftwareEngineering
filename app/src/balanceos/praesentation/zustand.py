"""Gemeinsamer Oberflächenzustand: gewählte Woche und Änderungssignale."""

from PySide6.QtCore import QObject, Signal

from balanceos.domaene.kalender import KW


class Zustand(QObject):
    """Hält die für alle Seiten gültige Woche und meldet Datenänderungen.

    Jede Seite hört auf ``daten_geaendert`` und ``woche_geaendert`` und lädt
    ihre Anzeige neu. So bleibt die Oberfläche ohne direkte Kopplung der
    Seiten untereinander aktuell.
    """

    daten_geaendert = Signal()
    woche_geaendert = Signal(object)
    seite_angefordert = Signal(int)
    """Bittet das Hauptfenster, die Seite mit diesem Index zu zeigen (0 = Dashboard)."""

    def __init__(self, kw: KW) -> None:
        """Erzeugt den Zustand mit der Startwoche."""
        super().__init__()
        self._kw = kw

    @property
    def kw(self) -> KW:
        """Aktuell gewählte Kalenderwoche."""
        return self._kw

    def setze_kw(self, kw: KW) -> None:
        """Wählt eine andere Woche und benachrichtigt alle Seiten."""
        if kw != self._kw:
            self._kw = kw
            self.woche_geaendert.emit(kw)
