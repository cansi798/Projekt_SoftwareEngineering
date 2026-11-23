"""Demodaten laden oder entfernen (US18, GP09)."""

from PySide6.QtWidgets import (
    QButtonGroup,
    QDialog,
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
from balanceos.domaene.bewertung import MIN_TAGE
from balanceos.domaene.kalender import KW
from balanceos.praesentation.zustand import Zustand

M_GELADEN = "Demodaten geladen. Entfernen unter Einstellungen → Daten."


def demodaten_laden(kontext: AppKontext, zustand: Zustand, parent: QWidget | None) -> bool:
    """Lädt die Demodaten, meldet das Ergebnis und wählt eine aussagekräftige Woche.

    Hat die aktuelle Woche weniger als vier Tage mit Daten, wird die Vorwoche
    gewählt, damit das Dashboard sofort Scores und Hinweise zeigt.
    """
    try:
        kontext.daten.demodaten_laden()
    except RegelVerletzung as e:
        QMessageBox.warning(parent, "Demodaten", str(e))
        return False
    meldung = M_GELADEN
    aktuell = KW.heute(kontext.heute())
    if kontext.auswertung.wochenbewertung(aktuell).vollstaendigkeit_tage < MIN_TAGE:
        vorwoche = aktuell.verschoben(-1)
        zustand.setze_kw(vorwoche)
        meldung += (
            f"\n\nDie aktuelle Woche hat erst wenige Einträge. Angezeigt wird KW {vorwoche.woche}."
        )
    else:
        zustand.setze_kw(aktuell)
    zustand.daten_geaendert.emit()
    QMessageBox.information(parent, "Demodaten", meldung)
    return True


class DemodatenDialog(QDialog):
    """Auswahl zwischen „Laden“ und „Entfernen“; nur die mögliche Option ist aktiv."""

    def __init__(
        self, kontext: AppKontext, zustand: Zustand, parent: QWidget | None = None
    ) -> None:
        """Baut den Dialog passend zum aktuellen Datenbestand auf."""
        super().__init__(parent)
        self._kontext = kontext
        self._zustand = zustand
        self.setWindowTitle("Demodaten")
        layout = QVBoxLayout(self)
        text = QLabel(
            "Die Demodaten zeigen acht Wochen aus dem Alltag der Persona Sarah Keller. Sie werden"
            " zusätzlich zu Ihren Daten geladen, sind als „Demo“ gekennzeichnet und lassen sich"
            " vollständig entfernen, ohne Ihre eigenen Einträge zu verändern."
        )
        text.setWordWrap(True)
        layout.addWidget(text)
        vorhanden = kontext.daten.demodaten_vorhanden()
        self.laden_option = QRadioButton("Demodaten laden")
        self.entfernen_option = QRadioButton("Demodaten entfernen")
        gruppe = QButtonGroup(self)
        gruppe.addButton(self.laden_option)
        gruppe.addButton(self.entfernen_option)
        self.laden_option.setEnabled(not vorhanden)
        self.entfernen_option.setEnabled(vorhanden)
        (self.entfernen_option if vorhanden else self.laden_option).setChecked(True)
        layout.addWidget(self.laden_option)
        layout.addWidget(self.entfernen_option)
        knoepfe = QHBoxLayout()
        knoepfe.addStretch(1)
        abbrechen = QPushButton("Abbrechen")
        self.ausfuehren_knopf = QPushButton("Ausführen")
        self.ausfuehren_knopf.setObjectName("primaer")
        self.ausfuehren_knopf.setDefault(True)
        knoepfe.addWidget(abbrechen)
        knoepfe.addWidget(self.ausfuehren_knopf)
        layout.addLayout(knoepfe)
        abbrechen.clicked.connect(self.reject)
        self.ausfuehren_knopf.clicked.connect(self._ausfuehren)

    def _ausfuehren(self) -> None:
        if self.laden_option.isChecked():
            if demodaten_laden(self._kontext, self._zustand, self):
                self.accept()
            return
        anzahl = self._kontext.daten.demodaten_entfernen()
        self._zustand.daten_geaendert.emit()
        QMessageBox.information(self, "Demodaten", f"{anzahl} Demo-Aktivitäten entfernt.")
        self.accept()
