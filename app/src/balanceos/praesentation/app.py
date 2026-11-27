"""Programmstart: Qt-Anwendung, Datenbank und Hauptfenster."""

import sqlite3
import sys
from collections.abc import Iterable
from pathlib import Path

import PySide6
from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
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


def starte(argv: list[str] | None = None) -> int:
    """Startet BalanceOS und liefert den Rückgabewert der Ereignisschleife.

    Kann die Datenbank nicht geöffnet werden, erscheint eine Meldung und die
    Anwendung endet mit dem Rückgabewert 1.
    """
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("BalanceOS")
    app.setStyleSheet(STYLESHEET)
    qt_uebersetzung_laden(app)
    try:
        kontext = AppKontext.erstellen(standardpfad())
    except (OSError, sqlite3.Error) as fehler:
        QMessageBox.critical(
            None, "BalanceOS", f"Die Datenbank konnte nicht geöffnet werden: {fehler}"
        )
        return 1
    fenster = Hauptfenster(kontext, Zustand(KW.heute(kontext.heute())))
    fenster.show()
    ergebnis = app.exec()
    kontext.db.schliessen()
    return ergebnis
