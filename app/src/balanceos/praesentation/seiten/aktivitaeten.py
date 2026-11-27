"""Seite „Aktivitäten“: tabellarische Liste der gewählten Woche (US05, US06, US08)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from balanceos.anwendung.fehler import RegelVerletzung
from balanceos.domaene.kalender import stunden_text
from balanceos.domaene.modell import Aktivitaet
from balanceos.domaene.typen import Aktivitaetsstatus, Wochentag
from balanceos.praesentation.dialoge.aktivitaet import aktivitaet_bearbeiten
from balanceos.praesentation.seiten.basis import Seite
from balanceos.praesentation.texte import STATUS_TEXT, WOCHENTAG_TEXT, als_html
from balanceos.praesentation.widgets.auswahl import Auswahl

SPALTEN = ["Datum", "Zeit", "Lebensbereich", "Titel", "Dauer", "Status", "Demo", "Serie"]


def _ueberspringbar(a: Aktivitaet | None) -> bool:
    """Nur geplante Termine einer Serie lassen sich überspringen (US08, GP02).

    Durchgeführte oder ausgefallene Termine tragen Bewertungen und Notizen;
    sie werden über „Löschen“ mit Rückfrage entfernt, nicht übersprungen.
    """
    return a is not None and a.serie_id is not None and a.status is Aktivitaetsstatus.GEPLANT


class AktivitaetenSeite(Seite):
    """Liste der Aktivitäten der gewählten Woche mit Filtern nach Bereich und Status."""

    titel = "Aktivitäten"

    def __init__(self, kontext, zustand) -> None:
        """Baut Filterzeile, Tabelle und Schaltflächen auf."""
        super().__init__(kontext, zustand)
        self._aktivitaeten = []
        self._namen: dict[int, str] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        filter_zeile = QHBoxLayout()
        bereich_label = QLabel("Lebensbereich")
        filter_zeile.addWidget(bereich_label)
        self.bereich_filter = Auswahl()
        bereich_label.setBuddy(self.bereich_filter)
        filter_zeile.addWidget(self.bereich_filter)
        filter_zeile.addSpacing(12)
        status_label = QLabel("Status")
        filter_zeile.addWidget(status_label)
        self.status_filter = Auswahl()
        status_label.setBuddy(self.status_filter)
        self.status_filter.addItem("Alle", None)
        for status, text in STATUS_TEXT.items():
            self.status_filter.addItem(text, status)
        filter_zeile.addWidget(self.status_filter)
        filter_zeile.addStretch(1)
        self.anzahl_label = QLabel()
        self.anzahl_label.setObjectName("leise")
        filter_zeile.addWidget(self.anzahl_label)
        layout.addLayout(filter_zeile)

        self.tabelle = QTableWidget(0, len(SPALTEN))
        self.tabelle.setHorizontalHeaderLabels(SPALTEN)
        self.tabelle.verticalHeader().hide()
        self.tabelle.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabelle.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabelle.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabelle, 1)

        knoepfe = QHBoxLayout()
        self.bearbeiten_knopf = QPushButton("Bearbeiten")
        self.loeschen_knopf = QPushButton("Löschen")
        self.loeschen_knopf.setObjectName("gefahr")
        self.ueberspringen_knopf = QPushButton("Termin überspringen")
        for knopf in (self.bearbeiten_knopf, self.loeschen_knopf, self.ueberspringen_knopf):
            knoepfe.addWidget(knopf)
        knoepfe.addStretch(1)
        layout.addLayout(knoepfe)

        self.bereich_filter.currentIndexChanged.connect(self._fuellen)
        self.status_filter.currentIndexChanged.connect(self._fuellen)
        self.tabelle.itemSelectionChanged.connect(self._auswahl_geaendert)
        self.tabelle.cellDoubleClicked.connect(lambda *_: self._bearbeiten())
        self.bearbeiten_knopf.clicked.connect(self._bearbeiten)
        self.loeschen_knopf.clicked.connect(self._loeschen)
        self.ueberspringen_knopf.clicked.connect(self._ueberspringen)
        self._auswahl_geaendert()

    def aktualisieren(self) -> None:
        """Lädt Bereiche und Aktivitäten der gewählten Woche neu."""
        bereiche = self.kontext.stammdaten.alle_bereiche()
        self._namen = {b.id: b.name for b in bereiche}
        gewaehlt = self.bereich_filter.currentData()
        self.bereich_filter.blockSignals(True)
        self.bereich_filter.clear()
        self.bereich_filter.addItem("Alle", None)
        for b in bereiche:
            self.bereich_filter.addItem(b.name, b.id)
        self.bereich_filter.setCurrentIndex(max(0, self.bereich_filter.findData(gewaehlt)))
        self.bereich_filter.blockSignals(False)
        self._aktivitaeten = self.kontext.aktivitaeten.fuer_woche(self.zustand.kw)
        self._fuellen()

    def _fuellen(self) -> None:
        bereich = self.bereich_filter.currentData()
        status = self.status_filter.currentData()
        zeilen = [
            a
            for a in self._aktivitaeten
            if (bereich is None or a.lebensbereich_id == bereich)
            and (status is None or a.status is status)
        ]
        self.tabelle.setRowCount(len(zeilen))
        for nr, a in enumerate(zeilen):
            zeit = f"{a.beginn:%H:%M}–{a.ende:%H:%M}" if a.beginn and a.ende else "–"
            if a.ueber_mitternacht:
                zeit += " (+1)"
            werte = [
                f"{WOCHENTAG_TEXT[Wochentag.aus_datum(a.datum)]} {a.datum:%d.%m.%Y}",
                zeit,
                self._namen.get(a.lebensbereich_id, "?"),
                a.titel,
                f"{a.dauer_minuten} min ({stunden_text(a.dauer_minuten / 60)})",
                STATUS_TEXT[a.status],
                "ja" if a.ist_demo else "",
                "ja" if a.serie_id else "",
            ]
            for spalte, text in enumerate(werte):
                zelle = QTableWidgetItem(text)
                zelle.setData(Qt.ItemDataRole.UserRole, a)
                self.tabelle.setItem(nr, spalte, zelle)
        self.tabelle.resizeColumnsToContents()
        self.tabelle.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.anzahl_label.setText(f"{len(zeilen)} von {len(self._aktivitaeten)} Aktivitäten")
        self._auswahl_geaendert()

    def _gewaehlt(self):
        zeilen = self.tabelle.selectionModel().selectedRows()
        if not zeilen:
            return None
        return self.tabelle.item(zeilen[0].row(), 0).data(Qt.ItemDataRole.UserRole)

    def _auswahl_geaendert(self) -> None:
        a = self._gewaehlt()
        self.bearbeiten_knopf.setEnabled(a is not None)
        self.loeschen_knopf.setEnabled(a is not None)
        self.ueberspringen_knopf.setEnabled(_ueberspringbar(a))

    def _bearbeiten(self) -> None:
        a = self._gewaehlt()
        if a is not None:
            aktivitaet_bearbeiten(self.kontext, self.zustand, a.id, parent=self)

    def _loeschen(self) -> None:
        a = self._gewaehlt()
        if a is None:
            return
        antwort = QMessageBox.question(
            self, "Aktivität löschen", als_html(f"Aktivität „{a.titel}“ wirklich löschen?")
        )
        if antwort == QMessageBox.StandardButton.Yes:
            self.kontext.aktivitaeten.loeschen(a.id)
            self.zustand.daten_geaendert.emit()

    def _ueberspringen(self) -> None:
        a = self._gewaehlt()
        if not _ueberspringbar(a):
            return
        antwort = QMessageBox.question(
            self,
            "Termin überspringen",
            als_html(
                f"Termin „{a.titel}“ am {a.datum:%d.%m.%Y} überspringen? "
                "Die übrigen Termine der Serie bleiben erhalten."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if antwort != QMessageBox.StandardButton.Yes:
            return
        try:
            self.kontext.aktivitaeten.termin_ueberspringen(a.id)
        except RegelVerletzung as e:
            QMessageBox.warning(self, "Termin überspringen", str(e))
            return
        self.zustand.daten_geaendert.emit()
