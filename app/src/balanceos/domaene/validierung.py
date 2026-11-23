"""Prüfung von Eingaben gegen Geschäftsregeln und Gültigkeitsregeln der Eingabefelder."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Fehler:
    """Ein Verstoß gegen eine Gültigkeitsregel mit Feldbezug und Meldung."""

    feld: str
    meldung: str
