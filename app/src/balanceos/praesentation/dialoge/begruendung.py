"""Dialog „Warum sehe ich das?“ mit der Begründung eines Hinweises (US13, NFA11)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.modell import Hinweis
from balanceos.praesentation.stil import FARBE_HINWEISART, SYMBOL_HINWEISART
from balanceos.praesentation.zustand import Zustand

KEINE_DIAGNOSE = (
    "Dieser Hinweis ist keine Diagnose. Er beschreibt einen Zusammenhang in Ihren eigenen "
    "Einträgen, keine Ursache, und ersetzt keine ärztliche oder psychotherapeutische Beratung."
)


class BegruendungDialog(QDialog):
    """Zeigt Regel, Modell, Datenbasis, Zeitraum, Schwelle, Wert, Quelle, Evidenzart und Grenzen."""

    def __init__(
        self,
        hinweis: Hinweis,
        kontext: AppKontext,
        zustand: Zustand,
        parent: QWidget | None = None,
    ) -> None:
        """Baut die Begründung zum übergebenen Hinweis auf."""
        super().__init__(parent)
        self._hinweis = hinweis
        self._kontext = kontext
        self._zustand = zustand
        self.setWindowTitle("Warum sehe ich das?")
        self.setMinimumWidth(620)
        layout = QVBoxLayout(self)

        kopf = QLabel(f"{SYMBOL_HINWEISART[hinweis.art]}  {hinweis.text}")
        kopf.setWordWrap(True)
        kopf.setStyleSheet(
            f"font-size: 11pt; font-weight: 600; color: {FARBE_HINWEISART[hinweis.art]};"
        )
        layout.addWidget(kopf)

        raster = QGridLayout()
        raster.setHorizontalSpacing(16)
        raster.setVerticalSpacing(6)
        self.zeilen = hinweis.begruendung.zeilen()
        for nr, (beschriftung, inhalt) in enumerate(self.zeilen):
            links = QLabel(beschriftung)
            links.setStyleSheet("font-weight: 600;")
            links.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            rechts = QLabel(inhalt)
            rechts.setWordWrap(True)
            rechts.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            raster.addWidget(links, nr, 0)
            raster.addWidget(rechts, nr, 1)
        raster.setColumnStretch(1, 1)
        layout.addLayout(raster)

        kasten = QFrame()
        kasten.setObjectName("infokasten")
        kasten_layout = QVBoxLayout(kasten)
        text = QLabel(KEINE_DIAGNOSE)
        text.setWordWrap(True)
        kasten_layout.addWidget(text)
        layout.addWidget(kasten)

        knoepfe = QHBoxLayout()
        self.deaktivieren_knopf = QPushButton(f"Regel {hinweis.regel} deaktivieren")
        self.deaktivieren_knopf.setToolTip(
            "Die Regel erzeugt keine Hinweise mehr. Sie können sie unter Einstellungen"
            " im Reiter „Regeln“ wieder einschalten."
        )
        self.deaktivieren_knopf.setAutoDefault(False)
        schliessen = QPushButton("Schließen")
        schliessen.setObjectName("primaer")
        schliessen.setDefault(True)
        knoepfe.addWidget(self.deaktivieren_knopf)
        knoepfe.addStretch(1)
        knoepfe.addWidget(schliessen)
        layout.addLayout(knoepfe)

        self.deaktivieren_knopf.clicked.connect(self._deaktivieren)
        schliessen.clicked.connect(self.accept)

    def _deaktivieren(self) -> None:
        self._kontext.auswertung.regel_setzen(self._hinweis.regel, False)
        self._zustand.daten_geaendert.emit()
        self.accept()
