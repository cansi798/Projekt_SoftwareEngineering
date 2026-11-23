"""Dialog „Alle Daten löschen“ mit Bestätigung durch Eingabe (US17, GR29)."""

from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.kalender import KW
from balanceos.domaene.validierung import LOESCHWORT
from balanceos.praesentation.zustand import Zustand

BETROFFEN = [
    "alle Aktivitäten und Wiederholungsserien, auch Demodaten",
    "eigene Lebensbereiche und Änderungen am Wunschprofil",
    "WHO-5-Ergebnisse und Wochenreflexionen",
    "Einstellungen, ausgeblendete Hinweise und abgeschaltete Regeln",
]


class LoeschenDialog(QDialog):
    """Löscht nach Eingabe von „LÖSCHEN“ alle Nutzdaten und zeigt danach das Dashboard."""

    def __init__(
        self, kontext: AppKontext, zustand: Zustand, parent: QWidget | None = None
    ) -> None:
        """Baut Warnung, Liste der betroffenen Daten und Eingabefeld auf."""
        super().__init__(parent)
        self._kontext = kontext
        self._zustand = zustand
        self.setWindowTitle("Alle Daten löschen")
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)

        kasten = QFrame()
        kasten.setObjectName("warnkasten")
        kasten_layout = QVBoxLayout(kasten)
        warnung = QLabel(
            "<b>Achtung:</b> Diese Aktion kann nicht rückgängig gemacht werden. BalanceOS"
            " startet danach wie beim ersten Mal."
        )
        warnung.setWordWrap(True)
        kasten_layout.addWidget(warnung)
        layout.addWidget(kasten)

        layout.addWidget(QLabel("Gelöscht werden:"))
        layout.addWidget(QLabel("".join(f"• {zeile}<br>" for zeile in BETROFFEN)))
        self.hinweis_text = "Bereits exportierte Dateien bleiben erhalten."
        hinweis = QLabel(self.hinweis_text)
        hinweis.setObjectName("leise")
        layout.addWidget(hinweis)

        layout.addWidget(QLabel(f"Zur Bestätigung bitte {LOESCHWORT} eingeben:"))
        self.eingabe = QLineEdit()
        self.eingabe.setPlaceholderText(LOESCHWORT)
        layout.addWidget(self.eingabe)

        knoepfe = QHBoxLayout()
        knoepfe.addStretch(1)
        self.abbrechen_knopf = QPushButton("Abbrechen")
        self.abbrechen_knopf.setDefault(True)
        self.loeschen_knopf = QPushButton("Endgültig löschen")
        self.loeschen_knopf.setObjectName("gefahr")
        self.loeschen_knopf.setAutoDefault(False)
        self.loeschen_knopf.setEnabled(False)
        knoepfe.addWidget(self.abbrechen_knopf)
        knoepfe.addWidget(self.loeschen_knopf)
        layout.addLayout(knoepfe)

        self.eingabe.textChanged.connect(
            lambda text: self.loeschen_knopf.setEnabled(text == LOESCHWORT)
        )
        self.abbrechen_knopf.clicked.connect(self.reject)
        self.loeschen_knopf.clicked.connect(self._loeschen)
        self.abbrechen_knopf.setFocus()

    def _loeschen(self) -> None:
        self._kontext.daten.alle_daten_loeschen(self.eingabe.text())
        self._zustand.setze_kw(KW.heute(self._kontext.heute()))
        self._zustand.daten_geaendert.emit()
        self._zustand.seite_angefordert.emit(0)
        self.accept()
