"""WHO-5-Fragebogen zum Wohlbefinden: Texte und Auswertung (US20, GP06; Topp et al., 2015)."""

from collections.abc import Sequence
from dataclasses import dataclass

AUSSAGEN: tuple[str, ...] = (
    "Ich war froh und guter Laune.",
    "Ich habe mich ruhig und entspannt gefühlt.",
    "Ich habe mich energisch und aktiv gefühlt.",
    "Beim Aufwachen habe ich mich frisch und ausgeruht gefühlt.",
    "Mein Alltag war voller Dinge, die mich interessieren.",
)
"""Die fünf Aussagen, bezogen auf die letzten zwei Wochen."""

SKALA: tuple[str, ...] = (
    "Zu keinem Zeitpunkt",
    "Ab und zu",
    "Etwas weniger als die Hälfte der Zeit",
    "Etwas mehr als die Hälfte der Zeit",
    "Meistens",
    "Die ganze Zeit",
)
"""Antwortstufen; der Index ist der Punktwert 0–5."""

EINLEITUNG = "Die folgenden Aussagen betreffen Ihr Wohlbefinden in den letzten zwei Wochen."

GRENZE_EMPFEHLUNG = 50
"""Bis zu diesem Prozentwert (einschließlich) erscheint der Empfehlungstext (GP06)."""

EMPFEHLUNGSTEXT = (
    "Ihr Ergebnis liegt bei höchstens 50 %. Wenn Sie sich über längere Zeit niedergeschlagen"
    " fühlen, sprechen Sie mit einer Ärztin, einem Arzt oder einer psychotherapeutischen"
    " Fachperson. Das Ergebnis ist keine Diagnose."
)

KEINE_DIAGNOSE = (
    "Der WHO-5 ist ein validiertes Kurzinstrument zum Wohlbefinden. Das Ergebnis ist keine"
    " Diagnose und fließt nicht in die Scores von BalanceOS ein."
)


@dataclass(frozen=True, slots=True)
class Who5Ergebnis:
    """Auswertung einer WHO-5-Erhebung."""

    rohwert: int
    prozentwert: int
    empfehlung: bool


def werte_aus(antworten: Sequence[int]) -> Who5Ergebnis:
    """Berechnet Rohwert (Summe, 0–25) und Prozentwert (Rohwert · 4, 0–100).

    Args:
        antworten: Fünf Antworten mit je 0–5 Punkten (vorher mit ``pruefe_who5`` geprüft).

    Returns:
        Ergebnis; ``empfehlung`` ist gesetzt, wenn der Prozentwert höchstens 50 beträgt.
    """
    rohwert = sum(antworten)
    prozentwert = rohwert * 4
    return Who5Ergebnis(rohwert, prozentwert, prozentwert <= GRENZE_EMPFEHLUNG)
