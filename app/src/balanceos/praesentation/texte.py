"""Anzeigetexte für Aufzählungswerte in der Oberfläche."""

from balanceos.domaene.typen import Aktivitaetsstatus, Bewegungsart, Wochentag

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
