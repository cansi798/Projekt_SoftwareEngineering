"""Programmstart: Qt-Anwendung, Datenbank und Hauptfenster."""

import sqlite3
import sys

from PySide6.QtWidgets import QApplication, QMessageBox

from balanceos.anwendung.kontext import AppKontext
from balanceos.domaene.kalender import KW
from balanceos.persistenz.datenbank import standardpfad
from balanceos.praesentation.hauptfenster import Hauptfenster
from balanceos.praesentation.stil import STYLESHEET
from balanceos.praesentation.zustand import Zustand


def starte(argv: list[str] | None = None) -> int:
    """Startet BalanceOS und liefert den Rückgabewert der Ereignisschleife.

    Kann die Datenbank nicht geöffnet werden, erscheint eine Meldung und die
    Anwendung endet mit dem Rückgabewert 1.
    """
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("BalanceOS")
    app.setStyleSheet(STYLESHEET)
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
