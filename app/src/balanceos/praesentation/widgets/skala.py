"""Auswahl eines Skalenwerts über eine Reihe von Schaltflächen."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QPushButton, QWidget

KNOPF_STIL = """
QPushButton { min-width: 30px; max-width: 30px; padding: 4px 0; }
QPushButton:checked { background: #3A7D44; color: white; border-color: #3A7D44; }
"""


class Skala(QWidget):
    """Wahl eines ganzzahligen Werts (z. B. 1–5) oder „keine Angabe“.

    Skalen statt Freitext verhindern ungültige Werte von vornherein
    (Spezifikation, Abschnitt „Eingabevalidierung“).
    """

    geaendert = Signal()

    def __init__(
        self,
        von: int = 1,
        bis: int = 5,
        mit_leer: bool = True,
        tooltips: dict[int, str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Erzeugt die Skala mit Werten von ``von`` bis ``bis``."""
        super().__init__(parent)
        self.setStyleSheet(KNOPF_STIL)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._gruppe = QButtonGroup(self)
        self._gruppe.setExclusive(True)
        if mit_leer:
            leer = QPushButton("–")
            leer.setCheckable(True)
            leer.setToolTip("keine Angabe")
            self._gruppe.addButton(leer, -1)
            layout.addWidget(leer)
        for wert in range(von, bis + 1):
            knopf = QPushButton(str(wert))
            knopf.setCheckable(True)
            if tooltips and wert in tooltips:
                knopf.setToolTip(tooltips[wert])
            self._gruppe.addButton(knopf, wert)
            layout.addWidget(knopf)
        layout.addStretch(1)
        self._gruppe.idToggled.connect(lambda _id, an: an and self.geaendert.emit())
        self.setze(None)

    def wert(self) -> int | None:
        """Gewählter Wert oder ``None`` für „keine Angabe“ bzw. keine Auswahl."""
        knopf_id = self._gruppe.checkedId()
        return None if knopf_id == -1 or self._gruppe.checkedButton() is None else knopf_id

    def setze(self, wert: int | None) -> None:
        """Wählt einen Wert; ``None`` wählt „keine Angabe“ bzw. hebt die Auswahl auf."""
        knopf = self._gruppe.button(-1 if wert is None else wert)
        if knopf is not None:
            knopf.setChecked(True)
        elif self._gruppe.checkedButton() is not None:
            self._gruppe.setExclusive(False)
            self._gruppe.checkedButton().setChecked(False)
            self._gruppe.setExclusive(True)
