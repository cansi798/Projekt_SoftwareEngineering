"""Seite „Reflexion“: Wochenreflexion und WHO-5-Fragebogen (US20, US22)."""

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.fehler import ValidierungsFehler
from balanceos.domaene.validierung import MAX_LEITFRAGE
from balanceos.domaene.who5 import KEINE_DIAGNOSE
from balanceos.praesentation.dialoge.who5 import Who5Dialog
from balanceos.praesentation.seiten.basis import Seite, etikett, karte, scrollbar
from balanceos.praesentation.widgets.feldfehler import fehlerlabel
from balanceos.praesentation.widgets.skala import Skala

LEITFRAGEN = (
    "Was ist diese Woche gut gelungen?",
    "Was ist zu kurz gekommen?",
    "Was nehme ich mir für die nächste Woche vor?",
)

STIMMUNG_TOOLTIPS = {
    1: "sehr schlecht",
    2: "eher schlecht",
    3: "mittel",
    4: "eher gut",
    5: "sehr gut",
}


class ReflexionSeite(Seite):
    """Drei Leitfragen zur gewählten Woche links, WHO-5 rechts."""

    titel = "Reflexion"

    def __init__(self, kontext, zustand) -> None:
        """Baut Reflexions- und WHO-5-Bereich auf."""
        super().__init__(kontext, zustand)
        self.fragen_labels: list[QLabel] = []
        self.antwort_felder: list[QPlainTextEdit] = []
        self.zaehler: list[QLabel] = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        innen = QWidget()
        links = QVBoxLayout(innen)
        rahmen, inhalt = karte("Wochenreflexion")
        self.kw_label = QLabel()
        self.kw_label.setStyleSheet("font-weight: 600;")
        inhalt.addWidget(self.kw_label)
        for nr, frage in enumerate(LEITFRAGEN):
            label = QLabel(frage)
            feld = QPlainTextEdit()
            feld.setFixedHeight(90)
            feld.setTabChangesFocus(True)
            label.setBuddy(feld)
            zaehler = QLabel()
            zaehler.setObjectName("leise")
            feld.textChanged.connect(lambda i=nr: self._zaehlen(i))
            self.fragen_labels.append(label)
            self.antwort_felder.append(feld)
            self.zaehler.append(zaehler)
            inhalt.addWidget(label)
            inhalt.addWidget(feld)
            inhalt.addWidget(zaehler)
        zeile = QHBoxLayout()
        zeile.addWidget(QLabel("Stimmung der Woche (optional):"))
        self.stimmung = Skala(1, 5, mit_leer=True, tooltips=STIMMUNG_TOOLTIPS)
        zeile.addWidget(self.stimmung, 1)
        inhalt.addLayout(zeile)
        self.fehler_label = fehlerlabel()
        inhalt.addWidget(self.fehler_label)
        knoepfe = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setObjectName("leise")
        knoepfe.addWidget(self.status_label, 1)
        self.speichern_knopf = QPushButton("Speichern")
        self.speichern_knopf.setObjectName("primaer")
        knoepfe.addWidget(self.speichern_knopf)
        inhalt.addLayout(knoepfe)
        links.addWidget(rahmen)
        links.addStretch(1)
        layout.addWidget(scrollbar(innen), 3)

        rechts = QVBoxLayout()
        who5_rahmen, who5 = karte("WHO-5-Wohlbefinden")
        kopf = QHBoxLayout()
        self.who5_etikett = etikett("validiertes Instrument", "#2F9E44")
        kopf.addWidget(self.who5_etikett)
        kopf.addStretch(1)
        who5.addLayout(kopf)
        self.who5_label = QLabel()
        self.who5_label.setWordWrap(True)
        who5.addWidget(self.who5_label)
        erklaerung = QLabel(KEINE_DIAGNOSE)
        erklaerung.setObjectName("leise")
        erklaerung.setWordWrap(True)
        who5.addWidget(erklaerung)
        self.who5_knopf = QPushButton("WHO-5-Fragebogen ausfüllen …")
        who5.addWidget(self.who5_knopf)
        rechts.addWidget(who5_rahmen)
        rechts.addStretch(1)
        layout.addLayout(rechts, 2)

        self.speichern_knopf.clicked.connect(self._speichern)
        self.who5_knopf.clicked.connect(lambda: Who5Dialog(self.kontext, self.zustand, self).exec())
        self.stimmung.geaendert.connect(lambda: self.status_label.setText(""))

    def _zaehlen(self, nr: int) -> None:
        laenge = len(self.antwort_felder[nr].toPlainText())
        label = self.zaehler[nr]
        label.setText(f"{laenge}/{MAX_LEITFRAGE}")
        label.setStyleSheet("color: #E03131;" if laenge > MAX_LEITFRAGE else "")
        zu_lang = any(len(f.toPlainText()) > MAX_LEITFRAGE for f in self.antwort_felder)
        self.speichern_knopf.setEnabled(not zu_lang)
        self.status_label.setText("")

    def _speichern(self) -> None:
        antworten = tuple(f.toPlainText().strip() for f in self.antwort_felder)
        try:
            self.kontext.reflexion.reflexion_speichern(
                self.zustand.kw, antworten, self.stimmung.wert()
            )
        except ValidierungsFehler as e:
            self.fehler_label.setText(e.fehler[0].meldung)
            self.fehler_label.show()
            return
        self.fehler_label.hide()
        self.status_label.setText(f"Reflexion für {self.zustand.kw.label()} gespeichert.")

    def aktualisieren(self) -> None:
        """Lädt die Reflexion der gewählten Woche und das letzte WHO-5-Ergebnis."""
        kw = self.zustand.kw
        self.kw_label.setText(kw.zeitraum_text())
        r = self.kontext.reflexion.reflexion(kw)
        antworten = r.antworten if r else ("", "", "")
        for feld, text in zip(self.antwort_felder, antworten, strict=True):
            feld.blockSignals(True)
            feld.setPlainText(text)
            feld.blockSignals(False)
        for nr in range(len(self.antwort_felder)):
            self._zaehlen(nr)
        self.stimmung.blockSignals(True)
        self.stimmung.setze(r.stimmung if r else None)
        self.stimmung.blockSignals(False)
        self.fehler_label.hide()
        self.status_label.setText("")

        verlauf = self.kontext.reflexion.who5_verlauf()
        if not verlauf:
            self.who5_label.setText("Noch kein Fragebogen ausgefüllt.")
            return
        letzte = verlauf[-1]
        text = (
            f"Letztes Ergebnis vom {letzte.datum:%d.%m.%Y}: <b>{letzte.prozentwert} %</b>"
            f" (Rohwert {letzte.rohwert} von 25)"
        )
        if len(verlauf) > 1:
            text += "<br>Bisher: " + ", ".join(
                f"{e.datum:%d.%m.} {e.prozentwert} %" for e in verlauf[-5:-1]
            )
        self.who5_label.setText(text)
