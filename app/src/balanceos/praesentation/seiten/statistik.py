"""Seite „Statistik“: Verlauf der Scores über acht Wochen (US21)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from balanceos.praesentation.seiten.basis import Seite, etikett, karte, scrollbar
from balanceos.praesentation.widgets.liniendiagramm import Liniendiagramm

WOCHEN = 8
GESAMT = "Gesamt-Score (programmeigen)"
GESAMT_FARBE = "#212529"
LEER_TEXT = "Noch keine bewertbaren Wochen."


class StatistikSeite(Seite):
    """Liniendiagramm der Bereichs-Scores und Tabelle Wochen × Bereiche bis zur gewählten KW."""

    titel = "Statistik"

    def __init__(self, kontext, zustand) -> None:
        """Baut Diagramm, Tabelle und Leeransicht auf."""
        super().__init__(kontext, zustand)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stapel = QStackedWidget()
        layout.addWidget(self.stapel)

        self.leer_label = QLabel(LEER_TEXT)
        self.leer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.leer_label.setObjectName("leise")
        self.stapel.addWidget(self.leer_label)

        innen = QWidget()
        spalte = QVBoxLayout(innen)
        rahmen, diagramm_layout = karte("Scores der letzten acht Wochen")
        kopf = QHBoxLayout()
        erklaerung = QLabel(
            "Score 0–100 je Lebensbereich; Wochen mit weniger als vier erfassten Tagen bleiben"
            " leer. Kontrollkästchen blenden Reihen ein und aus."
        )
        erklaerung.setObjectName("leise")
        erklaerung.setWordWrap(True)
        kopf.addWidget(erklaerung, 1)
        kopf.addWidget(etikett("programmeigen, nicht validiert", "#868E96"))
        diagramm_layout.addLayout(kopf)
        self.diagramm = Liniendiagramm()
        self.diagramm.setMinimumHeight(340)
        diagramm_layout.addWidget(self.diagramm)
        spalte.addWidget(rahmen)

        tabelle_rahmen, tabelle_layout = karte("Scores als Tabelle")
        self.tabelle = QTableWidget()
        self.tabelle.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabelle.setMinimumHeight(300)
        tabelle_layout.addWidget(self.tabelle)
        spalte.addWidget(tabelle_rahmen)
        self.inhalt = scrollbar(innen)
        self.stapel.addWidget(self.inhalt)

    def aktualisieren(self) -> None:
        """Berechnet den Verlauf bis zur gewählten Woche und füllt Diagramm und Tabelle."""
        verlauf = self.kontext.auswertung.verlauf(self.zustand.kw, WOCHEN)
        if not any(w.ausreichende_daten for w in verlauf):
            self.stapel.setCurrentWidget(self.leer_label)
            return
        self.stapel.setCurrentWidget(self.inhalt)
        bereiche = self.kontext.stammdaten.aktive_bereiche()
        beschriftungen = [f"KW {w.kw.woche}" for w in verlauf]
        reihen = []
        for b in bereiche:
            werte = []
            for w in verlauf:
                bb = w.bereich(b.id)
                werte.append(bb.score if bb is not None else None)
            reihen.append((b.name, b.farbe, werte))
        gestrichelt = []
        if self.kontext.stammdaten.einstellungen().gesamtscore_anzeigen:
            reihen.append((GESAMT, GESAMT_FARBE, [w.gesamtscore for w in verlauf]))
            gestrichelt.append(GESAMT)
        self.diagramm.setze_reihen(beschriftungen, reihen, gestrichelt)

        self.tabelle.clear()
        self.tabelle.setRowCount(len(verlauf))
        self.tabelle.setColumnCount(len(reihen))
        self.tabelle.setHorizontalHeaderLabels(
            ["Gesamt" if name == GESAMT else name for name, _, _ in reihen]
        )
        self.tabelle.setVerticalHeaderLabels([w.kw.label() for w in verlauf])
        for zeile in range(len(verlauf)):
            for spalte_nr, (_, _, werte) in enumerate(reihen):
                wert = werte[zeile]
                zelle = QTableWidgetItem("–" if wert is None else str(wert))
                zelle.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabelle.setItem(zeile, spalte_nr, zelle)
        self.tabelle.resizeColumnsToContents()
