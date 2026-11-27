"""Regressionstests: BalanceOS läuft je Datenordner nur einmal."""

import pytest
from PySide6.QtWidgets import QMessageBox

pytestmark = pytest.mark.gui


def test_zweite_sperre_auf_denselben_ordner_scheitert(tmp_path):
    from balanceos.praesentation.app import einzelinstanz_sperren

    erste = einzelinstanz_sperren(tmp_path)
    assert erste is not None
    assert einzelinstanz_sperren(tmp_path) is None
    erste.unlock()
    dritte = einzelinstanz_sperren(tmp_path)
    assert dritte is not None
    dritte.unlock()


def test_start_bei_laufender_instanz_meldet_und_oeffnet_keine_datenbank(
    qtbot, tmp_path, monkeypatch
):
    from balanceos.praesentation import app as app_modul

    db_pfad = tmp_path / "balanceos.db"
    monkeypatch.setattr(app_modul, "standardpfad", lambda: db_pfad)
    meldungen = []
    monkeypatch.setattr(
        QMessageBox, "information", lambda _p, _t, text, *_, **__: meldungen.append(text)
    )
    sperre = app_modul.einzelinstanz_sperren(tmp_path)
    try:
        assert app_modul.starte([]) == 1
    finally:
        sperre.unlock()
    assert len(meldungen) == 1
    assert "läuft bereits" in meldungen[0]
    assert not db_pfad.exists()
