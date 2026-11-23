"""Architekturregeln: Abhängigkeiten zeigen nur nach unten (NFA07)."""

import ast
import pathlib
import sys

SRC = pathlib.Path(__file__).resolve().parents[2] / "src" / "balanceos"


def _importe(paket: str) -> list[tuple[pathlib.Path, str]]:
    ergebnis = []
    for datei in (SRC / paket).rglob("*.py"):
        baum = ast.parse(datei.read_text(encoding="utf-8"))
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Import):
                ergebnis += [(datei, a.name) for a in knoten.names]
            elif isinstance(knoten, ast.ImportFrom):
                ergebnis.append((datei, knoten.module or ""))
    return ergebnis


def _verletzungen(paket: str, verboten: set[str]) -> list[str]:
    return [
        f"{datei.name}: {name}"
        for datei, name in _importe(paket)
        if any(name == v or name.startswith(v + ".") for v in verboten)
    ]


def test_domaene_importiert_weder_qt_noch_sqlite():
    verboten = {
        "PySide6",
        "sqlite3",
        "balanceos.persistenz",
        "balanceos.anwendung",
        "balanceos.praesentation",
    }
    assert _verletzungen("domaene", verboten) == []


def test_persistenz_und_anwendung_importieren_kein_qt():
    assert _verletzungen("persistenz", {"PySide6", "balanceos.praesentation"}) == []
    assert _verletzungen("anwendung", {"PySide6", "balanceos.praesentation"}) == []


def test_architekturtest_erkennt_verstoss(tmp_path, monkeypatch):
    """Gegenprobe: Ein verbotener Import wird tatsächlich gefunden."""
    paket = tmp_path / "domaene"
    paket.mkdir()
    (paket / "x.py").write_text("import sqlite3\n", encoding="utf-8")
    monkeypatch.setattr(sys.modules[__name__], "SRC", tmp_path)
    assert _verletzungen("domaene", {"sqlite3"}) == ["x.py: sqlite3"]
