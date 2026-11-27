"""Seite „Reflexion“: Wochenreflexion und WHO-5-Fragebogen (US20, US22)."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.fehler import ValidierungsFehler
from balanceos.domaene.kalender import KW
from balanceos.domaene.validierung import M_LEITFRAGE, MAX_LEITFRAGE
from balanceos.domaene.who5 import KEINE_DIAGNOSE
from balanceos.praesentation.dialoge.who5 import Who5Dialog
from balanceos.praesentation.seiten.basis import Seite, etikett, karte, scrollbar
from balanceos.praesentation.widgets.feldfehler import fehlerlabel, markiere
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
    """Drei Leitfragen zur gewählten Woche links, WHO-5 rechts.

    Ungespeicherte Eingaben gehen nicht verloren: Lädt die Seite dieselbe Woche neu,
    etwa nach einer WHO-5-Auswertung, bleiben die Felder unverändert. Vor dem Wechsel
    in eine andere Woche fragt die Seite, ob die Änderungen gespeichert werden sollen.
    """

    titel = "Reflexion"

    def __init__(self, kontext, zustand) -> None:
        """Baut Reflexions- und WHO-5-Bereich auf."""
        super().__init__(kontext, zustand)
        self.fragen_labels: list[QLabel] = []
        self.antwort_felder: list[QPlainTextEdit] = []
        self.zaehler: list[QLabel] = []
        self.feld_fehler: list[QLabel] = []
        self._ungespeichert = False
        self._geladene_kw: KW | None = None
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
            meldung = fehlerlabel()
            zaehler = QLabel()
            zaehler.setObjectName("leise")
            feld.textChanged.connect(lambda i=nr: self._zaehlen(i))
            feld.textChanged.connect(self._bearbeitet)
            self.fragen_labels.append(label)
            self.antwort_felder.append(feld)
            self.feld_fehler.append(meldung)
            self.zaehler.append(zaehler)
            inhalt.addWidget(label)
            inhalt.addWidget(feld)
            inhalt.addWidget(meldung)
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

        self.speichern_knopf.clicked.connect(lambda: self._speichern())
        self.who5_knopf.clicked.connect(lambda: Who5Dialog(self.kontext, self.zustand, self).exec())
        self.stimmung.geaendert.connect(lambda: self.status_label.setText(""))
        self.stimmung.geaendert.connect(self._bearbeitet)
        zustand.woche_geaendert.connect(self._woche_gewechselt)

    def _bearbeitet(self) -> None:
        self._ungespeichert = True

    def _zaehlen(self, nr: int) -> None:
        feld = self.antwort_felder[nr]
        laenge = len(feld.toPlainText())
        label = self.zaehler[nr]
        label.setText(f"{laenge}/{MAX_LEITFRAGE}")
        label.setStyleSheet("color: #E03131;" if laenge > MAX_LEITFRAGE else "")
        markiere(feld, self.feld_fehler[nr], M_LEITFRAGE if laenge > MAX_LEITFRAGE else None)
        zu_lang = any(len(f.toPlainText()) > MAX_LEITFRAGE for f in self.antwort_felder)
        self.speichern_knopf.setEnabled(not zu_lang)
        self.status_label.setText("")

    def _speichern(self, kw: KW | None = None) -> bool:
        """Speichert die Felder für ``kw``, ohne Angabe für die angezeigte Woche.

        Returns:
            ``True`` bei Erfolg, ``False`` bei ungültigen Eingaben.
        """
        kw = kw or self._geladene_kw or self.zustand.kw
        antworten = tuple(f.toPlainText().strip() for f in self.antwort_felder)
        try:
            self.kontext.reflexion.reflexion_speichern(kw, antworten, self.stimmung.wert())
        except ValidierungsFehler as e:
            self.fehler_label.setText(e.fehler[0].meldung)
            self.fehler_label.show()
            return False
        self._ungespeichert = False
        self.fehler_label.hide()
        self.status_label.setText(f"Reflexion für {kw.label()} gespeichert.")
        return True

    def _woche_gewechselt(self) -> None:
        # Ist die Seite sichtbar, fragt ``aktualisieren`` selbst. Verborgen soll die
        # Rückfrage nicht bis zum nächsten Anzeigen warten.
        if not self.isVisible():
            self._wochenwechsel_bestaetigt()

    def _wochenwechsel_bestaetigt(self) -> bool:
        """Fragt vor dem Wechsel in eine andere Woche nach ungespeicherten Änderungen.

        Returns:
            ``True``, wenn die gewählte Woche geladen werden darf. ``False``, wenn die
            Nutzer:in abbricht oder das Speichern scheitert; dann kehrt die Auswahl
            zur bisherigen Woche zurück.
        """
        alt = self._geladene_kw
        if not self._ungespeichert or alt is None or self.zustand.kw == alt:
            return True
        antwort = QMessageBox.question(
            self,
            "Wochenreflexion",
            f"Die Reflexion für {alt.label()} ist noch nicht gespeichert."
            " Möchten Sie die Änderungen speichern?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if antwort == QMessageBox.StandardButton.Discard:
            self._ungespeichert = False
            return True
        if antwort == QMessageBox.StandardButton.Save and self._speichern(alt):
            return True
        # Erst nach dem laufenden Signal zurückwechseln: So erfahren alle Seiten und die
        # Kopfzeile die bisherige Woche wieder in der üblichen Reihenfolge.
        QTimer.singleShot(0, lambda: self.zustand.setze_kw(alt))
        return False

    def aktualisieren(self) -> None:
        """Lädt die Reflexion der gewählten Woche und das letzte WHO-5-Ergebnis.

        Ungespeicherte Eingaben derselben Woche bleiben stehen.
        """
        if not self._wochenwechsel_bestaetigt():
            return
        kw = self.zustand.kw
        if not (self._ungespeichert and kw == self._geladene_kw):
            self._felder_laden(kw)
        self._who5_anzeigen()

    def _felder_laden(self, kw: KW) -> None:
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
        self._geladene_kw = kw
        self._ungespeichert = False

    def _who5_anzeigen(self) -> None:
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
