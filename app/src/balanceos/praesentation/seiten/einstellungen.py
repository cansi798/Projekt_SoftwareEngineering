"""Seite „Einstellungen“: Lebensbereiche, Wunschprofil, Regeln, Daten (US01–US04, US14, US16–19)."""

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.fehler import RegelVerletzung, ValidierungsFehler
from balanceos.domaene.kalender import zahl_text
from balanceos.domaene.modell import Einstellungen, Lebensbereich
from balanceos.domaene.regeln import EVIDENZ
from balanceos.domaene.validierung import MAX_WOCHENSTUNDEN
from balanceos.praesentation.dialoge.demodaten import DemodatenDialog
from balanceos.praesentation.dialoge.export import ExportDialog
from balanceos.praesentation.dialoge.lebensbereich import LebensbereichDialog, stunden
from balanceos.praesentation.dialoge.loeschen import LoeschenDialog
from balanceos.praesentation.seiten.basis import Seite, leeren, scrollbar
from balanceos.praesentation.widgets.feldfehler import fehlerlabel, markiere

TYP_TEXT = {"MINDESTZIEL": "Mindestziel", "OBERGRENZE": "Obergrenze"}


class EinstellungenSeite(Seite):
    """Einstellungen in vier Reitern; gültige Änderungen werden sofort gespeichert."""

    titel = "Einstellungen"

    def __init__(self, kontext, zustand) -> None:
        """Baut die vier Reiter auf."""
        super().__init__(kontext, zustand)
        self._bereiche: list[Lebensbereich] = []
        self._profil_ids: list[int] = []
        self.soll_felder: dict[int, QDoubleSpinBox] = {}
        self.gewicht_felder: dict[int, QSpinBox] = {}
        self.regel_schalter: dict[str, QCheckBox] = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.reiter = QTabWidget()
        layout.addWidget(self.reiter)
        self.reiter.addTab(self._bereiche_reiter(), "Lebensbereiche")
        self.reiter.addTab(self._profil_reiter(), "Wunschprofil")
        self.reiter.addTab(self._regeln_reiter(), "Regeln")
        self.reiter.addTab(self._daten_reiter(), "Daten")

    # --- Reiter „Lebensbereiche“ ----------------------------------------------------------

    def _bereiche_reiter(self) -> QWidget:
        seite = QWidget()
        layout = QVBoxLayout(seite)
        self.bereich_tabelle = QTableWidget(0, 5)
        self.bereich_tabelle.setHorizontalHeaderLabels(["Name", "Typ", "Soll", "Status", "Art"])
        self.bereich_tabelle.verticalHeader().hide()
        self.bereich_tabelle.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.bereich_tabelle.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.bereich_tabelle.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bereich_tabelle.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.bereich_tabelle, 1)
        knoepfe = QHBoxLayout()
        self.neu_knopf = QPushButton("Neu …")
        self.bearbeiten_knopf = QPushButton("Bearbeiten …")
        self.aktiv_knopf = QPushButton("Deaktivieren")
        self.loeschen_knopf = QPushButton("Löschen")
        self.loeschen_knopf.setObjectName("gefahr")
        for knopf in (self.neu_knopf, self.bearbeiten_knopf, self.aktiv_knopf, self.loeschen_knopf):
            knoepfe.addWidget(knopf)
        knoepfe.addStretch(1)
        layout.addLayout(knoepfe)
        hinweis = QLabel(
            "Standardbereiche lassen sich umbenennen und deaktivieren, aber nicht löschen."
            " Eigene Bereiche lassen sich nur löschen, solange ihnen keine Aktivitäten zugeordnet"
            " sind."
        )
        hinweis.setObjectName("leise")
        hinweis.setWordWrap(True)
        layout.addWidget(hinweis)
        self.bereich_tabelle.itemSelectionChanged.connect(self._auswahl_geaendert)
        self.bereich_tabelle.cellDoubleClicked.connect(lambda *_: self._bearbeiten())
        self.neu_knopf.clicked.connect(self._neu)
        self.bearbeiten_knopf.clicked.connect(self._bearbeiten)
        self.aktiv_knopf.clicked.connect(self._aktiv_umschalten)
        self.loeschen_knopf.clicked.connect(self._loeschen)
        return seite

    def _gewaehlter_bereich(self) -> Lebensbereich | None:
        zeilen = self.bereich_tabelle.selectionModel().selectedRows()
        return self._bereiche[zeilen[0].row()] if zeilen else None

    def _auswahl_geaendert(self) -> None:
        b = self._gewaehlter_bereich()
        for knopf in (self.bearbeiten_knopf, self.aktiv_knopf, self.loeschen_knopf):
            knopf.setEnabled(b is not None)
        self.aktiv_knopf.setText("Aktivieren" if b is not None and not b.aktiv else "Deaktivieren")
        if b is not None:
            self.loeschen_knopf.setToolTip(
                "Standardbereiche können nur deaktiviert werden." if b.ist_standard else ""
            )

    def _neu(self) -> None:
        LebensbereichDialog(self.kontext, self.zustand, parent=self).exec()

    def _bearbeiten(self) -> None:
        b = self._gewaehlter_bereich()
        if b is not None:
            LebensbereichDialog(self.kontext, self.zustand, b, parent=self).exec()

    def _aktiv_umschalten(self) -> None:
        b = self._gewaehlter_bereich()
        if b is None:
            return
        try:
            self.kontext.stammdaten.speichern(replace(b, aktiv=not b.aktiv))
        except ValidierungsFehler as e:
            QMessageBox.warning(self, "Lebensbereich", e.fehler[0].meldung)
            return
        self.zustand.daten_geaendert.emit()

    def _loeschen(self) -> None:
        b = self._gewaehlter_bereich()
        if b is None:
            return
        try:
            self.kontext.stammdaten.loeschen_pruefen(b.id)
            antwort = QMessageBox.question(
                self, "Lebensbereich löschen", f"Lebensbereich „{b.name}“ wirklich löschen?"
            )
            if antwort != QMessageBox.StandardButton.Yes:
                return
            self.kontext.stammdaten.loeschen(b.id)
        except RegelVerletzung as e:
            QMessageBox.warning(self, "Lebensbereich löschen", str(e))
            return
        self.zustand.daten_geaendert.emit()

    # --- Reiter „Wunschprofil“ ------------------------------------------------------------

    def _profil_reiter(self) -> QWidget:
        innen = QWidget()
        layout = QVBoxLayout(innen)
        erklaerung = QLabel(
            "Legen Sie fest, wie viele Stunden pro Woche Sie sich für jeden aktiven Lebensbereich"
            " wünschen. Das Gewicht bestimmt den Anteil am optionalen Gesamt-Score. Änderungen"
            " werden sofort gespeichert."
        )
        erklaerung.setWordWrap(True)
        layout.addWidget(erklaerung)
        self.profil_raster = QGridLayout()
        self.profil_raster.setHorizontalSpacing(16)
        layout.addLayout(self.profil_raster)
        self.summe_label = QLabel()
        self.summe_label.setStyleSheet("font-weight: 600;")
        layout.addWidget(self.summe_label)
        self.wunsch_fehler = fehlerlabel()
        layout.addWidget(self.wunsch_fehler)

        layout.addSpacing(12)
        self.gesamtscore_feld = QCheckBox(
            "Gesamt-Score anzeigen (programmeigener Score, nicht validiert)"
        )
        layout.addWidget(self.gesamtscore_feld)
        zeile = QHBoxLayout()
        zeile.addWidget(QLabel("Anteil der Zielerfüllung am Bereichs-Score (α):"))
        self.alpha_regler = QSlider(Qt.Orientation.Horizontal)
        self.alpha_regler.setRange(0, 10)
        self.alpha_regler.setPageStep(1)
        self.alpha_regler.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.alpha_regler.setFixedWidth(220)
        zeile.addWidget(self.alpha_regler)
        self.alpha_label = QLabel()
        self.alpha_label.setStyleSheet("font-weight: 600;")
        zeile.addWidget(self.alpha_label)
        zeile.addStretch(1)
        layout.addLayout(zeile)
        alpha_text = QLabel(
            "Bei 1 zählt nur die Zielerfüllung, bei 0 nur die Zufriedenheit. Standard: 0,6."
        )
        alpha_text.setObjectName("leise")
        layout.addWidget(alpha_text)
        layout.addStretch(1)
        self.gesamtscore_feld.toggled.connect(self._einstellungen_speichern)
        self.alpha_regler.valueChanged.connect(self._einstellungen_speichern)
        return scrollbar(innen)

    def _profil_aufbauen(self, aktive: list[Lebensbereich]) -> None:
        leeren(self.profil_raster)
        self.soll_felder, self.gewicht_felder = {}, {}
        for spalte, titel in enumerate(["Lebensbereich", "Typ", "Soll pro Woche", "Gewicht"]):
            kopf = QLabel(titel)
            kopf.setObjectName("leise")
            self.profil_raster.addWidget(kopf, 0, spalte)
        for zeile, b in enumerate(aktive, start=1):
            self.profil_raster.addWidget(
                QLabel(f'<span style="color:{b.farbe}">●</span> {b.name}'), zeile, 0
            )
            self.profil_raster.addWidget(QLabel(TYP_TEXT[b.typ]), zeile, 1)
            soll = QDoubleSpinBox()
            soll.setRange(0, MAX_WOCHENSTUNDEN)
            soll.setSingleStep(0.5)
            soll.setDecimals(1)
            soll.setSuffix(" h")
            soll.setKeyboardTracking(False)
            gewicht = QSpinBox()
            gewicht.setRange(0, 10)
            gewicht.setKeyboardTracking(False)
            # Die Spaltenköpfe sind keine Buddy-Labels; Screenreader brauchen den Namen am Feld.
            soll.setAccessibleName(f"Soll pro Woche: {b.name}")
            gewicht.setAccessibleName(f"Gewicht: {b.name}")
            self.soll_felder[b.id] = soll
            self.gewicht_felder[b.id] = gewicht
            self.profil_raster.addWidget(soll, zeile, 2)
            self.profil_raster.addWidget(gewicht, zeile, 3)
            soll.valueChanged.connect(lambda _w, i=b.id: self._profil_speichern(i))
            gewicht.valueChanged.connect(lambda _w, i=b.id: self._profil_speichern(i))
        self.profil_raster.setColumnStretch(4, 1)
        self._profil_ids = [b.id for b in aktive]

    def _profil_werte(self, aktive: list[Lebensbereich]) -> None:
        for b in aktive:
            for feld, wert in (
                (self.soll_felder[b.id], b.soll_stunden),
                (self.gewicht_felder[b.id], b.gewicht),
            ):
                feld.blockSignals(True)
                feld.setValue(wert)
                feld.blockSignals(False)
                markiere(feld, self.wunsch_fehler, None)
        self.summe_label.setText(
            f"{stunden(self.kontext.stammdaten.verplante_stunden())} von"
            f" {MAX_WOCHENSTUNDEN} h verplant"
        )

    def _profil_speichern(self, bereich_id: int) -> None:
        b = self.kontext.stammdaten.bereich(bereich_id)
        soll_feld = self.soll_felder[bereich_id]
        neu = replace(
            b,
            soll_stunden=soll_feld.value(),
            gewicht=self.gewicht_felder[bereich_id].value(),
        )
        try:
            self.kontext.stammdaten.speichern(neu)
        except ValidierungsFehler as e:
            feld = self.gewicht_felder[bereich_id] if e.fehler[0].feld == "gewicht" else soll_feld
            markiere(feld, self.wunsch_fehler, e.fehler[0].meldung)
            return
        markiere(soll_feld, self.wunsch_fehler, None)
        self.zustand.daten_geaendert.emit()

    def _einstellungen_speichern(self) -> None:
        alpha = self.alpha_regler.value() / 10
        self.alpha_label.setText(zahl_text(alpha))
        self.kontext.stammdaten.einstellungen_speichern(
            Einstellungen(alpha=alpha, gesamtscore_anzeigen=self.gesamtscore_feld.isChecked())
        )
        self.zustand.daten_geaendert.emit()

    # --- Reiter „Regeln“ ------------------------------------------------------------------

    def _regeln_reiter(self) -> QWidget:
        innen = QWidget()
        layout = QVBoxLayout(innen)
        text = QLabel(
            "Abgeschaltete Regeln erzeugen keine Hinweise. Die Grundlagen der Regeln erklärt der"
            " Balance-Kompass."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        self.regel_raster = QGridLayout()
        self.regel_raster.setHorizontalSpacing(16)
        modelle = {m.schluessel: m.name for m in self.kontext.auswertung.kompassmodelle()}
        for spalte, titel in enumerate(["Regel", "Modell", "Evidenzart"]):
            kopf = QLabel(titel)
            kopf.setObjectName("leise")
            self.regel_raster.addWidget(kopf, 0, spalte)
        for zeile, r in enumerate(self.kontext.auswertung.regeln(), start=1):
            schalter = QCheckBox(f"{r.kennung} – {r.bezeichnung}")
            self.regel_schalter[r.kennung] = schalter
            self.regel_raster.addWidget(schalter, zeile, 0)
            self.regel_raster.addWidget(QLabel(modelle.get(r.modell_schluessel, "")), zeile, 1)
            evidenz = QLabel(EVIDENZ.get(r.kennung, ""))
            evidenz.setObjectName("leise")
            self.regel_raster.addWidget(evidenz, zeile, 2)
            schalter.toggled.connect(lambda an, k=r.kennung: self._regel_setzen(k, an))
        self.regel_raster.setColumnStretch(3, 1)
        layout.addLayout(self.regel_raster)
        layout.addStretch(1)
        return scrollbar(innen)

    def _regel_setzen(self, kennung: str, aktiv: bool) -> None:
        self.kontext.auswertung.regel_setzen(kennung, aktiv)
        self.zustand.daten_geaendert.emit()

    # --- Reiter „Daten“ -------------------------------------------------------------------

    def _daten_reiter(self) -> QWidget:
        seite = QWidget()
        layout = QVBoxLayout(seite)
        eintraege = [
            (
                "Exportieren …",
                "Aktivitäten als CSV oder alle Nutzdaten als JSON speichern.",
                lambda: ExportDialog(self.kontext, self.zustand, self).exec(),
            ),
            (
                "Demodaten …",
                "Acht Beispielwochen laden oder wieder entfernen.",
                lambda: DemodatenDialog(self.kontext, self.zustand, self).exec(),
            ),
            (
                "Alle Daten löschen …",
                "Alle Nutzdaten entfernen und wie beim ersten Start beginnen.",
                lambda: LoeschenDialog(self.kontext, self.zustand, self).exec(),
            ),
        ]
        self.daten_knoepfe: list[QPushButton] = []
        for text, erklaerung, aktion in eintraege:
            zeile = QHBoxLayout()
            knopf = QPushButton(text)
            knopf.setMinimumWidth(190)
            if text.startswith("Alle"):
                knopf.setObjectName("gefahr")
            knopf.clicked.connect(aktion)
            self.daten_knoepfe.append(knopf)
            zeile.addWidget(knopf)
            beschreibung = QLabel(erklaerung)
            beschreibung.setObjectName("leise")
            zeile.addWidget(beschreibung, 1)
            layout.addLayout(zeile)
        layout.addSpacing(16)
        pfad = self.kontext.daten.datenbankpfad
        ordner = str(Path(pfad).parent) if pfad != ":memory:" else "(nur im Arbeitsspeicher)"
        self.ordner_label = QLabel(
            f"Datenordner: {ordner}<br>Alle Daten bleiben auf diesem Rechner; BalanceOS"
            " überträgt nichts ins Internet."
        )
        self.ordner_label.setWordWrap(True)
        self.ordner_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.ordner_label)
        layout.addStretch(1)
        return seite

    # --- Aktualisieren --------------------------------------------------------------------

    def aktualisieren(self) -> None:
        """Lädt Bereiche, Wunschprofil, Einstellungen und Regeln neu."""
        self._bereiche = self.kontext.stammdaten.alle_bereiche()
        gewaehlt = self._gewaehlter_bereich()
        self.bereich_tabelle.setRowCount(len(self._bereiche))
        for zeile, b in enumerate(self._bereiche):
            werte = [
                b.name,
                TYP_TEXT[b.typ],
                f"{stunden(b.soll_stunden)} h",
                "aktiv" if b.aktiv else "inaktiv",
                "Standard" if b.ist_standard else "eigener Bereich",
            ]
            for spalte, text in enumerate(werte):
                zelle = QTableWidgetItem(text)
                if spalte == 0:
                    zelle.setData(Qt.ItemDataRole.DecorationRole, _farbfeld(b.farbe))
                self.bereich_tabelle.setItem(zeile, spalte, zelle)
        self.bereich_tabelle.resizeColumnsToContents()
        if gewaehlt is not None:
            ids = [b.id for b in self._bereiche]
            if gewaehlt.id in ids:
                self.bereich_tabelle.selectRow(ids.index(gewaehlt.id))
        self._auswahl_geaendert()

        aktive = [b for b in self._bereiche if b.aktiv]
        if [b.id for b in aktive] != self._profil_ids:
            self._profil_aufbauen(aktive)
        self._profil_werte(aktive)

        e = self.kontext.stammdaten.einstellungen()
        for feld in (self.gesamtscore_feld, self.alpha_regler):
            feld.blockSignals(True)
        self.gesamtscore_feld.setChecked(e.gesamtscore_anzeigen)
        self.alpha_regler.setValue(round(e.alpha * 10))
        self.alpha_label.setText(zahl_text(e.alpha))
        for feld in (self.gesamtscore_feld, self.alpha_regler):
            feld.blockSignals(False)

        for r in self.kontext.auswertung.regeln():
            schalter = self.regel_schalter.get(r.kennung)
            if schalter is not None:
                schalter.blockSignals(True)
                schalter.setChecked(r.aktiv)
                schalter.blockSignals(False)


def _farbfeld(farbe: str) -> QPixmap:
    """Kleines Farbquadrat für die Bereichstabelle."""
    bild = QPixmap(12, 12)
    bild.fill(QColor(farbe))
    return bild
