"""Service für Aktivitäten und wöchentliche Wiederholungsserien (US05–US08, GP01, GP02)."""

from collections.abc import Callable
from dataclasses import replace
from datetime import date, time, timedelta

from balanceos.anwendung.fehler import RegelVerletzung, ValidierungsFehler
from balanceos.domaene.kalender import KW, berechne_dauer
from balanceos.domaene.modell import Aktivitaet, Wiederholungsserie
from balanceos.domaene.serien import erzeuge_termin, horizont, ist_termindatum, termindaten
from balanceos.domaene.typen import Aktivitaetsstatus, StandardSchluessel, Wochentag
from balanceos.domaene.validierung import pruefe_aktivitaet, pruefe_serie
from balanceos.persistenz.datenbank import Datenbank
from balanceos.persistenz.repo_aktivitaeten import AktivitaetRepository, SerieRepository
from balanceos.persistenz.repo_bereiche import LebensbereichRepository

M_KEINE_SERIE = "Nur Termine einer Wiederholungsserie können übersprungen werden."
STANDARD_DAUER = 60


class AktivitaetService:
    """Erfassen, Bearbeiten und Löschen von Aktivitäten und Serien."""

    def __init__(
        self,
        aktivitaeten: AktivitaetRepository,
        serien: SerieRepository,
        bereiche: LebensbereichRepository,
        db: Datenbank,
        heute: Callable[[], date],
    ) -> None:
        """Erzeugt den Service mit Repositories, Datenbank und Datumsquelle."""
        self._aktivitaeten = aktivitaeten
        self._serien = serien
        self._bereiche = bereiche
        self._db = db
        self._heute = heute

    # --- Lesen -----------------------------------------------------------------------------

    def fuer_woche(self, kw: KW) -> list[Aktivitaet]:
        """Alle Aktivitäten einer Kalenderwoche, sortiert nach Datum und Beginn."""
        return self._aktivitaeten.im_zeitraum(kw.montag(), kw.sonntag())

    def ueberlauf_aus_vorwoche(self, kw: KW) -> list[Aktivitaet]:
        """Aktivitäten vom Sonntag vor ``kw``, die über Mitternacht in den Montag reichen.

        Die Wochenansicht zeichnet ihren Teil nach Mitternacht am Montag. Sie
        zählen weiterhin nur zur Vorwoche (GR11).
        """
        sonntag = kw.montag() - timedelta(days=1)
        return [
            a
            for a in self._aktivitaeten.im_zeitraum(sonntag, sonntag)
            if a.beginn is not None
            and a.beginn.hour * 60 + a.beginn.minute + a.dauer_minuten > 24 * 60
        ]

    def aktivitaet(self, aktivitaet_id: int) -> Aktivitaet | None:
        """Aktivität mit der angegebenen ID."""
        return self._aktivitaeten.nach_id(aktivitaet_id)

    def serie(self, serie_id: int) -> Wiederholungsserie | None:
        """Serie mit der angegebenen ID."""
        return self._serien.nach_id(serie_id)

    def vorbelegung(self, datum: date, beginn: time | None = None) -> Aktivitaet:
        """Vorbelegte neue Aktivität für den Erfassungsdialog (GP01).

        Der Status ist für heutige und vergangene Tage „Durchgeführt“, sonst
        „Geplant“; Lebensbereich ist der erste aktive Bereich.
        """
        aktive = [b for b in self._bereiche.alle() if b.aktiv]
        status = (
            Aktivitaetsstatus.DURCHGEFUEHRT if datum <= self._heute() else Aktivitaetsstatus.GEPLANT
        )
        return Aktivitaet(
            titel="",
            lebensbereich_id=aktive[0].id if aktive else 0,
            datum=datum,
            dauer_minuten=STANDARD_DAUER,
            status=status,
            beginn=beginn,
        )

    # --- Einzelne Aktivitäten -------------------------------------------------------------

    def _bereinigen(self, a: Aktivitaet) -> Aktivitaet:
        """Wendet die automatischen Regeln GR10, GR11, GR13 und GR15 an."""
        a = replace(a, titel=a.titel.strip(), notiz=(a.notiz or "").strip() or None)
        if a.beginn is not None and a.ende is not None:
            try:
                a.dauer_minuten = berechne_dauer(a.beginn, a.ende, None)
            except ValueError:
                pass  # die Validierung meldet den Fehler am Feld
        if a.status is not Aktivitaetsstatus.DURCHGEFUEHRT:
            a.zufriedenheit = a.belastung = a.erholung = None
        bereich = self._bereiche.nach_id(a.lebensbereich_id)
        if bereich is None or bereich.standard_schluessel is not StandardSchluessel.BEWEGUNG:
            a.bewegungsart = None
        return a

    def pruefen(self, a: Aktivitaet) -> list:
        """Prüft eine Aktivität so, wie sie gespeichert würde; leer heißt gültig."""
        a = self._bereinigen(a)
        return pruefe_aktivitaet(a, self._bereiche.nach_id(a.lebensbereich_id), self._heute())

    def speichern(self, a: Aktivitaet) -> Aktivitaet:
        """Speichert eine neue oder geänderte Aktivität.

        Ein geänderter Serientermin wird als einzeln bearbeitet markiert, damit
        spätere Änderungen an der Serie ihn nicht überschreiben (GR19).

        Raises:
            ValidierungsFehler: wenn die Aktivität gegen Gültigkeitsregeln verstößt.
        """
        a = self._bereinigen(a)
        fehler = pruefe_aktivitaet(a, self._bereiche.nach_id(a.lebensbereich_id), self._heute())
        if fehler:
            raise ValidierungsFehler(fehler)
        alt = self._aktivitaeten.nach_id(a.id) if a.id is not None and a.serie_id else None
        with self._db.transaktion():
            if alt is not None:
                a.einzeln_bearbeitet = True
                if alt.datum != a.datum:
                    self._ausnahme_eintragen(alt.serie_id, alt.datum)
            return self._aktivitaeten.speichern(a)

    def loeschen(self, aktivitaet_id: int) -> None:
        """Löscht eine Aktivität.

        Bei einem Serientermin wird sein Datum als Ausnahme eingetragen (GR18),
        damit eine spätere Änderung der Serie den Termin nicht neu erzeugt.
        """
        a = self._aktivitaeten.nach_id(aktivitaet_id)
        with self._db.transaktion():
            if a is not None and a.serie_id is not None:
                self._ausnahme_eintragen(a.serie_id, a.datum)
            self._aktivitaeten.loeschen(aktivitaet_id)

    def _ausnahme_eintragen(self, serie_id: int, tag: date) -> None:
        """Trägt ``tag`` als Ausnahme ein, wenn dort laut Serie ein Termin liegt."""
        serie = self._serien.nach_id(serie_id)
        if serie is not None and ist_termindatum(serie, tag):
            serie.ausnahmen.add(tag)
            self._serien.speichern(serie)

    # --- Serien ----------------------------------------------------------------------------

    def serie_anlegen(
        self, vorlage: Aktivitaet, wochentage: frozenset[Wochentag], enddatum: date | None
    ) -> Wiederholungsserie:
        """Legt eine Serie aus den Angaben des Erfassungsdialogs an (US07).

        Termine entstehen vom Datum der Vorlage bis zum Horizont von 52 Wochen.
        Fällt das Datum der Vorlage auf einen gewählten Wochentag, wird die
        Vorlage selbst zum ersten Termin und behält Status und Bewertungen;
        sonst wird sie als einzelne Aktivität gespeichert.

        Raises:
            ValidierungsFehler: bei ungültiger Vorlage oder Serie.
        """
        vorlage = self._bereinigen(vorlage)
        serie = Wiederholungsserie(
            titel=vorlage.titel,
            lebensbereich_id=vorlage.lebensbereich_id,
            wochentage=frozenset(wochentage),
            startdatum=vorlage.datum,
            dauer_minuten=vorlage.dauer_minuten,
            enddatum=enddatum,
            beginn=vorlage.beginn,
            bewegungsart=vorlage.bewegungsart,
        )
        bereich = self._bereiche.nach_id(vorlage.lebensbereich_id)
        fehler = pruefe_aktivitaet(vorlage, bereich, self._heute()) + pruefe_serie(serie)
        if fehler:
            raise ValidierungsFehler(fehler)
        bis = horizont(self._heute())
        with self._db.transaktion():
            self._serien.speichern(serie)
            termine = []
            for tag in termindaten(serie, serie.startdatum, bis):
                if tag == vorlage.datum:
                    termine.append(replace(vorlage, serie_id=serie.id, id=None))
                else:
                    termine.append(erzeuge_termin(serie, tag))
            if not ist_termindatum(serie, vorlage.datum):
                termine.append(replace(vorlage, id=None))
            self._aktivitaeten.einfuegen_viele(termine)
            serie.generiert_bis = bis
            self._serien.speichern(serie)
        return serie

    def _ersetzbar(self, a: Aktivitaet) -> bool:
        """Zukünftiger, unbearbeiteter geplanter Termin (GR19, GR20)."""
        return (
            a.datum > self._heute()
            and a.status is Aktivitaetsstatus.GEPLANT
            and not a.einzeln_bearbeitet
        )

    def serie_aendern(self, serie: Wiederholungsserie) -> None:
        """Übernimmt Änderungen einer Serie in alle zukünftigen, unbearbeiteten Termine (GR19).

        Die gespeicherten Ausnahmen bleiben erhalten und werden mit denen der
        übergebenen Serie vereinigt. So gehen Ausnahmen nicht verloren, die nach
        dem Laden der Serie entstanden sind, etwa durch das Verschieben oder
        Löschen eines Termins unmittelbar zuvor (GR18).

        Raises:
            ValidierungsFehler: bei ungültiger Serie.
        """
        fehler = pruefe_serie(serie)
        if fehler:
            raise ValidierungsFehler(fehler)
        heute = self._heute()
        bis = horizont(heute)
        with self._db.transaktion():
            gespeichert = self._serien.nach_id(serie.id) if serie.id is not None else None
            if gespeichert is not None:
                serie.ausnahmen = set(serie.ausnahmen) | gespeichert.ausnahmen
            behalten = set()
            for t in self._aktivitaeten.termine_der_serie(serie.id):
                if self._ersetzbar(t):
                    self._aktivitaeten.loeschen(t.id)
                else:
                    behalten.add(t.datum)
            ab = max(heute + timedelta(days=1), serie.startdatum)
            neu = [
                erzeuge_termin(serie, tag)
                for tag in termindaten(serie, ab, bis)
                if tag not in behalten
            ]
            self._aktivitaeten.einfuegen_viele(neu)
            serie.generiert_bis = bis
            self._serien.speichern(serie)

    def serie_loeschen(self, serie_id: int) -> None:
        """Löscht eine Serie mit ihren zukünftigen, unbearbeiteten Terminen (GR20).

        Vergangene, durchgeführte, ausgefallene und einzeln bearbeitete Termine
        bleiben als einzelne Aktivitäten erhalten.
        """
        with self._db.transaktion():
            for t in self._aktivitaeten.termine_der_serie(serie_id):
                if self._ersetzbar(t):
                    self._aktivitaeten.loeschen(t.id)
            self._serien.loeschen(serie_id)

    def termin_ueberspringen(self, aktivitaet_id: int) -> None:
        """Überspringt einen einzelnen Termin einer Serie (US08, GR18).

        Raises:
            RegelVerletzung: wenn die Aktivität zu keiner Serie gehört.
        """
        a = self._aktivitaeten.nach_id(aktivitaet_id)
        serie = self._serien.nach_id(a.serie_id) if a and a.serie_id else None
        if a is None or serie is None:
            raise RegelVerletzung(M_KEINE_SERIE)
        self.loeschen(a.id)

    def horizont_fortschreiben(self) -> int:
        """Erzeugt fehlende Termine aller Serien bis 52 Wochen im Voraus (GP02).

        Returns:
            Anzahl der neu erzeugten Termine.
        """
        bis = horizont(self._heute())
        anzahl = 0
        with self._db.transaktion():
            for serie in self._serien.alle():
                ab = (
                    serie.generiert_bis + timedelta(days=1)
                    if serie.generiert_bis
                    else serie.startdatum
                )
                if ab > bis:
                    continue
                vorhanden = {t.datum for t in self._aktivitaeten.termine_der_serie(serie.id)}
                neu = [
                    erzeuge_termin(serie, tag)
                    for tag in termindaten(serie, ab, bis)
                    if tag not in vorhanden
                ]
                self._aktivitaeten.einfuegen_viele(neu)
                anzahl += len(neu)
                serie.generiert_bis = bis
                self._serien.speichern(serie)
        return anzahl
