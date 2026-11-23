"""Seite „Balance-Kompass“: Modelle, Quellen, Grenzen und zugeordnete Regeln (US15)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QVBoxLayout,
    QWidget,
)

from balanceos.domaene.modell import KompassModell
from balanceos.praesentation.seiten.basis import Seite, karte, leeren, scrollbar
from balanceos.praesentation.texte import EVIDENZART_TEXT

HINWEIS = (
    "BalanceOS ist kein Medizinprodukt und stellt keine Diagnosen. Die Modelle erklären, woher"
    " die Hinweise kommen; sie ersetzen keine ärztliche oder psychotherapeutische Beratung."
)


def _textlabel() -> QLabel:
    label = QLabel()
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class KompassSeite(Seite):
    """Liste der sechs Modelle links, Details des gewählten Modells rechts."""

    titel = "Kompass"

    def __init__(self, kontext, zustand) -> None:
        """Baut Modellliste und Detailbereich auf."""
        super().__init__(kontext, zustand)
        self._modelle: list[KompassModell] = []
        self.regel_zeilen: list[tuple[str, QLabel]] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        kasten = QFrame()
        kasten.setObjectName("infokasten")
        kasten_layout = QVBoxLayout(kasten)
        self.hinweis_kasten_text = QLabel(HINWEIS)
        self.hinweis_kasten_text.setWordWrap(True)
        kasten_layout.addWidget(self.hinweis_kasten_text)
        layout.addWidget(kasten)

        zeile = QHBoxLayout()
        layout.addLayout(zeile, 1)
        self.modell_liste = QListWidget()
        self.modell_liste.setFixedWidth(260)
        zeile.addWidget(self.modell_liste)

        innen = QWidget()
        details = QVBoxLayout(innen)
        self.name_label = QLabel()
        self.name_label.setObjectName("seitentitel")
        details.addWidget(self.name_label)
        self.evidenz_label = QLabel()
        self.evidenz_label.setObjectName("etikett")
        self.evidenz_label.setStyleSheet("background: #1C7ED6; color: white;")
        details.addWidget(self.evidenz_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.beschreibung_label = _textlabel()
        self.grenzen_label = _textlabel()
        self.quelle_label = _textlabel()
        for titel, label in (
            ("Worum es geht", self.beschreibung_label),
            ("Grenzen", self.grenzen_label),
            ("Quelle", self.quelle_label),
        ):
            rahmen, inhalt = karte(titel)
            inhalt.addWidget(label)
            details.addWidget(rahmen)
        rahmen, karten_layout = karte("Regeln in BalanceOS")
        self._regeln_layout = QVBoxLayout()
        karten_layout.addLayout(self._regeln_layout)
        details.addWidget(rahmen)
        details.addStretch(1)
        zeile.addWidget(scrollbar(innen), 1)

        self.modell_liste.currentRowChanged.connect(self._zeige)

    def aktualisieren(self) -> None:
        """Lädt die Modelle und behält die Auswahl bei."""
        zeile = max(0, self.modell_liste.currentRow())
        self._modelle = self.kontext.auswertung.kompassmodelle()
        self.modell_liste.blockSignals(True)
        self.modell_liste.clear()
        for m in self._modelle:
            self.modell_liste.addItem(m.name)
        self.modell_liste.blockSignals(False)
        self.modell_liste.setCurrentRow(min(zeile, len(self._modelle) - 1))
        self._zeige(self.modell_liste.currentRow())

    def _zeige(self, zeile: int) -> None:
        if not 0 <= zeile < len(self._modelle):
            return
        m = self._modelle[zeile]
        self.name_label.setText(m.name)
        self.evidenz_label.setText(EVIDENZART_TEXT[m.evidenzart])
        self.beschreibung_label.setText(m.kurzbeschreibung)
        self.grenzen_label.setText(m.grenzen)
        self.quelle_label.setText(m.quelle)
        leeren(self._regeln_layout)
        self.regel_zeilen = []
        regeln = [
            r for r in self.kontext.auswertung.regeln() if r.modell_schluessel == m.schluessel
        ]
        for r in regeln:
            zustand = "aktiv" if r.aktiv else "abgeschaltet"
            label = QLabel(f"<b>{r.kennung}</b> – {r.bezeichnung} ({zustand})")
            self.regel_zeilen.append((r.kennung, label))
            self._regeln_layout.addWidget(label)
        if not regeln:
            self._regeln_layout.addWidget(QLabel("Diesem Modell ist keine Regel zugeordnet."))
