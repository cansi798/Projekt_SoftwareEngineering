"""Dialog „Exportieren“ für CSV und JSON (US16, NFA10)."""

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QDate, QStandardPaths
from PySide6.QtWidgets import (
    QButtonGroup,
    QDateEdit,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.fehler import RegelVerletzung
from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.validierung import pruefe_zeitraum
from balanceos.praesentation.widgets.feldfehler import fehlerlabel, markiere
from balanceos.praesentation.zustand import Zustand


def _datumsfeld(tag) -> QDateEdit:
    feld = QDateEdit(QDate(tag.year, tag.month, tag.day))
    feld.setDisplayFormat("dd.MM.yyyy")
    feld.setCalendarPopup(True)
    return feld


def dokumente_ordner() -> Path:
    """Vorgeschlagener Speicherort (Ordner „Dokumente“ des Benutzers)."""
    ort = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
    return Path(ort) if ort else Path.home()


class ExportDialog(QDialog):
    """Wahl zwischen CSV (Aktivitäten eines Zeitraums) und JSON (alle Nutzdaten)."""

    def __init__(
        self, kontext: AppKontext, zustand: Zustand, parent: QWidget | None = None
    ) -> None:
        """Baut den Dialog mit der gewählten Woche als Zeitraum auf."""
        super().__init__(parent)
        self._kontext = kontext
        self.setWindowTitle("Daten exportieren")
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)

        self.csv_option = QRadioButton("CSV: Aktivitäten eines Zeitraums (für Excel)")
        self.json_option = QRadioButton("JSON: vollständige Kopie aller Nutzdaten")
        gruppe = QButtonGroup(self)
        gruppe.addButton(self.csv_option)
        gruppe.addButton(self.json_option)
        self.csv_option.setChecked(True)
        layout.addWidget(self.csv_option)

        self._zeitraum = QWidget()
        form = QFormLayout(self._zeitraum)
        form.setContentsMargins(24, 0, 0, 0)
        self.von_feld = _datumsfeld(zustand.kw.montag())
        self.bis_feld = _datumsfeld(zustand.kw.sonntag())
        form.addRow("von", self.von_feld)
        form.addRow("bis", self.bis_feld)
        self.zeitraum_fehler = fehlerlabel()
        form.addRow("", self.zeitraum_fehler)
        layout.addWidget(self._zeitraum)
        layout.addWidget(self.json_option)

        hinweis = QLabel(
            "Wochenbewertungen und Hinweise werden nicht exportiert; sie lassen sich jederzeit"
            " aus den Daten neu berechnen."
        )
        hinweis.setObjectName("leise")
        hinweis.setWordWrap(True)
        layout.addWidget(hinweis)

        knoepfe = QHBoxLayout()
        knoepfe.addStretch(1)
        abbrechen = QPushButton("Abbrechen")
        self.exportieren_knopf = QPushButton("Exportieren …")
        self.exportieren_knopf.setObjectName("primaer")
        self.exportieren_knopf.setDefault(True)
        knoepfe.addWidget(abbrechen)
        knoepfe.addWidget(self.exportieren_knopf)
        layout.addLayout(knoepfe)

        for signal in (
            self.csv_option.toggled,
            self.von_feld.dateChanged,
            self.bis_feld.dateChanged,
        ):
            signal.connect(self._pruefen)
        abbrechen.clicked.connect(self.reject)
        self.exportieren_knopf.clicked.connect(self._exportieren)
        self._pruefen()

    def _pruefen(self) -> bool:
        csv_gewaehlt = self.csv_option.isChecked()
        self._zeitraum.setEnabled(csv_gewaehlt)
        fehler = pruefe_zeitraum(self.von_feld.date().toPython(), self.bis_feld.date().toPython())
        meldung = fehler[0].meldung if fehler and csv_gewaehlt else None
        markiere(self.bis_feld, self.zeitraum_fehler, meldung)
        self.exportieren_knopf.setEnabled(meldung is None)
        return meldung is None

    def _exportieren(self) -> None:
        if not self._pruefen():
            return
        export = self._kontext.export
        if self.csv_option.isChecked():
            von, bis = self.von_feld.date().toPython(), self.bis_feld.date().toPython()
            name, filter_ = export.dateiname_csv(von, bis), "CSV-Datei (*.csv)"
        else:
            name, filter_ = export.dateiname_json(self._kontext.heute()), "JSON-Datei (*.json)"
        pfad, _ = QFileDialog.getSaveFileName(
            self, "Exportieren", str(dokumente_ordner() / name), filter_
        )
        if not pfad:
            return
        try:
            if self.csv_option.isChecked():
                anzahl = export.csv_exportieren(Path(pfad), von, bis)
                inhalt = f"{anzahl} Aktivitäten exportiert."
            else:
                export.json_exportieren(Path(pfad), datetime.now())
                inhalt = "Alle Nutzdaten exportiert."
        except RegelVerletzung as e:
            QMessageBox.warning(self, "Exportieren", str(e))
            return
        datei = Path(pfad)
        QMessageBox.information(
            self, "Exportieren", f"{inhalt}\n\nDatei: {datei.name}\nOrdner: {datei.parent}"
        )
        self.accept()
