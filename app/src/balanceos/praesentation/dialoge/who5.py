"""Dialog „WHO-5-Fragebogen“ mit Auswertung (US20, GP06, GR26)."""

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDateEdit,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.fehler import ValidierungsFehler
from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.who5 import AUSSAGEN, EINLEITUNG, EMPFEHLUNGSTEXT, KEINE_DIAGNOSE, SKALA
from balanceos.praesentation.widgets.feldfehler import fehlerlabel
from balanceos.praesentation.zustand import Zustand


class Who5Dialog(QDialog):
    """Fünf Aussagen mit je sechs Antwortstufen; „Auswerten“ erst bei vollständiger Antwort."""

    def __init__(
        self, kontext: AppKontext, zustand: Zustand, parent: QWidget | None = None
    ) -> None:
        """Baut Fragebogen, Ergebnisbereich und Knöpfe auf."""
        super().__init__(parent)
        self._kontext = kontext
        self._zustand = zustand
        self.setWindowTitle("WHO-5-Fragebogen zum Wohlbefinden")
        self.setMinimumWidth(920)
        layout = QVBoxLayout(self)

        form = QFormLayout()
        heute = kontext.heute()
        self.datum_feld = QDateEdit(QDate(heute.year, heute.month, heute.day))
        self.datum_feld.setDisplayFormat("dd.MM.yyyy")
        self.datum_feld.setCalendarPopup(True)
        self.datum_feld.setMaximumDate(QDate(heute.year, heute.month, heute.day))
        form.addRow("Datum", self.datum_feld)
        layout.addLayout(form)
        einleitung = QLabel(EINLEITUNG)
        einleitung.setWordWrap(True)
        layout.addWidget(einleitung)

        raster = QGridLayout()
        raster.setHorizontalSpacing(10)
        for spalte, text in enumerate(SKALA, start=1):
            kopf = QLabel(f"{text}<br><b>{spalte - 1}</b>")
            kopf.setObjectName("leise")
            kopf.setWordWrap(True)
            kopf.setAlignment(Qt.AlignmentFlag.AlignCenter)
            kopf.setFixedSize(104, 72)
            raster.addWidget(kopf, 0, spalte)
        self.optionen: list[list[QRadioButton]] = []
        self._gruppen: list[QButtonGroup] = []
        for zeile, aussage in enumerate(AUSSAGEN, start=1):
            text = QLabel(f"{zeile}. {aussage}")
            text.setWordWrap(True)
            text.setMinimumSize(250, 40)
            raster.addWidget(text, zeile, 0)
            gruppe = QButtonGroup(self)
            knoepfe = []
            for wert, stufe in enumerate(SKALA):
                knopf = QRadioButton()
                knopf.setToolTip(f"{stufe} ({wert})")
                knopf.setAccessibleName(f"Aussage {zeile}: {stufe}")
                gruppe.addButton(knopf, wert)
                knoepfe.append(knopf)
                raster.addWidget(knopf, zeile, wert + 1, Qt.AlignmentFlag.AlignCenter)
            gruppe.idToggled.connect(lambda *_: self._pruefen())
            self._gruppen.append(gruppe)
            self.optionen.append(knoepfe)
        raster.setColumnStretch(0, 1)
        layout.addLayout(raster)

        self.offen_label = QLabel()
        self.offen_label.setObjectName("leise")
        layout.addWidget(self.offen_label)
        self.fehler_label = fehlerlabel()
        layout.addWidget(self.fehler_label)

        self.ergebnis_kasten = QFrame()
        self.ergebnis_kasten.setObjectName("infokasten")
        kasten = QVBoxLayout(self.ergebnis_kasten)
        self.ergebnis_label = QLabel()
        self.ergebnis_label.setStyleSheet("font-weight: 600; font-size: 15px;")
        kasten.addWidget(self.ergebnis_label)
        self.empfehlung_label = QLabel(EMPFEHLUNGSTEXT)
        self.empfehlung_label.setWordWrap(True)
        kasten.addWidget(self.empfehlung_label)
        hinweis = QLabel(KEINE_DIAGNOSE)
        hinweis.setObjectName("leise")
        hinweis.setWordWrap(True)
        kasten.addWidget(hinweis)
        self.ergebnis_kasten.hide()
        layout.addWidget(self.ergebnis_kasten)

        knoepfe = QHBoxLayout()
        knoepfe.addStretch(1)
        self.abbrechen_knopf = QPushButton("Abbrechen")
        self.auswerten_knopf = QPushButton("Auswerten")
        self.auswerten_knopf.setObjectName("primaer")
        self.auswerten_knopf.setDefault(True)
        knoepfe.addWidget(self.abbrechen_knopf)
        knoepfe.addWidget(self.auswerten_knopf)
        layout.addLayout(knoepfe)
        self.abbrechen_knopf.clicked.connect(self.reject)
        self.auswerten_knopf.clicked.connect(self._auswerten)
        self._pruefen()

    def antworten(self) -> list[int | None]:
        """Gewählte Punktwerte je Aussage, ``None`` für offene Aussagen."""
        return [g.checkedId() if g.checkedId() >= 0 else None for g in self._gruppen]

    def _pruefen(self) -> None:
        offen = sum(1 for a in self.antworten() if a is None)
        wort = "Aussage" if offen == 1 else "Aussagen"
        self.offen_label.setText(f"Noch offen: {offen} {wort}." if offen else "")
        self.auswerten_knopf.setEnabled(offen == 0)

    def _auswerten(self) -> None:
        try:
            ergebnis = self._kontext.reflexion.who5_speichern(
                self.datum_feld.date().toPython(), self.antworten()
            )
        except ValidierungsFehler as e:
            self.fehler_label.setText(e.fehler[0].meldung)
            self.fehler_label.show()
            return
        self.fehler_label.hide()
        self.ergebnis_label.setText(
            f"Rohwert {ergebnis.rohwert} von 25 · {ergebnis.prozentwert} % (gespeichert)"
        )
        self.empfehlung_label.setVisible(ergebnis.empfehlung)
        self.ergebnis_kasten.show()
        for gruppe in self._gruppen:
            for knopf in gruppe.buttons():
                knopf.setEnabled(False)
        self.datum_feld.setEnabled(False)
        self.auswerten_knopf.hide()
        self.abbrechen_knopf.setText("Schließen")
        self._zustand.daten_geaendert.emit()
