"""CSV- und JSON-Export der Nutzdaten (US16, NFA10; Spezifikation Kap. 4.3)."""

import csv
import json
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from balanceos.anwendung.fehler import RegelVerletzung
from balanceos.domaene.kalender import KW
from balanceos.domaene.typen import Wochentag
from balanceos.domaene.validierung import M_SPEICHERORT
from balanceos.persistenz.repo_aktivitaeten import AktivitaetRepository, SerieRepository
from balanceos.persistenz.repo_bereiche import EinstellungenRepository, LebensbereichRepository
from balanceos.persistenz.repo_wissen import ReflexionRepository, RegelRepository, Who5Repository

FORMAT = "BalanceOS-Export"
VERSION = 1


def _zeit(t: time | None) -> str | None:
    return None if t is None else f"{t:%H:%M}"


def _datum(d: date | None) -> str | None:
    return None if d is None else d.isoformat()


def _ja_nein(wert: bool) -> str:
    return "ja" if wert else "nein"


def _leer(wert: Any) -> str:
    return "" if wert is None else str(wert)


class ExportService:
    """Schreibt Aktivitäten als CSV und alle Nutzdaten als JSON in eine Datei."""

    CSV_SPALTEN: tuple[str, ...] = (
        "datum",
        "kalenderwoche",
        "lebensbereich",
        "bereichstyp",
        "titel",
        "beginn",
        "ende",
        "dauerMinuten",
        "status",
        "zufriedenheit",
        "belastung",
        "erholung",
        "bewegungsart",
        "notiz",
        "ausSerie",
        "istDemo",
    )

    def __init__(
        self,
        aktivitaeten: AktivitaetRepository,
        serien: SerieRepository,
        bereiche: LebensbereichRepository,
        einstellungen: EinstellungenRepository,
        regeln: RegelRepository,
        who5: Who5Repository,
        reflexionen: ReflexionRepository,
    ) -> None:
        """Erzeugt den Service mit den Repositories aller exportierten Daten."""
        self._aktivitaeten = aktivitaeten
        self._serien = serien
        self._bereiche = bereiche
        self._einstellungen = einstellungen
        self._regeln = regeln
        self._who5 = who5
        self._reflexionen = reflexionen

    @staticmethod
    def dateiname_csv(von: date, bis: date) -> str:
        """Vorgeschlagener Dateiname des CSV-Exports."""
        return f"BalanceOS_Aktivitaeten_{von.isoformat()}_{bis.isoformat()}.csv"

    @staticmethod
    def dateiname_json(tag: date) -> str:
        """Vorgeschlagener Dateiname des JSON-Exports."""
        return f"BalanceOS_Export_{tag.isoformat()}.json"

    def csv_exportieren(self, pfad: Path, von: date, bis: date) -> int:
        """Schreibt die Aktivitäten von ``von`` bis ``bis`` als CSV-Datei.

        Returns:
            Anzahl der geschriebenen Datenzeilen (ohne Kopfzeile).

        Raises:
            RegelVerletzung: wenn die Datei nicht geschrieben werden kann.
        """
        bereiche = {b.id: b for b in self._bereiche.alle()}
        zeilen = []
        for a in self._aktivitaeten.im_zeitraum(von, bis):
            b = bereiche[a.lebensbereich_id]
            zeilen.append(
                [
                    a.datum.isoformat(),
                    KW.aus_datum(a.datum).iso(),
                    b.name,
                    b.typ,
                    a.titel,
                    _leer(_zeit(a.beginn)),
                    _leer(_zeit(a.ende)),
                    a.dauer_minuten,
                    a.status,
                    _leer(a.zufriedenheit),
                    _leer(a.belastung),
                    _leer(a.erholung),
                    _leer(a.bewegungsart),
                    _leer(a.notiz),
                    _ja_nein(a.serie_id is not None),
                    _ja_nein(a.ist_demo),
                ]
            )
        try:
            with Path(pfad).open("w", encoding="utf-8-sig", newline="") as datei:
                schreiber = csv.writer(
                    datei, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL
                )
                schreiber.writerow(self.CSV_SPALTEN)
                schreiber.writerows(zeilen)
        except OSError as e:
            raise RegelVerletzung(M_SPEICHERORT) from e
        return len(zeilen)

    def daten_als_dict(self, jetzt: datetime) -> dict[str, Any]:
        """Alle Nutzdaten in der Struktur des JSON-Exports (Formatversion 1)."""
        bereiche = self._bereiche.alle()
        namen = {b.id: b.name for b in bereiche}
        serien = self._serien.alle()
        nummer = {s.id: nr for nr, s in enumerate(serien, start=1)}
        einstellungen = self._einstellungen.laden()
        return {
            "format": FORMAT,
            "version": VERSION,
            "exportiertAm": jetzt.replace(microsecond=0).isoformat(),
            "einstellungen": {
                "alpha": einstellungen.alpha,
                "gesamtScoreAnzeigen": einstellungen.gesamtscore_anzeigen,
            },
            "lebensbereiche": [
                {
                    "name": b.name,
                    "typ": str(b.typ),
                    "farbe": b.farbe,
                    "aktiv": b.aktiv,
                    "istStandard": b.ist_standard,
                    "sollStundenProWoche": float(b.soll_stunden),
                    "gewicht": b.gewicht,
                }
                for b in bereiche
            ],
            "aktivitaeten": [
                {
                    "titel": a.titel,
                    "lebensbereich": namen[a.lebensbereich_id],
                    "datum": a.datum.isoformat(),
                    "beginn": _zeit(a.beginn),
                    "ende": _zeit(a.ende),
                    "dauerMinuten": a.dauer_minuten,
                    "status": str(a.status),
                    "zufriedenheit": a.zufriedenheit,
                    "belastung": a.belastung,
                    "erholung": a.erholung,
                    "bewegungsart": None if a.bewegungsart is None else str(a.bewegungsart),
                    "notiz": a.notiz,
                    "istDemo": a.ist_demo,
                    "serie": nummer.get(a.serie_id),
                }
                for a in self._aktivitaeten.alle()
            ],
            "wiederholungsserien": [
                {
                    "nr": nummer[s.id],
                    "titel": s.titel,
                    "lebensbereich": namen[s.lebensbereich_id],
                    "wochentage": [str(t) for t in Wochentag if t in s.wochentage],
                    "startdatum": s.startdatum.isoformat(),
                    "enddatum": _datum(s.enddatum),
                    "beginn": _zeit(s.beginn),
                    "dauerMinuten": s.dauer_minuten,
                    "bewegungsart": None if s.bewegungsart is None else str(s.bewegungsart),
                    "ausnahmen": [d.isoformat() for d in sorted(s.ausnahmen)],
                }
                for s in serien
            ],
            "regeln": [{"kennung": r.kennung, "aktiv": r.aktiv} for r in self._regeln.alle()],
            "who5Erhebungen": [
                {
                    "datum": e.datum.isoformat(),
                    "antworten": list(e.antworten),
                    "rohwert": e.rohwert,
                    "prozentwert": e.prozentwert,
                }
                for e in sorted(self._who5.alle(), key=lambda e: e.datum)
            ],
            "wochenreflexionen": [
                {
                    "jahr": r.kw.jahr,
                    "kalenderwoche": r.kw.woche,
                    "antworten": list(r.antworten),
                    "stimmung": r.stimmung,
                }
                for r in sorted(self._reflexionen.alle(), key=lambda r: r.kw)
            ],
        }

    def json_exportieren(self, pfad: Path, jetzt: datetime) -> None:
        """Schreibt alle Nutzdaten als JSON-Datei (UTF-8 ohne BOM).

        Raises:
            RegelVerletzung: wenn die Datei nicht geschrieben werden kann.
        """
        text = json.dumps(self.daten_als_dict(jetzt), ensure_ascii=False, indent=2)
        try:
            Path(pfad).write_text(text + "\n", encoding="utf-8", newline="\n")
        except OSError as e:
            raise RegelVerletzung(M_SPEICHERORT) from e
