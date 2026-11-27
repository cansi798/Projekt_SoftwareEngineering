"""Seite „Dashboard“: Wochenbewertung mit Soll-Ist-Balken und Hinweisen (US10–US13, US19)."""

from html import escape

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from balanceos.domaene.bewertung import MIN_TAGE
from balanceos.domaene.modell import Bereichsbewertung, Hinweis
from balanceos.domaene.typen import Bereichstyp
from balanceos.praesentation.dialoge.aktivitaet import aktivitaet_bearbeiten
from balanceos.praesentation.dialoge.begruendung import BegruendungDialog
from balanceos.praesentation.dialoge.lebensbereich import stunden
from balanceos.praesentation.seiten.basis import Seite, karte, leeren, scrollbar
from balanceos.praesentation.stil import FARBE_HINWEISART, SYMBOL_HINWEISART
from balanceos.praesentation.widgets.soll_ist_balken import SollIstBalken

MAX_HINWEISE = 5
TYP_TEXT = {Bereichstyp.MINDESTZIEL: "Mindestziel", Bereichstyp.OBERGRENZE: "Obergrenze"}


class HinweisZeile(QFrame):
    """Ein Hinweis mit Symbol, Text, Regelkennung, „Warum?“ und „Ausblenden“."""

    def __init__(self, hinweis: Hinweis, seite: "DashboardSeite") -> None:
        """Baut die Zeile für einen Hinweis auf."""
        super().__init__()
        self.hinweis = hinweis
        farbe = FARBE_HINWEISART[hinweis.art]
        self.setStyleSheet(
            f"HinweisZeile {{ border-left: 4px solid {farbe}; background: #FBFBFC; }}"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 6, 6)
        symbol = QLabel(SYMBOL_HINWEISART[hinweis.art])
        symbol.setStyleSheet(f"color: {farbe}; font-size: 13pt;")
        symbol.setToolTip(
            {"WARNUNG": "Warnung", "POSITIV": "Positiv", "SYSTEM": "System"}[hinweis.art]
        )
        layout.addWidget(symbol)
        text = QLabel(hinweis.text)
        text.setTextFormat(Qt.TextFormat.PlainText)
        text.setWordWrap(True)
        layout.addWidget(text, 1)
        kennung = QLabel(hinweis.regel)
        kennung.setTextFormat(Qt.TextFormat.PlainText)
        kennung.setObjectName("leise")
        layout.addWidget(kennung)
        self.warum_knopf = QPushButton("Warum?")
        self.warum_knopf.setObjectName("link")
        self.warum_knopf.setToolTip("Begründung mit Modell, Schwelle, Quelle und Evidenzart")
        self.ausblenden_knopf = QPushButton("Ausblenden")
        self.ausblenden_knopf.setObjectName("link")
        self.ausblenden_knopf.setToolTip("Hinweis für diese Woche ausblenden")
        layout.addWidget(self.warum_knopf)
        layout.addWidget(self.ausblenden_knopf)
        self.warum_knopf.clicked.connect(lambda: seite.begruendung_zeigen(hinweis))
        self.ausblenden_knopf.clicked.connect(lambda: seite.ausblenden(hinweis))


class DashboardSeite(Seite):
    """Übersicht der gewählten Woche oder, bei leerer Datenbank, ein Einstieg in drei Schritten."""

    titel = "Dashboard"

    def __init__(self, kontext, zustand) -> None:
        """Baut leere Ansicht und Inhaltsansicht auf."""
        super().__init__(kontext, zustand)
        self.score_labels: dict[int, QLabel] = {}
        self.abweichung_labels: dict[int, QLabel] = {}
        self.hinweis_zeilen: list[HinweisZeile] = []
        self._hinweise: list[Hinweis] = []
        haupt = QVBoxLayout(self)
        haupt.setContentsMargins(0, 0, 0, 0)
        self.stapel = QStackedWidget()
        haupt.addWidget(self.stapel)
        self.leer_ansicht = self._leer_aufbauen()
        innen = QWidget()
        self._inhalt_layout = QVBoxLayout(innen)
        self._inhalt_layout.setContentsMargins(20, 16, 20, 16)
        self._inhalt_layout.setSpacing(14)
        self._inhalt_aufbauen()
        self.stapel.addWidget(self.leer_ansicht)
        self.inhalt = scrollbar(innen)
        self.stapel.addWidget(self.inhalt)

    # --- Aufbau ---------------------------------------------------------------------------

    def _leer_aufbauen(self) -> QWidget:
        seite = QWidget()
        layout = QVBoxLayout(seite)
        layout.setContentsMargins(60, 40, 60, 40)
        rahmen, inhalt = karte("Willkommen bei BalanceOS")
        einleitung = QLabel(
            "Noch sind keine Aktivitäten erfasst. In drei Schritten zur ersten Wochenauswertung:"
        )
        einleitung.setWordWrap(True)
        inhalt.addWidget(einleitung)
        schritte = [
            (
                "Wunschprofil prüfen",
                "Unter „Einstellungen“ legen Sie fest, wie viele Stunden pro Woche Sie sich für"
                " jeden Lebensbereich wünschen.",
            ),
            (
                "Aktivitäten erfassen",
                "Tragen Sie ein, womit Sie Ihre Zeit verbringen, an mindestens vier Tagen der"
                " Woche.",
            ),
            (
                "Woche auswerten",
                "Das Dashboard vergleicht Wunsch und Wirklichkeit und zeigt begründete Hinweise.",
            ),
        ]
        for nr, (titel, text) in enumerate(schritte, start=1):
            zeile = QLabel(f"<b>{nr}. {titel}</b><br>{text}")
            zeile.setWordWrap(True)
            zeile.setContentsMargins(0, 8, 0, 0)
            inhalt.addWidget(zeile)
        knoepfe = QHBoxLayout()
        self.erste_aktivitaet_knopf = QPushButton("Erste Aktivität erfassen")
        self.erste_aktivitaet_knopf.setObjectName("primaer")
        self.demodaten_knopf = QPushButton("Demodaten laden")
        self.demodaten_knopf.setToolTip("Acht Wochen Beispieldaten zum Ausprobieren laden")
        knoepfe.addWidget(self.erste_aktivitaet_knopf)
        knoepfe.addWidget(self.demodaten_knopf)
        knoepfe.addStretch(1)
        inhalt.addSpacing(12)
        inhalt.addLayout(knoepfe)
        layout.addWidget(rahmen)
        layout.addStretch(1)
        self.erste_aktivitaet_knopf.clicked.connect(self._erste_aktivitaet)
        self.demodaten_knopf.clicked.connect(self.demodaten_laden)
        return seite

    def _inhalt_aufbauen(self) -> None:
        kacheln = QHBoxLayout()
        kacheln.setSpacing(14)
        rahmen, inhalt = karte("Datenvollständigkeit")
        zeile = QHBoxLayout()
        self.vollstaendigkeit_label = QLabel()
        self.vollstaendigkeit_label.setObjectName("grosszahl")
        zeile.addWidget(self.vollstaendigkeit_label)
        tage = QLabel("Tage")
        tage.setObjectName("leise")
        zeile.addWidget(tage, alignment=Qt.AlignmentFlag.AlignBottom)
        zeile.addStretch(1)
        inhalt.addLayout(zeile)
        self.vollstaendigkeit_text = QLabel()
        self.vollstaendigkeit_text.setObjectName("leise")
        self.vollstaendigkeit_text.setWordWrap(True)
        inhalt.addWidget(self.vollstaendigkeit_text)
        kacheln.addWidget(rahmen, 1)

        self.gesamt_karte, inhalt = karte("Gesamt-Score")
        zeile = QHBoxLayout()
        self.gesamt_label = QLabel()
        self.gesamt_label.setObjectName("grosszahl")
        zeile.addWidget(self.gesamt_label)
        von = QLabel("/ 100")
        von.setObjectName("leise")
        zeile.addWidget(von, alignment=Qt.AlignmentFlag.AlignBottom)
        zeile.addStretch(1)
        inhalt.addLayout(zeile)
        hinweis = QLabel("programmeigener Score, nicht validiert · gewichteter Mittelwert")
        hinweis.setObjectName("leise")
        hinweis.setWordWrap(True)
        inhalt.addWidget(hinweis)
        kacheln.addWidget(self.gesamt_karte, 1)
        kacheln.addStretch(0)
        self._inhalt_layout.addLayout(kacheln)

        rahmen, inhalt = karte("Lebensbereiche: Wunsch und Wirklichkeit")
        self._raster = QGridLayout()
        self._raster.setHorizontalSpacing(14)
        self._raster.setVerticalSpacing(6)
        inhalt.addLayout(self._raster)
        legende = QLabel(
            '<span style="color:#2F9E44">■</span> Soll erreicht &nbsp;&nbsp;'
            '<span style="color:#E03131">■</span> über Obergrenze &nbsp;&nbsp;'
            "│ Soll &nbsp;&nbsp; Balken bis 150 % des Solls &nbsp;&nbsp;"
            "Score 0–100: programmeigen, nicht validiert"
        )
        legende.setObjectName("leise")
        legende.setWordWrap(True)
        inhalt.addWidget(legende)
        self._inhalt_layout.addWidget(rahmen)

        rahmen, inhalt = karte()
        kopf = QHBoxLayout()
        self.hinweise_titel = QLabel()
        self.hinweise_titel.setObjectName("kartentitel")
        kopf.addWidget(self.hinweise_titel)
        kopf.addStretch(1)
        self.alle_hinweise_knopf = QPushButton()
        self.alle_hinweise_knopf.setObjectName("link")
        kopf.addWidget(self.alle_hinweise_knopf)
        inhalt.addLayout(kopf)
        self._hinweis_layout = QVBoxLayout()
        self._hinweis_layout.setSpacing(6)
        inhalt.addLayout(self._hinweis_layout)
        self._inhalt_layout.addWidget(rahmen)
        self._inhalt_layout.addStretch(1)
        self.alle_hinweise_knopf.clicked.connect(self.alle_hinweise_zeigen)

    # --- Aktualisieren --------------------------------------------------------------------

    def aktualisieren(self) -> None:
        """Berechnet Bewertung und Hinweise der gewählten Woche neu."""
        if not self.kontext.auswertung.gibt_aktivitaeten():
            self.stapel.setCurrentWidget(self.leer_ansicht)
            return
        self.stapel.setCurrentWidget(self.inhalt)
        kw = self.zustand.kw
        bewertung = self.kontext.auswertung.wochenbewertung(kw)
        einstellungen = self.kontext.stammdaten.einstellungen()

        self.vollstaendigkeit_label.setText(f"{bewertung.vollstaendigkeit_tage}/7")
        if bewertung.ausreichende_daten:
            self.vollstaendigkeit_text.setText(
                f"ausreichend für die Bewertung (mindestens {MIN_TAGE} Tage)"
            )
        else:
            self.vollstaendigkeit_text.setText(
                f"zu wenig Daten: Scores erscheinen ab {MIN_TAGE} Tagen mit Einträgen"
            )
        self.gesamt_karte.setVisible(einstellungen.gesamtscore_anzeigen)
        self.gesamt_label.setText(
            "–" if bewertung.gesamtscore is None else str(bewertung.gesamtscore)
        )

        self._bereiche_fuellen(bewertung)
        self._hinweise = self.kontext.auswertung.hinweise(kw)
        self._hinweise_fuellen()

    def _bereiche_fuellen(self, bewertung) -> None:
        leeren(self._raster)
        self.score_labels = {}
        self.abweichung_labels = {}
        for spalte, titel in enumerate(
            ["Lebensbereich", "Typ", "Soll-Ist-Balken", "Ist / Soll", "Ist − Soll", "Score"]
        ):
            kopf = QLabel(titel)
            kopf.setObjectName("leise")
            self._raster.addWidget(kopf, 0, spalte)
        bereiche = {b.id: b for b in self.kontext.stammdaten.alle_bereiche()}
        for zeile, bw in enumerate(bewertung.bereiche, start=1):
            b = bereiche[bw.lebensbereich_id]
            name = QLabel(f'<span style="color:{b.farbe}">●</span> {escape(b.name)}')
            name.setTextFormat(Qt.TextFormat.RichText)
            self._raster.addWidget(name, zeile, 0)
            typ = QLabel(TYP_TEXT[b.typ])
            typ.setObjectName("leise")
            self._raster.addWidget(typ, zeile, 1)
            balken = SollIstBalken()
            balken.setze(bw, b.typ, b.farbe)
            self._raster.addWidget(balken, zeile, 2)
            self._raster.addWidget(QLabel(balken.text()), zeile, 3)
            abweichung = QLabel(abweichung_text(bw))
            abweichung.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.abweichung_labels[b.id] = abweichung
            self._raster.addWidget(abweichung, zeile, 4)
            if bw.zielerfuellung is None:
                score = QLabel("kein Soll festgelegt")
                score.setObjectName("leise")
            elif bw.score is None:
                score = QLabel("zu wenig Daten")
                score.setObjectName("leise")
                score.setToolTip(f"Scores erscheinen ab {MIN_TAGE} Tagen mit Einträgen")
            else:
                score = QLabel(str(bw.score))
                score.setStyleSheet("font-weight: 600;")
            score.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.score_labels[b.id] = score
            self._raster.addWidget(score, zeile, 5)
        self._raster.setColumnStretch(2, 1)

    def _hinweise_fuellen(self) -> None:
        leeren(self._hinweis_layout)
        self.hinweis_zeilen = []
        anzahl = len(self._hinweise)
        self.hinweise_titel.setText(f"Hinweise der Woche ({anzahl})")
        self.alle_hinweise_knopf.setText(f"Alle Hinweise ({anzahl})")
        self.alle_hinweise_knopf.setVisible(anzahl > MAX_HINWEISE)
        for hinweis in self._hinweise[:MAX_HINWEISE]:
            zeile = HinweisZeile(hinweis, self)
            self.hinweis_zeilen.append(zeile)
            self._hinweis_layout.addWidget(zeile)
        if not self._hinweise:
            self._hinweis_layout.addWidget(HinweisLeer())

    # --- Aktionen -------------------------------------------------------------------------

    def begruendung_zeigen(self, hinweis: Hinweis) -> None:
        """Öffnet den Dialog „Warum sehe ich das?“."""
        BegruendungDialog(hinweis, self.kontext, self.zustand, self).exec()

    def ausblenden(self, hinweis: Hinweis) -> None:
        """Blendet einen Hinweis für die Woche aus und aktualisiert die Anzeige."""
        self.kontext.auswertung.hinweis_ausblenden(hinweis)
        self.zustand.daten_geaendert.emit()

    def alle_hinweise_zeigen(self) -> None:
        """Zeigt alle Hinweise der Woche in einem eigenen Fenster."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Alle Hinweise · {self.zustand.kw.zeitraum_text()}")
        dialog.setMinimumWidth(720)
        layout = QVBoxLayout(dialog)
        inhalt = QWidget()
        liste = QVBoxLayout(inhalt)
        for hinweis in self._hinweise:
            liste.addWidget(HinweisZeile(hinweis, self))
        liste.addStretch(1)
        layout.addWidget(scrollbar(inhalt))
        schliessen = QPushButton("Schließen")
        schliessen.clicked.connect(dialog.accept)
        layout.addWidget(schliessen, alignment=Qt.AlignmentFlag.AlignRight)
        self.zustand.daten_geaendert.connect(dialog.accept)
        dialog.exec()
        self.zustand.daten_geaendert.disconnect(dialog.accept)

    def _erste_aktivitaet(self) -> None:
        aktivitaet_bearbeiten(self.kontext, self.zustand, datum=self.kontext.heute(), parent=self)

    def demodaten_laden(self) -> None:
        """Lädt die Demodaten und zeigt eine Woche mit ausreichend Daten (US18)."""
        from balanceos.praesentation.dialoge.demodaten import demodaten_laden

        demodaten_laden(self.kontext, self.zustand, self)


def abweichung_text(bewertung: Bereichsbewertung) -> str:
    """Abweichung Ist − Soll mit Vorzeichen, z. B. „+6 h“ oder „−1,5 h“ (US10).

    Ohne Soll gibt es keine Abweichung; dann erscheint „–“.
    """
    if bewertung.zielerfuellung is None:
        return "–"
    wert = bewertung.abweichung
    if stunden(abs(wert)) == "0":
        return "0 h"
    return f"{'+' if wert > 0 else '−'}{stunden(abs(wert))} h"


class HinweisLeer(QLabel):
    """Platzhalter, wenn die Woche keine Hinweise hat."""

    def __init__(self) -> None:
        """Erzeugt den Platzhaltertext."""
        super().__init__("Keine Hinweise für diese Woche.")
        self.setObjectName("leise")
