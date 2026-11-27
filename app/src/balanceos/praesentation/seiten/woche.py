"""Seite „Woche“: Kalenderansicht der gewählten Woche (US09)."""

import html

from PySide6.QtWidgets import QLabel, QVBoxLayout

from balanceos.domaene.kalender import stunden_text
from balanceos.domaene.typen import Aktivitaetsstatus
from balanceos.praesentation.dialoge.aktivitaet import aktivitaet_bearbeiten
from balanceos.praesentation.seiten.basis import Seite, scrollbar
from balanceos.praesentation.widgets.wochenkalender import Wochenkalender


class WocheSeite(Seite):
    """Wochenkalender mit Legende; Doppelklick erfasst oder bearbeitet Aktivitäten."""

    titel = "Woche"

    def __init__(self, kontext, zustand) -> None:
        """Baut Kalender, Legende und Zusammenfassung auf."""
        super().__init__(kontext, zustand)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        self.legende = QLabel()
        self.legende.setWordWrap(True)
        layout.addWidget(self.legende)
        self.summe_label = QLabel()
        self.summe_label.setObjectName("leise")
        self.summe_label.setWordWrap(True)
        layout.addWidget(self.summe_label)
        self.kalender = Wochenkalender()
        layout.addWidget(scrollbar(self.kalender), 1)
        self.kalender.aktivitaet_doppelklick.connect(self._bearbeiten)
        self.kalender.freie_flaeche_doppelklick.connect(self._neu)

    def aktualisieren(self) -> None:
        """Lädt die Aktivitäten der gewählten Woche."""
        kw = self.zustand.kw
        bereiche = self.kontext.stammdaten.alle_bereiche()
        aktivitaeten = self.kontext.aktivitaeten.fuer_woche(kw)
        # Überlauf vom Sonntag der Vorwoche nur zeichnen, nicht zählen (GR11).
        ueberlauf = self.kontext.aktivitaeten.ueberlauf_aus_vorwoche(kw)
        self.kalender.setze(
            kw,
            ueberlauf + aktivitaeten,
            {b.id: b.farbe for b in bereiche},
            self.kontext.heute(),
            {b.id: b.name for b in bereiche},
        )
        self.legende.setText(
            "&nbsp;&nbsp; ".join(
                f'<span style="color:{b.farbe}">&#9679;</span>&nbsp;{html.escape(b.name)}'
                for b in bereiche
                if b.aktiv
            )
        )
        durchgefuehrt = sum(
            a.dauer_minuten for a in aktivitaeten if a.status is Aktivitaetsstatus.DURCHGEFUEHRT
        )
        anzahl = len(aktivitaeten)
        self.summe_label.setText(
            f"{anzahl} {'Aktivität' if anzahl == 1 else 'Aktivitäten'}"
            f" · {stunden_text(durchgefuehrt / 60)} durchgeführt"
            " · Doppelklick auf eine freie Stelle erfasst eine Aktivität,"
            " Doppelklick auf einen Block bearbeitet sie."
        )

    def _bearbeiten(self, aktivitaet_id: int) -> None:
        aktivitaet_bearbeiten(self.kontext, self.zustand, aktivitaet_id, parent=self)

    def _neu(self, tag, zeit) -> None:
        aktivitaet_bearbeiten(self.kontext, self.zustand, datum=tag, beginn=zeit, parent=self)
