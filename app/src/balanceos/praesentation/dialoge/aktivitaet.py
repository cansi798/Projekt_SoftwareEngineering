"""Dialog „Aktivität erfassen“ bzw. „Aktivität bearbeiten“ (US05–US08)."""

from dataclasses import replace
from datetime import date, datetime, time, timedelta

from PySide6.QtCore import QDate, Qt, QTime
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from balanceos.anwendung.fehler import RegelVerletzung, ValidierungsFehler
from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.kalender import MAX_DAUER_MINUTEN, berechne_dauer, stunden_text
from balanceos.domaene.modell import Aktivitaet, Wiederholungsserie
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel, Wochentag
from balanceos.domaene.validierung import MAX_NOTIZ, MAX_TITEL, Fehler, pruefe_serie
from balanceos.praesentation.texte import BEWEGUNGSART_TEXT, STATUS_TEXT, WOCHENTAG_TEXT
from balanceos.praesentation.widgets.auswahl import Auswahl
from balanceos.praesentation.widgets.feldfehler import fehlerlabel, markiere
from balanceos.praesentation.widgets.skala import Skala
from balanceos.praesentation.zustand import Zustand

FELDNAMEN = {
    "titel": "Titel",
    "lebensbereich": "Lebensbereich",
    "zeit": "Beginn und Ende",
    "dauer": "Dauer",
    "status": "Status",
    "bewertung": "Bewertung",
    "bewegungsart": "Bewegungsart",
    "notiz": "Notiz",
    "wochentage": "Wochentage",
    "enddatum": "Enddatum",
}
SKALA_TEXTE = {
    "zufriedenheit": {1: "sehr unzufrieden", 5: "sehr zufrieden"},
    "belastung": {1: "kaum belastend", 5: "sehr belastend"},
    "erholung": {1: "kaum erholsam", 5: "sehr erholsam"},
}
STANDARD_BEGINN = time(8, 0)


def _qdate(d: date) -> QDate:
    return QDate(d.year, d.month, d.day)


def _qtime(t: time) -> QTime:
    return QTime(t.hour, t.minute)


class AktivitaetDialog(QDialog):
    """Erfassen und Bearbeiten einer Aktivität, optional als wöchentliche Serie.

    Jede Eingabe wird sofort gegen die Gültigkeitsregeln geprüft. Meldungen
    erscheinen unter dem Feld, sobald es bearbeitet oder verlassen wurde;
    „Speichern“ ist nur bei gültigen Eingaben aktiv und nennt im Tooltip die
    offenen Felder.
    """

    def __init__(
        self,
        kontext: AppKontext,
        zustand: Zustand,
        aktivitaet: Aktivitaet | None = None,
        datum: date | None = None,
        beginn: time | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Erzeugt den Dialog für eine neue (``aktivitaet is None``) oder bestehende Aktivität."""
        super().__init__(parent)
        self._kontext = kontext
        self._zustand = zustand
        self._service = kontext.aktivitaeten
        self._bearbeiten = aktivitaet is not None
        self._original = aktivitaet or self._service.vorbelegung(datum or kontext.heute(), beginn)
        if not self._bearbeiten and beginn is not None:
            self._original.ende = (
                datetime.combine(date.min, beginn) + timedelta(minutes=self._original.dauer_minuten)
            ).time()
        self._serie = (
            self._service.serie(self._original.serie_id) if self._original.serie_id else None
        )
        self._beruehrt: set[str] = set()
        self._status_manuell = self._bearbeiten
        self._laedt = True
        self.fehlerlabels: dict[str, QLabel] = {}

        self.setWindowTitle("Aktivität bearbeiten" if self._bearbeiten else "Aktivität erfassen")
        self.setMinimumWidth(780)
        self._aufbauen()
        self._werte_setzen(self._original)
        self._laedt = False
        self._pruefen()

    # --- Aufbau ---------------------------------------------------------------------------

    def _fehler(self, schluessel: str) -> QLabel:
        label = fehlerlabel()
        self.fehlerlabels[schluessel] = label
        return label

    def _mit_fehler(self, feld: QWidget, schluessel: str) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(feld)
        layout.addWidget(self._fehler(schluessel))
        return box

    def _aufbauen(self) -> None:
        haupt = QVBoxLayout(self)
        spalten = QHBoxLayout()
        haupt.addLayout(spalten)

        links = QFormLayout()
        links.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.titel_feld = QLineEdit()
        self.titel_feld.setMaxLength(MAX_TITEL + 20)
        self.titel_feld.setPlaceholderText("z. B. Joggen")
        links.addRow("Titel*", self._mit_fehler(self.titel_feld, "titel"))

        self.bereich_feld = Auswahl()
        self._bereiche = {b.id: b for b in self._kontext.stammdaten.alle_bereiche()}
        for b in self._bereiche.values():
            if b.aktiv or b.id == self._original.lebensbereich_id and self._bearbeiten:
                self.bereich_feld.addItem(b.name + ("" if b.aktiv else " (inaktiv)"), b.id)
        links.addRow("Lebensbereich*", self._mit_fehler(self.bereich_feld, "lebensbereich"))

        self.datum_feld = QDateEdit()
        self.datum_feld.setDisplayFormat("dd.MM.yyyy")
        self.datum_feld.setCalendarPopup(True)
        links.addRow("Datum*", self.datum_feld)

        modus = QWidget()
        modus_layout = QHBoxLayout(modus)
        modus_layout.setContentsMargins(0, 0, 0, 0)
        self.modus_zeit = QRadioButton("Beginn und Ende")
        self.modus_dauer = QRadioButton("Dauer")
        gruppe = QButtonGroup(self)
        gruppe.addButton(self.modus_zeit)
        gruppe.addButton(self.modus_dauer)
        modus_layout.addWidget(self.modus_zeit)
        modus_layout.addWidget(self.modus_dauer)
        modus_layout.addStretch(1)
        links.addRow("Zeitangabe", modus)

        zeit = QWidget()
        zeit_layout = QHBoxLayout(zeit)
        zeit_layout.setContentsMargins(0, 0, 0, 0)
        self.beginn_feld = QTimeEdit()
        self.beginn_feld.setDisplayFormat("HH:mm")
        self.ende_feld = QTimeEdit()
        self.ende_feld.setDisplayFormat("HH:mm")
        zeit_layout.addWidget(self.beginn_feld)
        zeit_layout.addWidget(QLabel("bis"))
        zeit_layout.addWidget(self.ende_feld)
        self.folgetag_label = QLabel("endet am Folgetag")
        self.folgetag_label.setObjectName("leise")
        zeit_layout.addWidget(self.folgetag_label)
        zeit_layout.addStretch(1)
        self._zeit_zeile = self._mit_fehler(zeit, "zeit")
        links.addRow("Uhrzeit", self._zeit_zeile)

        self.dauer_feld = QSpinBox()
        self.dauer_feld.setRange(0, MAX_DAUER_MINUTEN + 1)
        self.dauer_feld.setSuffix(" min")
        self.dauer_feld.setSingleStep(15)
        self._dauer_zeile = self._mit_fehler(self.dauer_feld, "dauer")
        links.addRow("Dauer", self._dauer_zeile)
        self.dauer_info = QLabel()
        self.dauer_info.setObjectName("leise")
        links.addRow("", self.dauer_info)

        self.status_feld = Auswahl()
        for status, text in STATUS_TEXT.items():
            self.status_feld.addItem(text, status)
        links.addRow("Status", self._mit_fehler(self.status_feld, "status"))

        rechts = QFormLayout()
        self.skalen: dict[str, Skala] = {}
        for schluessel, beschriftung in (
            ("zufriedenheit", "Zufriedenheit"),
            ("belastung", "Belastung"),
            ("erholung", "Erholung"),
        ):
            skala = Skala(tooltips=SKALA_TEXTE[schluessel])
            self.skalen[schluessel] = skala
            rechts.addRow(beschriftung, skala)
        rechts.addRow("", self._fehler("bewertung"))

        self.bewegungsart_label = QLabel("Bewegungsart")
        self.bewegungsart_feld = Auswahl()
        self.bewegungsart_feld.addItem("keine Angabe", None)
        for art, text in BEWEGUNGSART_TEXT.items():
            self.bewegungsart_feld.addItem(text, art)
        rechts.addRow(self.bewegungsart_label, self.bewegungsart_feld)

        self.notiz_feld = QPlainTextEdit()
        self.notiz_feld.setPlaceholderText("optional")
        self.notiz_feld.setFixedHeight(90)
        self.notiz_feld.setTabChangesFocus(True)
        self.notiz_zaehler = QLabel()
        self.notiz_zaehler.setObjectName("leise")
        notiz = QWidget()
        notiz_layout = QVBoxLayout(notiz)
        notiz_layout.setContentsMargins(0, 0, 0, 0)
        notiz_layout.setSpacing(2)
        notiz_layout.addWidget(self.notiz_feld)
        notiz_layout.addWidget(self.notiz_zaehler, alignment=Qt.AlignmentFlag.AlignRight)
        notiz_layout.addWidget(self._fehler("notiz"))
        rechts.addRow("Notiz", notiz)

        spalten.addLayout(links, 1)
        spalten.addSpacing(20)
        spalten.addLayout(rechts, 1)

        haupt.addWidget(self._wiederholung_aufbauen())

        self.serie_anwenden = QCheckBox(
            "Änderungen auf alle zukünftigen Termine der Serie anwenden"
        )
        haupt.addWidget(self.serie_anwenden)

        knoepfe = QHBoxLayout()
        self.loeschen_knopf = QPushButton("Löschen")
        self.loeschen_knopf.setObjectName("gefahr")
        self.ueberspringen_knopf = QPushButton("Termin überspringen")
        self.serie_loeschen_knopf = QPushButton("Serie löschen")
        self.serie_loeschen_knopf.setObjectName("gefahr")
        abbrechen = QPushButton("Abbrechen")
        self.speichern_knopf = QPushButton("Speichern")
        self.speichern_knopf.setObjectName("primaer")
        self.speichern_knopf.setDefault(True)
        for knopf in (self.loeschen_knopf, self.ueberspringen_knopf, self.serie_loeschen_knopf):
            knopf.setAutoDefault(False)
            knoepfe.addWidget(knopf)
        knoepfe.addStretch(1)
        abbrechen.setAutoDefault(False)
        knoepfe.addWidget(abbrechen)
        knoepfe.addWidget(self.speichern_knopf)
        haupt.addLayout(knoepfe)

        ist_termin = self._serie is not None
        self.loeschen_knopf.setVisible(self._bearbeiten)
        self.ueberspringen_knopf.setVisible(self._bearbeiten and ist_termin)
        self.serie_loeschen_knopf.setVisible(self._bearbeiten and ist_termin)
        self.serie_anwenden.setVisible(self._bearbeiten and ist_termin)
        self.wiederholen_feld.setVisible(not self._bearbeiten)
        self._wiederholung_box.setVisible(False)

        for signal in (
            self.titel_feld.textChanged,
            self.bereich_feld.currentIndexChanged,
            self.datum_feld.dateChanged,
            self.modus_zeit.toggled,
            self.beginn_feld.timeChanged,
            self.ende_feld.timeChanged,
            self.dauer_feld.valueChanged,
            self.status_feld.currentIndexChanged,
            self.bewegungsart_feld.currentIndexChanged,
            self.notiz_feld.textChanged,
            self.wiederholen_feld.toggled,
            self.enddatum_aktiv.toggled,
            self.enddatum_feld.dateChanged,
            *(s.geaendert for s in self.skalen.values()),
            *(c.toggled for c in self.wochentag_felder.values()),
        ):
            signal.connect(self._pruefen)
        self.titel_feld.editingFinished.connect(lambda: self._beruehren("titel"))
        self.titel_feld.textEdited.connect(lambda: self._beruehren("titel"))
        self.beginn_feld.timeChanged.connect(lambda: self._beruehren("zeit"))
        self.ende_feld.timeChanged.connect(lambda: self._beruehren("zeit"))
        self.dauer_feld.valueChanged.connect(lambda: self._beruehren("dauer"))
        self.status_feld.activated.connect(self._status_gewaehlt)
        self.datum_feld.dateChanged.connect(self._datum_geaendert)
        self.modus_zeit.toggled.connect(self._modus_geaendert)
        self.wiederholen_feld.toggled.connect(self._wiederholung_box.setVisible)
        self.enddatum_aktiv.toggled.connect(self.enddatum_feld.setEnabled)
        self.enddatum_aktiv.toggled.connect(lambda: self._beruehren("enddatum"))
        self.enddatum_feld.dateChanged.connect(lambda: self._beruehren("enddatum"))
        for feld in self.wochentag_felder.values():
            feld.toggled.connect(lambda: self._beruehren("wochentage"))
        self.speichern_knopf.clicked.connect(self._speichern)
        abbrechen.clicked.connect(self.reject)
        self.loeschen_knopf.clicked.connect(self._loeschen)
        self.ueberspringen_knopf.clicked.connect(self._ueberspringen)
        self.serie_loeschen_knopf.clicked.connect(self._serie_loeschen)

    def _wiederholung_aufbauen(self) -> QWidget:
        box = QWidget()
        layout = QVBoxLayout(box)
        layout.setContentsMargins(0, 8, 0, 0)
        self.wiederholen_feld = QCheckBox("Wöchentlich wiederholen")
        layout.addWidget(self.wiederholen_feld)
        self._wiederholung_box = QWidget()
        raster = QGridLayout(self._wiederholung_box)
        raster.setContentsMargins(24, 0, 0, 0)
        tage = QHBoxLayout()
        self.wochentag_felder: dict[Wochentag, QCheckBox] = {}
        for tag, text in WOCHENTAG_TEXT.items():
            feld = QCheckBox(text)
            self.wochentag_felder[tag] = feld
            tage.addWidget(feld)
        tage.addStretch(1)
        raster.addWidget(QLabel("an"), 0, 0)
        raster.addLayout(tage, 0, 1)
        raster.addWidget(self._fehler("wochentage"), 1, 1)
        self.enddatum_aktiv = QCheckBox("Enddatum")
        self.enddatum_feld = QDateEdit()
        self.enddatum_feld.setDisplayFormat("dd.MM.yyyy")
        self.enddatum_feld.setCalendarPopup(True)
        self.enddatum_feld.setEnabled(False)
        ende = QHBoxLayout()
        ende.addWidget(self.enddatum_aktiv)
        ende.addWidget(self.enddatum_feld)
        hinweis = QLabel("ohne Enddatum: 52 Wochen im Voraus")
        hinweis.setObjectName("leise")
        ende.addWidget(hinweis)
        ende.addStretch(1)
        raster.addLayout(ende, 2, 1)
        raster.addWidget(self._fehler("enddatum"), 3, 1)
        layout.addWidget(self._wiederholung_box)
        return box

    def _werte_setzen(self, a: Aktivitaet) -> None:
        self.titel_feld.setText(a.titel)
        index = self.bereich_feld.findData(a.lebensbereich_id)
        self.bereich_feld.setCurrentIndex(max(0, index))
        self.datum_feld.setDate(_qdate(a.datum))
        mit_zeit = a.beginn is not None
        self.modus_zeit.setChecked(mit_zeit)
        self.modus_dauer.setChecked(not mit_zeit)
        beginn = a.beginn or STANDARD_BEGINN
        ende = (
            a.ende
            or (datetime.combine(date.min, beginn) + timedelta(minutes=a.dauer_minuten)).time()
        )
        self.beginn_feld.setTime(_qtime(beginn))
        self.ende_feld.setTime(_qtime(ende))
        self.dauer_feld.setValue(a.dauer_minuten)
        self.status_feld.setCurrentIndex(self.status_feld.findData(a.status))
        self.skalen["zufriedenheit"].setze(a.zufriedenheit)
        self.skalen["belastung"].setze(a.belastung)
        self.skalen["erholung"].setze(a.erholung)
        self.bewegungsart_feld.setCurrentIndex(
            max(0, self.bewegungsart_feld.findData(a.bewegungsart))
        )
        self.notiz_feld.setPlainText(a.notiz or "")
        self.wochentag_felder[Wochentag.aus_datum(a.datum)].setChecked(True)
        self.enddatum_feld.setDate(_qdate(a.datum + timedelta(weeks=4)))
        if self._serie is not None and self._serie.enddatum is not None:
            self.enddatum_feld.setDate(_qdate(self._serie.enddatum))
        self._modus_geaendert()

    # --- Reaktionen -----------------------------------------------------------------------

    def _beruehren(self, schluessel: str) -> None:
        if not self._laedt:
            self._beruehrt.add(schluessel)
            self._pruefen()

    def _status_gewaehlt(self) -> None:
        self._status_manuell = True
        self._beruehren("status")

    def _datum_geaendert(self) -> None:
        if self._laedt:
            return
        if not self._status_manuell:
            vorschlag = self._service.vorbelegung(self.datum_feld.date().toPython()).status
            self.status_feld.setCurrentIndex(self.status_feld.findData(vorschlag))
        self._beruehren("status")

    def _modus_geaendert(self) -> None:
        mit_zeit = self.modus_zeit.isChecked()
        self._zeit_zeile.setEnabled(mit_zeit)
        self.dauer_feld.setEnabled(not mit_zeit)
        self._pruefen()

    def _aktivitaet_aus_feldern(self) -> Aktivitaet:
        mit_zeit = self.modus_zeit.isChecked()
        beginn = self.beginn_feld.time().toPython() if mit_zeit else None
        ende = self.ende_feld.time().toPython() if mit_zeit else None
        return replace(
            self._original,
            titel=self.titel_feld.text(),
            lebensbereich_id=self.bereich_feld.currentData() or 0,
            datum=self.datum_feld.date().toPython(),
            beginn=beginn,
            ende=ende,
            dauer_minuten=self.dauer_feld.value(),
            status=self.status_feld.currentData(),
            zufriedenheit=self.skalen["zufriedenheit"].wert(),
            belastung=self.skalen["belastung"].wert(),
            erholung=self.skalen["erholung"].wert(),
            bewegungsart=self.bewegungsart_feld.currentData()
            if not self.bewegungsart_feld.isHidden()
            else None,
            notiz=self.notiz_feld.toPlainText(),
        )

    def _gewaehlte_tage(self) -> frozenset[Wochentag]:
        return frozenset(t for t, feld in self.wochentag_felder.items() if feld.isChecked())

    def _enddatum(self) -> date | None:
        return self.enddatum_feld.date().toPython() if self.enddatum_aktiv.isChecked() else None

    def _pruefen(self) -> list[Fehler]:
        """Prüft alle Felder, zeigt Meldungen an berührten Feldern und sperrt „Speichern“."""
        if self._laedt:
            return []
        durchgefuehrt = self.status_feld.currentData() is Aktivitaetsstatus.DURCHGEFUEHRT
        for skala in self.skalen.values():
            skala.setEnabled(durchgefuehrt)
        bereich = self._bereiche.get(self.bereich_feld.currentData())
        ist_bewegung = (
            bereich is not None and bereich.standard_schluessel is StandardSchluessel.BEWEGUNG
        )
        self.bewegungsart_label.setVisible(ist_bewegung)
        self.bewegungsart_feld.setVisible(ist_bewegung)

        a = self._aktivitaet_aus_feldern()
        self._dauer_anzeigen(a)
        laenge = len(self.notiz_feld.toPlainText())
        self.notiz_zaehler.setText(f"{laenge}/{MAX_NOTIZ}")
        if laenge > MAX_NOTIZ:
            self._beruehrt.add("notiz")

        fehler = self._service.pruefen(a)
        if self.wiederholen_feld.isChecked() and not self._bearbeiten:
            serie = Wiederholungsserie(
                titel=a.titel,
                lebensbereich_id=a.lebensbereich_id,
                wochentage=self._gewaehlte_tage(),
                startdatum=a.datum,
                dauer_minuten=max(1, a.dauer_minuten),
                enddatum=self._enddatum(),
            )
            fehler += [f for f in pruefe_serie(serie) if f.feld != "dauer"]
        self._fehler_anzeigen(fehler)
        return fehler

    def _dauer_anzeigen(self, a: Aktivitaet) -> None:
        if self.modus_zeit.isChecked():
            try:
                minuten = berechne_dauer(a.beginn, a.ende, None)
            except ValueError:
                self.dauer_info.setText("")
                self.folgetag_label.hide()
                return
            self.folgetag_label.setVisible(a.ende < a.beginn)
        else:
            minuten = a.dauer_minuten
            self.folgetag_label.hide()
        self.dauer_info.setText(f"Dauer: {minuten} min ({stunden_text(minuten / 60)})")

    def _fehler_anzeigen(self, fehler: list[Fehler]) -> None:
        nach_feld = {f.feld: f.meldung for f in fehler}
        felder = {
            "titel": self.titel_feld,
            "lebensbereich": self.bereich_feld,
            "zeit": self.beginn_feld,
            "dauer": self.dauer_feld,
            "status": self.status_feld,
            "notiz": self.notiz_feld,
            "enddatum": self.enddatum_feld,
        }
        for schluessel, label in self.fehlerlabels.items():
            meldung = nach_feld.get(schluessel)
            sichtbar = (
                meldung if schluessel in self._beruehrt or schluessel == "bewertung" else None
            )
            feld = felder.get(schluessel)
            if feld is not None:
                markiere(feld, label, sichtbar)
            else:
                label.setText(sichtbar or "")
                label.setVisible(bool(sichtbar))
        self.speichern_knopf.setEnabled(not fehler)
        if fehler:
            offen = ", ".join(dict.fromkeys(FELDNAMEN.get(f.feld, f.feld) for f in fehler))
            self.speichern_knopf.setToolTip(f"Noch nicht gültig: {offen}")
        else:
            self.speichern_knopf.setToolTip("Speichern (Enter)")

    # --- Aktionen -------------------------------------------------------------------------

    def done(self, ergebnis: int) -> None:
        """Beendet den Dialog und stoppt die Prüfung, bevor Qt die Felder abbaut."""
        self._laedt = True
        super().done(ergebnis)

    def _fertig(self) -> None:
        self._zustand.daten_geaendert.emit()
        self.accept()

    def _speichern(self) -> None:
        if self._pruefen():
            return
        a = self._aktivitaet_aus_feldern()
        try:
            if self.wiederholen_feld.isChecked() and not self._bearbeiten:
                self._service.serie_anlegen(a, self._gewaehlte_tage(), self._enddatum())
            else:
                gespeichert = self._service.speichern(a)
                if self._serie is not None and self.serie_anwenden.isChecked():
                    self._serie_uebernehmen(gespeichert)
        except ValidierungsFehler as e:
            self._beruehrt.update(f.feld for f in e.fehler)
            self._fehler_anzeigen(e.fehler)
            return
        except RegelVerletzung as e:
            QMessageBox.warning(self, self.windowTitle(), str(e))
            return
        self._fertig()

    def _serie_uebernehmen(self, a: Aktivitaet) -> None:
        serie = replace(
            self._serie,
            titel=a.titel,
            lebensbereich_id=a.lebensbereich_id,
            beginn=a.beginn,
            dauer_minuten=a.dauer_minuten,
            bewegungsart=a.bewegungsart,
            ausnahmen=set(self._serie.ausnahmen),
        )
        self._service.serie_aendern(serie)

    def _fragen(self, text: str) -> bool:
        antwort = QMessageBox.question(
            self,
            self.windowTitle(),
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return antwort == QMessageBox.StandardButton.Yes

    def _loeschen(self) -> None:
        if self._fragen(f"Aktivität „{self._original.titel}“ wirklich löschen?"):
            self._service.loeschen(self._original.id)
            self._fertig()

    def _ueberspringen(self) -> None:
        if self._fragen(
            f"Termin am {self._original.datum:%d.%m.%Y} überspringen? "
            "Die übrigen Termine der Serie bleiben erhalten."
        ):
            try:
                self._service.termin_ueberspringen(self._original.id)
            except RegelVerletzung as e:
                QMessageBox.warning(self, self.windowTitle(), str(e))
                return
            self._fertig()

    def _serie_loeschen(self) -> None:
        if self._fragen(
            "Serie löschen? Zukünftige geplante Termine werden entfernt; vergangene, "
            "durchgeführte und einzeln bearbeitete Termine bleiben erhalten."
        ):
            self._service.serie_loeschen(self._serie.id)
            self._fertig()


def aktivitaet_bearbeiten(
    kontext: AppKontext,
    zustand: Zustand,
    aktivitaet_id: int | None = None,
    datum: date | None = None,
    beginn: time | None = None,
    parent: QWidget | None = None,
) -> bool:
    """Öffnet den Dialog modal; liefert ``True``, wenn gespeichert oder gelöscht wurde."""
    aktivitaet = kontext.aktivitaeten.aktivitaet(aktivitaet_id) if aktivitaet_id else None
    dialog = AktivitaetDialog(kontext, zustand, aktivitaet, datum, beginn, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
