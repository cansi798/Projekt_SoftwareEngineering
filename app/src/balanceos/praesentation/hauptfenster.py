"""Hauptfenster mit Seitenleiste, Kopfzeile und Inhaltsbereich."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.kalender import KW
from balanceos.praesentation.seiten.aktivitaeten import AktivitaetenSeite
from balanceos.praesentation.seiten.basis import Seite
from balanceos.praesentation.seiten.dashboard import DashboardSeite
from balanceos.praesentation.seiten.einstellungen import EinstellungenSeite
from balanceos.praesentation.seiten.kompass import KompassSeite
from balanceos.praesentation.seiten.reflexion import ReflexionSeite
from balanceos.praesentation.seiten.statistik import StatistikSeite
from balanceos.praesentation.seiten.woche import WocheSeite
from balanceos.praesentation.zustand import Zustand

SEITEN: list[type[Seite]] = [
    DashboardSeite,
    WocheSeite,
    AktivitaetenSeite,
    StatistikSeite,
    ReflexionSeite,
    KompassSeite,
    EinstellungenSeite,
]
"""Die sieben Seiten in der festen Reihenfolge der Seitenleiste."""


class Hauptfenster(QMainWindow):
    """Hauptfenster von BalanceOS (Spezifikation, Abschnitt „Hauptfenster und Navigation“)."""

    def __init__(self, kontext: AppKontext, zustand: Zustand) -> None:
        """Baut Seitenleiste, Kopfzeile und Seiten auf."""
        super().__init__()
        self.kontext = kontext
        self.zustand = zustand
        self.setWindowTitle("BalanceOS")
        self.setMinimumSize(1280, 720)

        self.seitenleiste = QListWidget()
        self.seitenleiste.setObjectName("seitenleiste")
        self.seitenleiste.setFixedWidth(210)
        self.stapel = QStackedWidget()
        self.seiten: list[Seite] = []
        for klasse in SEITEN:
            seite = klasse(kontext, zustand)
            self.seiten.append(seite)
            self.stapel.addWidget(seite)
            self.seitenleiste.addItem(seite.titel)
        self.seitenleiste.currentRowChanged.connect(self.zeige_seite)

        logo = QLabel("BalanceOS")
        logo.setObjectName("logo")
        untertitel = QLabel("Woche im Gleichgewicht")
        untertitel.setStyleSheet("background:#1F2A37;color:#ADB5BD;padding:0 18px 8px 18px;")
        leiste = QWidget()
        leiste.setStyleSheet("background:#1F2A37;")
        leiste_layout = QVBoxLayout(leiste)
        leiste_layout.setContentsMargins(0, 0, 0, 0)
        leiste_layout.setSpacing(0)
        leiste_layout.addWidget(logo)
        leiste_layout.addWidget(untertitel)
        leiste_layout.addWidget(self.seitenleiste, 1)

        rechts = QWidget()
        rechts_layout = QVBoxLayout(rechts)
        rechts_layout.setContentsMargins(0, 0, 0, 0)
        rechts_layout.setSpacing(0)
        rechts_layout.addWidget(self._kopfzeile())
        inhalt = QWidget()
        inhalt_layout = QVBoxLayout(inhalt)
        inhalt_layout.setContentsMargins(20, 16, 20, 16)
        inhalt_layout.addWidget(self.stapel)
        rechts_layout.addWidget(inhalt, 1)

        zentral = QWidget()
        layout = QHBoxLayout(zentral)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(leiste)
        layout.addWidget(rechts, 1)
        self.setCentralWidget(zentral)

        zustand.woche_geaendert.connect(self._kw_anzeigen)
        self._kw_anzeigen(zustand.kw)
        self.seitenleiste.setCurrentRow(0)

        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.neue_aktivitaet)
        QShortcut(QKeySequence("Alt+Left"), self, activated=lambda: self._blaettern(-1))
        QShortcut(QKeySequence("Alt+Right"), self, activated=lambda: self._blaettern(1))

    def _kopfzeile(self) -> QWidget:
        kopf = QWidget()
        kopf.setObjectName("kopfzeile")
        kopf.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QHBoxLayout(kopf)
        layout.setContentsMargins(20, 10, 20, 10)
        self.titel_label = QLabel()
        self.titel_label.setObjectName("seitentitel")
        self.zurueck_knopf = QPushButton("◀")
        self.zurueck_knopf.setToolTip("Vorherige Woche (Alt+Links)")
        self.zurueck_knopf.setAccessibleName("Vorherige Woche")
        self.kw_label = QLabel()
        self.kw_label.setObjectName("kwLabel")
        self.vor_knopf = QPushButton("▶")
        self.vor_knopf.setToolTip("Nächste Woche (Alt+Rechts)")
        self.vor_knopf.setAccessibleName("Nächste Woche")
        self.heute_knopf = QPushButton("Heute")
        self.heute_knopf.setToolTip("Zur aktuellen Woche springen")
        self.neu_knopf = QPushButton("+ Aktivität")
        self.neu_knopf.setObjectName("primaer")
        self.neu_knopf.setToolTip("Neue Aktivität erfassen (Strg+N)")
        self.zurueck_knopf.clicked.connect(lambda: self._blaettern(-1))
        self.vor_knopf.clicked.connect(lambda: self._blaettern(1))
        self.heute_knopf.clicked.connect(
            lambda: self.zustand.setze_kw(KW.heute(self.kontext.heute()))
        )
        self.neu_knopf.clicked.connect(self.neue_aktivitaet)
        layout.addWidget(self.titel_label)
        layout.addStretch(1)
        for w in (self.zurueck_knopf, self.kw_label, self.vor_knopf, self.heute_knopf):
            layout.addWidget(w)
        layout.addSpacing(16)
        layout.addWidget(self.neu_knopf)
        return kopf

    def _blaettern(self, wochen: int) -> None:
        self.zustand.setze_kw(self.zustand.kw.verschoben(wochen))

    def _kw_anzeigen(self, kw: KW) -> None:
        self.kw_label.setText(kw.zeitraum_text())

    def zeige_seite(self, index: int) -> None:
        """Zeigt die Seite mit dem angegebenen Index an."""
        if index < 0:
            return
        if self.seitenleiste.currentRow() != index:
            self.seitenleiste.setCurrentRow(index)
        self.stapel.setCurrentIndex(index)
        self.titel_label.setText(self.seiten[index].titel)

    def neue_aktivitaet(self) -> None:
        """Öffnet den Dialog „Aktivität erfassen“ (ab Inkrement I2)."""
