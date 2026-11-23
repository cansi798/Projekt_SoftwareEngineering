"""Tests der WHO-5-Auswertung (US20, GP06)."""

from balanceos.domaene.who5 import AUSSAGEN, EMPFEHLUNGSTEXT, SKALA, Who5Ergebnis, werte_aus


def test_who5_beispiel():
    assert werte_aus((3, 4, 3, 2, 4)) == Who5Ergebnis(16, 64, False)


def test_who5_grenze_50():
    assert werte_aus((3, 3, 2, 2, 2)) == Who5Ergebnis(12, 48, True)
    assert werte_aus((3, 3, 3, 2, 2)) == Who5Ergebnis(13, 52, False)


def test_who5_texte():
    assert len(AUSSAGEN) == 5 and AUSSAGEN[0] == "Ich war froh und guter Laune."
    assert SKALA[0] == "Zu keinem Zeitpunkt" and SKALA[5] == "Die ganze Zeit"
    assert "keine Diagnose" in EMPFEHLUNGSTEXT
