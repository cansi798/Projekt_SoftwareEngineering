"""Anzeigetexte für Aufzählungswerte in der Oberfläche."""

from html import escape

from balanceos.domaene.typen import Aktivitaetsstatus, Bewegungsart, Evidenzart, Wochentag

STATUS_TEXT: dict[Aktivitaetsstatus, str] = {
    Aktivitaetsstatus.GEPLANT: "Geplant",
    Aktivitaetsstatus.DURCHGEFUEHRT: "Durchgeführt",
    Aktivitaetsstatus.AUSGEFALLEN: "Ausgefallen",
}

BEWEGUNGSART_TEXT: dict[Bewegungsart, str] = {
    Bewegungsart.AUSDAUER_MODERAT: "Ausdauer, moderat",
    Bewegungsart.AUSDAUER_INTENSIV: "Ausdauer, intensiv",
    Bewegungsart.KRAFT: "Kraft",
}

WOCHENTAG_TEXT: dict[Wochentag, str] = {
    Wochentag.MO: "Mo",
    Wochentag.DI: "Di",
    Wochentag.MI: "Mi",
    Wochentag.DO: "Do",
    Wochentag.FR: "Fr",
    Wochentag.SA: "Sa",
    Wochentag.SO: "So",
}

EVIDENZART_TEXT = {
    Evidenzart.THEORIE: "Theorie",
    Evidenzart.EMPFEHLUNG: "Empfehlung",
    Evidenzart.VALIDIERTES_INSTRUMENT: "validiertes Instrument",
    Evidenzart.PERSOENLICHE_REGEL: "persönliche Regel",
    Evidenzart.PROGRAMMEIGEN: "programmeigen",
}
"""Anzeigetexte der Evidenzarten (Balance-Kompass, Begründungsdialog)."""


def als_html(text: str) -> str:
    """Setzt Klartext als HTML-Absatz, damit Qt Zeichen wie „<“ wörtlich anzeigt.

    Rückfragen und Tooltips erkennen HTML automatisch. Ein Titel wie „<b>X</b>“
    würde sonst fett dargestellt. Zeilenumbrüche bleiben als ``<br>`` erhalten.
    """
    return "<p>" + escape(text).replace("\n", "<br>") + "</p>"
