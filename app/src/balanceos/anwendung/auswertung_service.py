"""Service für Wochenbewertung, Hinweise, Verlauf und Balance-Kompass (US10–US15, US19)."""

from balanceos.domaene.bewertung import bewerte_woche
from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import Hinweis, KompassModell, Regel, Wochenbewertung
from balanceos.domaene.regeln import RegelKontext, pruefe_regeln
from balanceos.persistenz.datenbank import Datenbank
from balanceos.persistenz.repo_aktivitaeten import AktivitaetRepository
from balanceos.persistenz.repo_bereiche import EinstellungenRepository, LebensbereichRepository
from balanceos.persistenz.repo_wissen import (
    AusblendungRepository,
    KompassRepository,
    RegelRepository,
)


class AuswertungService:
    """Berechnet Bewertungen und Hinweise bei jeder Anfrage neu (nichts wird gespeichert)."""

    def __init__(
        self,
        aktivitaeten: AktivitaetRepository,
        bereiche: LebensbereichRepository,
        einstellungen: EinstellungenRepository,
        regeln: RegelRepository,
        kompass: KompassRepository,
        ausblendungen: AusblendungRepository,
        db: Datenbank,
    ) -> None:
        """Erzeugt den Service mit seinen Repositories."""
        self._aktivitaeten = aktivitaeten
        self._bereiche = bereiche
        self._einstellungen = einstellungen
        self._regeln = regeln
        self._kompass = kompass
        self._ausblendungen = ausblendungen
        self._db = db

    def gibt_aktivitaeten(self) -> bool:
        """``True``, sobald mindestens eine Aktivität gespeichert ist."""
        return bool(self._db.abfrage("SELECT 1 FROM aktivitaet LIMIT 1"))

    def wochenbewertung(self, kw: KW) -> Wochenbewertung:
        """Bewertung einer Kalenderwoche (GP03, GP05)."""
        aktivitaeten = self._aktivitaeten.im_zeitraum(kw.montag(), kw.sonntag())
        return bewerte_woche(kw, self._bereiche.alle(), aktivitaeten, self._einstellungen.laden())

    def verlauf(self, bis_kw: KW, wochen: int = 8) -> list[Wochenbewertung]:
        """Bewertungen der letzten ``wochen`` Wochen bis ``bis_kw``, älteste zuerst."""
        kws = [bis_kw.verschoben(-i) for i in range(wochen - 1, -1, -1)]
        aktivitaeten = self._aktivitaeten.im_zeitraum(kws[0].montag(), bis_kw.sonntag())
        bereiche = self._bereiche.alle()
        einstellungen = self._einstellungen.laden()
        return [bewerte_woche(kw, bereiche, aktivitaeten, einstellungen) for kw in kws]

    def hinweise(self, kw: KW, mit_ausgeblendeten: bool = False) -> list[Hinweis]:
        """Sortierte Hinweise einer Woche; ausgeblendete fehlen standardmäßig (GR24)."""
        bereiche = self._bereiche.alle()
        einstellungen = self._einstellungen.laden()
        aktivitaeten = self._aktivitaeten.im_zeitraum(kw.verschoben(-2).montag(), kw.sonntag())
        wochen = [kw.verschoben(-i) for i in range(3)]
        kontext = RegelKontext(
            kw=kw,
            bereiche=bereiche,
            aktivitaeten=aktivitaeten,
            bewertungen={
                w: bewerte_woche(w, bereiche, aktivitaeten, einstellungen) for w in wochen
            },
            regeln={r.kennung: r for r in self._regeln.alle()},
            modelle={m.schluessel: m for m in self._kompass.alle()},
        )
        hinweise = pruefe_regeln(kontext)
        if mit_ausgeblendeten:
            return hinweise
        weg = self._ausblendungen.ausgeblendet(kw)
        return [h for h in hinweise if (h.regel, h.lebensbereich_id) not in weg]

    def hinweis_ausblenden(self, h: Hinweis) -> None:
        """Blendet einen Hinweis für seine Woche aus (US12)."""
        self._ausblendungen.ausblenden(h.regel, h.kw, h.lebensbereich_id)

    def regeln(self) -> list[Regel]:
        """Alle Regeln mit Aktivzustand."""
        return self._regeln.alle()

    def regel_setzen(self, kennung: str, aktiv: bool) -> None:
        """Schaltet eine Regel ein oder aus (US14)."""
        self._regeln.aktiv_setzen(kennung, aktiv)

    def kompassmodelle(self) -> list[KompassModell]:
        """Alle Modelle des Balance-Kompasses (US15)."""
        return self._kompass.alle()

    def modell(self, schluessel: str) -> KompassModell:
        """Modell mit dem angegebenen Schlüssel.

        Raises:
            KeyError: wenn es kein Modell mit diesem Schlüssel gibt.
        """
        for m in self._kompass.alle():
            if m.schluessel == schluessel:
                return m
        raise KeyError(schluessel)
