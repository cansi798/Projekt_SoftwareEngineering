"""Gemeinsame Test-Fixtures."""

import os
from datetime import date

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

HEUTE = date(2026, 11, 18)
"""Festes Tagesdatum für alle Tests (Mittwoch, KW 47/2026)."""


@pytest.fixture
def heute() -> date:
    return HEUTE


@pytest.fixture
def kontext():
    from balanceos.anwendung.kontext import AppKontext

    k = AppKontext.erstellen(":memory:", heute=lambda: HEUTE)
    yield k
    k.db.schliessen()
