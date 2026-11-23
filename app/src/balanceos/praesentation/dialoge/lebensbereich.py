"""Dialog „Lebensbereich anlegen/bearbeiten“ (US01–US03)."""

from dataclasses import replace

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.fehler import ValidierungsFehler
from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.kalender import zahl_text
from balanceos.domaene.modell import Lebensbereich
from balanceos.domaene.typen import Bereichstyp
from balanceos.domaene.validierung import (
    MAX_NAME,
    MAX_WOCHENSTUNDEN,
    Fehler,
    pruefe_lebensbereich,
)
from balanceos.praesentation.widgets.feldfehler import fehlerlabel, markiere
from balanceos.praesentation.zustand import Zustand


def stunden(wert: float) -> str:
    """Stunden ohne überflüssiges „,0“ (z. B. „147“, „145,5“)."""
    text = zahl_text(wert)
    return text[:-2] if text.endswith(",0") else text


class LebensbereichDialog(QDialog):
    """Name, Typ, Farbe, Aktivzustand, Soll und Gewicht eines Lebensbereichs."""

    def __init__(
        self,
        kontext: AppKontext,
        zustand: Zustand,
        bereich: Lebensbereich | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Erzeugt den Dialog für einen neuen (``bereich is None``) oder bestehenden Bereich."""
        super().__init__(parent)
        self._kontext = kontext
        self._palette = kontext.stammdaten.farbpalette()
        self._zustand = zustand
        self._original = bereich or Lebensbereich("", Bereichstyp.MINDESTZIEL, self._palette[0], 0)
        self._name_beruehrt = bereich is not None
        self.setWindowTitle("Lebensbereich bearbeiten" if bereich else "Lebensbereich anlegen")
        self.setMinimumWidth(520)
        self.fehlerlabels: dict[str, QLabel] = {}
        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.name_feld = QLineEdit(self._original.name)
        self.name_feld.setMaxLength(MAX_NAME + 10)
        form.addRow("Name*", self._mit_fehler(self.name_feld, "name"))

        typ = QWidget()
        typ_layout = QVBoxLayout(typ)
        typ_layout.setContentsMargins(0, 0, 0, 0)
        self.mindest_option = QRadioButton("Mindestziel: mehr Zeit ist bis zum Soll besser")
        self.ober_option = QRadioButton("Obergrenze: eine Überschreitung des Solls ist ungünstig")
        gruppe = QButtonGroup(self)
        gruppe.addButton(self.mindest_option)
        gruppe.addButton(self.ober_option)
        (
            self.ober_option
            if self._original.typ is Bereichstyp.OBERGRENZE
            else self.mindest_option
        ).setChecked(True)
        typ_layout.addWidget(self.mindest_option)
        typ_layout.addWidget(self.ober_option)
        form.addRow("Typ", typ)

        farben = QWidget()
        raster = QGridLayout(farben)
        raster.setContentsMargins(0, 0, 0, 0)
        raster.setSpacing(4)
        self.farb_knoepfe: list[QPushButton] = []
        self._farb_gruppe = QButtonGroup(self)
        for nr, farbe in enumerate(self._palette):
            knopf = QPushButton()
            knopf.setCheckable(True)
            knopf.setFixedSize(26, 26)
            knopf.setToolTip(farbe)
            knopf.setStyleSheet(
                f"QPushButton {{ background: {farbe}; border-radius: 13px; border: 2px solid"
                f" white; }} QPushButton:checked {{ border: 3px solid #212529; }}"
            )
            self._farb_gruppe.addButton(knopf, nr)
            self.farb_knoepfe.append(knopf)
            raster.addWidget(knopf, 0, nr)
        if self._original.farbe in self._palette:
            self.farb_knoepfe[self._palette.index(self._original.farbe)].setChecked(True)
        else:
            self.farb_knoepfe[0].setChecked(True)
        form.addRow("Farbe", farben)

        self.aktiv_feld = QCheckBox("aktiv (wird bewertet und bei neuen Aktivitäten angeboten)")
        self.aktiv_feld.setChecked(self._original.aktiv)
        form.addRow("", self._mit_fehler(self.aktiv_feld, "aktiv"))

        self.soll_feld = QDoubleSpinBox()
        self.soll_feld.setRange(0, MAX_WOCHENSTUNDEN)
        self.soll_feld.setSingleStep(0.5)
        self.soll_feld.setDecimals(1)
        self.soll_feld.setSuffix(" h pro Woche")
        self.soll_feld.setValue(self._original.soll_stunden)
        form.addRow("Soll (Wunsch)", self._mit_fehler(self.soll_feld, "soll"))

        self.gewicht_feld = QSpinBox()
        self.gewicht_feld.setRange(0, 10)
        self.gewicht_feld.setValue(self._original.gewicht)
        self.gewicht_feld.setToolTip(
            "Gewicht im optionalen Gesamt-Score (0 = nicht berücksichtigt)"
        )
        form.addRow("Gewicht", self._mit_fehler(self.gewicht_feld, "gewicht"))

        self.verplant_label = QLabel()
        self.verplant_label.setObjectName("leise")
        form.addRow("", self.verplant_label)
        form.addRow("", self._fehler("summe"))

        knoepfe = QHBoxLayout()
        knoepfe.addStretch(1)
        abbrechen = QPushButton("Abbrechen")
        self.speichern_knopf = QPushButton("Speichern")
        self.speichern_knopf.setObjectName("primaer")
        self.speichern_knopf.setDefault(True)
        knoepfe.addWidget(abbrechen)
        knoepfe.addWidget(self.speichern_knopf)
        layout.addLayout(knoepfe)

        self.name_feld.textChanged.connect(self._name_geaendert)
        for signal in (
            self.mindest_option.toggled,
            self.aktiv_feld.toggled,
            self.soll_feld.valueChanged,
            self.gewicht_feld.valueChanged,
        ):
            signal.connect(self._pruefen)
        abbrechen.clicked.connect(self.reject)
        self.speichern_knopf.clicked.connect(self._speichern)
        self._pruefen()

    def _fehler(self, schluessel: str) -> QLabel:
        label = fehlerlabel()
        self.fehlerlabels[schluessel] = label
        return label

    def _mit_fehler(self, feld: QWidget, schluessel: str) -> QWidget:
        box = QWidget()
        spalte = QVBoxLayout(box)
        spalte.setContentsMargins(0, 0, 0, 0)
        spalte.setSpacing(2)
        spalte.addWidget(feld)
        spalte.addWidget(self._fehler(schluessel))
        return box

    def _name_geaendert(self) -> None:
        self._name_beruehrt = True
        self._pruefen()

    def _bereich_aus_feldern(self) -> Lebensbereich:
        return replace(
            self._original,
            name=self.name_feld.text(),
            typ=Bereichstyp.OBERGRENZE if self.ober_option.isChecked() else Bereichstyp.MINDESTZIEL,
            farbe=self._palette[max(0, self._farb_gruppe.checkedId())],
            aktiv=self.aktiv_feld.isChecked(),
            soll_stunden=self.soll_feld.value(),
            gewicht=self.gewicht_feld.value(),
        )

    def _pruefen(self) -> list[Fehler]:
        b = self._bereich_aus_feldern()
        alle = self._kontext.stammdaten.alle_bereiche()
        fehler = pruefe_lebensbereich(b, alle)
        andere = [x for x in alle if b.id is None or x.id != b.id]
        summe = sum(x.soll_stunden for x in [*andere, b] if x.aktiv)
        self.verplant_label.setText(f"{stunden(summe)} von {MAX_WOCHENSTUNDEN} h verplant")
        self._anzeigen(fehler)
        return fehler

    def _anzeigen(self, fehler: list[Fehler]) -> None:
        nach_feld = {f.feld: f.meldung for f in fehler}
        felder = {
            "name": self.name_feld,
            "soll": self.soll_feld,
            "gewicht": self.gewicht_feld,
            "summe": self.soll_feld,
        }
        for schluessel, label in self.fehlerlabels.items():
            meldung = nach_feld.get(schluessel)
            if schluessel == "name" and not self._name_beruehrt:
                meldung = None
            if schluessel in ("name", "gewicht"):
                markiere(felder[schluessel], label, meldung)
            else:
                label.setText(meldung or "")
                label.setVisible(bool(meldung))
        self.speichern_knopf.setEnabled(not fehler)

    def _speichern(self) -> None:
        if self._pruefen():
            return
        try:
            self._kontext.stammdaten.speichern(self._bereich_aus_feldern())
        except ValidierungsFehler as e:
            self._name_beruehrt = True
            self._anzeigen(e.fehler)
            return
        self._zustand.daten_geaendert.emit()
        self.accept()
