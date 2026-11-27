"""Deutsche Beschriftung der Qt-Standarddialoge (NFA01)."""

import pytest
from PySide6.QtWidgets import QMessageBox

pytestmark = pytest.mark.gui


def test_rueckfragen_zeigen_deutsche_knoepfe(qapp):
    """Nach dem Laden der Qt-Übersetzung heißen Ja/Nein-Knöpfe deutsch."""
    from balanceos.praesentation.app import qt_uebersetzung_laden

    uebersetzer = qt_uebersetzung_laden(qapp)
    try:
        assert uebersetzer is not None
        box = QMessageBox(
            QMessageBox.Icon.Question,
            "Löschen",
            "Wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        assert {b.text() for b in box.buttons()} == {"&Ja", "&Nein"}
    finally:
        if uebersetzer is not None:
            qapp.removeTranslator(uebersetzer)


def test_fehlende_uebersetzung_bricht_nicht_ab(qapp, tmp_path):
    """Ohne Übersetzungsdatei startet die Anwendung trotzdem (englische Standardtexte)."""
    from balanceos.praesentation.app import qt_uebersetzung_laden

    assert qt_uebersetzung_laden(qapp, verzeichnisse=[tmp_path]) is None
