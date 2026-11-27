"""Programmstart: Qt-Anwendung, Datenbank und Hauptfenster."""

import sqlite3
import sys
import traceback
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from types import TracebackType

import PySide6
from PySide6.QtCore import QLibraryInfo, QLocale, QLockFile, QTranslator
from PySide6.QtWidgets import QApplication, QMessageBox

from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.kalender import KW
from balanceos.persistenz.datenbank import standardpfad
from balanceos.praesentation.hauptfenster import Hauptfenster
from balanceos.praesentation.stil import STYLESHEET
from balanceos.praesentation.zustand import Zustand


def _uebersetzungsordner() -> list[Path]:
    """Mögliche Ablageorte der Qt-Übersetzungen (installiert und in der exe)."""
    return [
        Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)),
        Path(PySide6.__file__).parent / "translations",
    ]


def qt_uebersetzung_laden(
    app: QApplication, verzeichnisse: Iterable[Path] | None = None
) -> QTranslator | None:
    """Lädt die deutsche Übersetzung der Qt-Standardtexte (z. B. „Ja“/„Nein“).

    Liefert den installierten Übersetzer oder ``None``, wenn keine Datei
    gefunden wird; die Anwendung läuft dann mit den englischen Standardtexten.
    """
    for ordner in verzeichnisse if verzeichnisse is not None else _uebersetzungsordner():
        uebersetzer = QTranslator(app)
        if uebersetzer.load(QLocale(QLocale.Language.German), "qtbase", "_", str(ordner)):
            app.installTranslator(uebersetzer)
            return uebersetzer
    return None


def fehlertext(art: type[BaseException], fehler: BaseException) -> str:
    """Deutsche Meldung zu einem unerwarteten Fehler; Datenbankfehler werden eigens benannt."""
    if issubclass(art, sqlite3.Error):
        return (
            "Die Daten konnten nicht gespeichert werden. Möglicherweise ist die Datenbank"
            " gerade von einem anderen Programm gesperrt oder der Datenträger ist voll."
            " Bitte prüfen Sie das und versuchen Sie es erneut."
            f"\n\nTechnische Angabe: {fehler}"
        )
    return (
        "Ein unerwarteter Fehler ist aufgetreten. Die letzte Aktion wurde möglicherweise"
        " nicht vollständig ausgeführt."
        f"\n\nTechnische Angabe: {art.__name__}: {fehler}"
    )


def fehlerbehandlung_installieren(logdatei: Path | None = None) -> None:
    """Meldet Ausnahmen aus der Ereignisschleife in einem Fenster statt sie zu verschlucken.

    Qt ruft für Ausnahmen in Slots ``sys.excepthook`` auf. Die ausführbare Datei hat
    keine Konsole, daher zeigt der hier installierte Behandler eine deutsche Meldung,
    schreibt den vollständigen Fehler in ``logdatei`` und, falls vorhanden, auf die
    Standardfehlerausgabe. Die Anwendung läuft danach weiter.

    Args:
        logdatei: Datei, an die der Fehler angehängt wird, oder ``None``.
    """
    aktiv = False

    def behandeln(
        art: type[BaseException], fehler: BaseException, verlauf: TracebackType | None
    ) -> None:
        """Protokolliert einen unbehandelten Fehler und zeigt ihn als Meldung an."""
        nonlocal aktiv
        if issubclass(art, KeyboardInterrupt) or aktiv:
            sys.__excepthook__(art, fehler, verlauf)
            return
        aktiv = True
        try:
            details = "".join(traceback.format_exception(art, fehler, verlauf))
            if sys.stderr is not None:
                sys.stderr.write(details)
            meldung = fehlertext(art, fehler)
            if logdatei is not None:
                try:
                    with open(logdatei, "a", encoding="utf-8") as datei:
                        datei.write(f"--- {datetime.now():%Y-%m-%d %H:%M:%S}\n{details}\n")
                    meldung += f"\n\nEinzelheiten stehen in {logdatei}."
                except OSError:
                    pass
            if QApplication.instance() is not None:
                QMessageBox.critical(QApplication.activeWindow(), "BalanceOS", meldung)
        finally:
            aktiv = False

    sys.excepthook = behandeln


def einzelinstanz_sperren(ordner: Path) -> QLockFile | None:
    """Sperrt den Datenordner für diese Programminstanz.

    Liefert die gehaltene Sperre oder ``None``, wenn bereits eine andere Instanz
    läuft. Die Sperre gilt nur als verwaist, wenn der sperrende Prozess nicht mehr
    existiert (``staleLockTime`` 0), damit eine lange laufende Instanz sie behält.
    """
    sperre = QLockFile(str(ordner / "balanceos.lock"))
    sperre.setStaleLockTime(0)
    return sperre if sperre.tryLock(0) else None


def starte(argv: list[str] | None = None) -> int:
    """Startet BalanceOS und liefert den Rückgabewert der Ereignisschleife.

    Kann die Datenbank nicht geöffnet werden, erscheint eine Meldung und die
    Anwendung endet mit dem Rückgabewert 1. Fehler im laufenden Betrieb meldet
    ``fehlerbehandlung_installieren``; sie landen zusätzlich in ``fehler.log``
    neben der Datenbank.
    """
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("BalanceOS")
    app.setStyleSheet(STYLESHEET)
    qt_uebersetzung_laden(app)
    try:
        pfad = standardpfad()
        sperre = einzelinstanz_sperren(pfad.parent)
        if sperre is None:
            QMessageBox.information(
                None,
                "BalanceOS",
                "BalanceOS läuft bereits. Bitte das geöffnete Fenster verwenden.",
            )
            return 1
        kontext = AppKontext.erstellen(pfad)
    except (OSError, sqlite3.Error) as fehler:
        QMessageBox.critical(
            None, "BalanceOS", f"Die Datenbank konnte nicht geöffnet werden: {fehler}"
        )
        return 1
    fehlerbehandlung_installieren(pfad.parent / "fehler.log")
    fenster = Hauptfenster(kontext, Zustand(KW.heute(kontext.heute())))
    fenster.show()
    ergebnis = app.exec()
    kontext.db.schliessen()
    sperre.unlock()
    return ergebnis
