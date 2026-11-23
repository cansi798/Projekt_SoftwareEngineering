"""Integrationstests der SQLite-Persistenz und der Stammdaten."""

from datetime import date, time

import pytest

from balanceos.domaene.kalender import KW
from balanceos.domaene.modell import (
    Aktivitaet,
    Einstellungen,
    Lebensbereich,
    Who5Erhebung,
    Wiederholungsserie,
    Wochenreflexion,
)
from balanceos.domaene.typen import (
    Aktivitaetsstatus,
    Bereichstyp,
    Bewegungsart,
    StandardSchluessel,
    Wochentag,
)
from balanceos.persistenz.datenbank import Datenbank, alle_nutzdaten_loeschen
from balanceos.persistenz.repo_aktivitaeten import AktivitaetRepository, SerieRepository
from balanceos.persistenz.repo_bereiche import EinstellungenRepository, LebensbereichRepository
from balanceos.persistenz.repo_wissen import (
    AusblendungRepository,
    KompassRepository,
    ReflexionRepository,
    RegelRepository,
    Who5Repository,
)
from balanceos.persistenz.stammdaten import initialisiere


@pytest.fixture
def db():
    datenbank = Datenbank(":memory:")
    initialisiere(datenbank)
    yield datenbank
    datenbank.schliessen()


def _bewegung(db) -> Lebensbereich:
    return LebensbereichRepository(db).nach_schluessel(StandardSchluessel.BEWEGUNG)


def test_initialisierung_legt_zehn_bereiche_sechs_modelle_zehn_regeln_an(db):
    bereiche = LebensbereichRepository(db).alle()
    assert len(bereiche) == 10
    assert sum(b.soll_stunden for b in bereiche) == pytest.approx(143)
    assert [b.name for b in bereiche][:3] == ["Arbeit", "Schlaf", "Bewegung"]
    assert len(KompassRepository(db).alle()) == 6
    regeln = RegelRepository(db).alle()
    assert [r.kennung for r in regeln] == [f"R{i:02d}" for i in range(1, 11)]
    assert regeln[0].schwelle == 150


def test_initialisierung_idempotent(db):
    initialisiere(db)
    assert len(LebensbereichRepository(db).alle()) == 10
    assert len(RegelRepository(db).alle()) == 10


def test_obergrenzen_der_standardbereiche(db):
    repo = LebensbereichRepository(db)
    assert repo.nach_schluessel(StandardSchluessel.ARBEIT).typ is Bereichstyp.OBERGRENZE
    assert repo.nach_schluessel(StandardSchluessel.VERPFLICHTUNGEN).typ is Bereichstyp.OBERGRENZE
    assert repo.nach_schluessel(StandardSchluessel.SCHLAF).typ is Bereichstyp.MINDESTZIEL


def test_aktivitaet_roundtrip(db):
    repo = AktivitaetRepository(db)
    a = Aktivitaet(
        "Joggen",
        _bewegung(db).id,
        date(2026, 11, 10),
        45,
        Aktivitaetsstatus.DURCHGEFUEHRT,
        beginn=time(18, 0),
        ende=time(18, 45),
        zufriedenheit=4,
        belastung=2,
        erholung=4,
        bewegungsart=Bewegungsart.AUSDAUER_MODERAT,
        notiz="Runde am Fluss",
    )
    gespeichert = repo.speichern(a)
    assert gespeichert.id is not None
    assert repo.nach_id(gespeichert.id) == gespeichert


def test_aktivitaeten_im_zeitraum_sortiert(db):
    repo = AktivitaetRepository(db)
    bid = _bewegung(db).id
    status = Aktivitaetsstatus.DURCHGEFUEHRT
    repo.speichern(Aktivitaet("B", bid, date(2026, 11, 11), 30, status, beginn=time(9, 0)))
    repo.speichern(Aktivitaet("C", bid, date(2026, 11, 11), 30, status))
    repo.speichern(Aktivitaet("A", bid, date(2026, 11, 11), 30, status, beginn=time(7, 0)))
    repo.speichern(Aktivitaet("X", bid, date(2026, 11, 16), 30, status))
    titel = [a.titel for a in repo.im_zeitraum(date(2026, 11, 9), date(2026, 11, 15))]
    assert titel == ["A", "B", "C"]


def test_serie_mit_ausnahmen_roundtrip(db):
    repo = SerieRepository(db)
    s = Wiederholungsserie(
        "Joggen",
        _bewegung(db).id,
        frozenset({Wochentag.DI, Wochentag.DO}),
        date(2026, 11, 3),
        45,
        beginn=time(18, 0),
        ausnahmen={date(2026, 11, 19)},
        generiert_bis=date(2027, 11, 2),
        bewegungsart=Bewegungsart.AUSDAUER_MODERAT,
    )
    gespeichert = repo.speichern(s)
    assert repo.nach_id(gespeichert.id) == gespeichert
    gespeichert.ausnahmen.add(date(2026, 11, 24))
    repo.speichern(gespeichert)
    assert repo.nach_id(gespeichert.id).ausnahmen == {date(2026, 11, 19), date(2026, 11, 24)}


def test_serie_loeschen_entkoppelt_termine(db):
    serien, aktivitaeten = SerieRepository(db), AktivitaetRepository(db)
    bid = _bewegung(db).id
    s = serien.speichern(
        Wiederholungsserie("J", bid, frozenset({Wochentag.DI}), date(2026, 11, 3), 45)
    )
    a = aktivitaeten.speichern(
        Aktivitaet("J", bid, date(2026, 11, 3), 45, Aktivitaetsstatus.GEPLANT, serie_id=s.id)
    )
    serien.loeschen(s.id)
    assert aktivitaeten.nach_id(a.id).serie_id is None


def test_transaktion_rollback_bei_fehler(db):
    repo = AktivitaetRepository(db)
    with pytest.raises(RuntimeError), db.transaktion():
        repo.speichern(
            Aktivitaet("A", _bewegung(db).id, date(2026, 11, 10), 30, Aktivitaetsstatus.GEPLANT)
        )
        raise RuntimeError("Abbruch")
    assert repo.alle() == []


def test_aenderung_nach_neuem_oeffnen_vorhanden(tmp_path):
    pfad = tmp_path / "balanceos.db"
    db1 = Datenbank(pfad)
    initialisiere(db1)
    bid = LebensbereichRepository(db1).nach_schluessel(StandardSchluessel.BEWEGUNG).id
    AktivitaetRepository(db1).speichern(
        Aktivitaet("A", bid, date(2026, 11, 10), 30, Aktivitaetsstatus.GEPLANT)
    )
    db1.schliessen()
    db2 = Datenbank(pfad)
    assert len(AktivitaetRepository(db2).alle()) == 1
    db2.schliessen()


def test_einstellungen_speichern(db):
    repo = EinstellungenRepository(db)
    assert repo.laden() == Einstellungen()
    repo.speichern(Einstellungen(alpha=0.4, gesamtscore_anzeigen=True))
    assert repo.laden() == Einstellungen(alpha=0.4, gesamtscore_anzeigen=True)


def test_regel_aktiv_setzen(db):
    repo = RegelRepository(db)
    repo.aktiv_setzen("R03", False)
    assert not next(r for r in repo.alle() if r.kennung == "R03").aktiv


def test_ausblendungen(db):
    repo = AusblendungRepository(db)
    repo.ausblenden("R01", KW(2026, 46), None)
    repo.ausblenden("R08", KW(2026, 46), 4)
    repo.ausblenden("R08", KW(2026, 46), 4)  # doppelt ist erlaubt
    assert repo.ausgeblendet(KW(2026, 46)) == {("R01", None), ("R08", 4)}
    assert repo.ausgeblendet(KW(2026, 47)) == set()


def test_who5_und_reflexion(db):
    who5 = Who5Repository(db)
    who5.speichern(Who5Erhebung(date(2026, 11, 1), (1, 1, 1, 1, 1)))
    who5.speichern(Who5Erhebung(date(2026, 11, 15), (3, 4, 3, 2, 4)))
    assert [e.prozentwert for e in who5.alle()] == [64, 20]
    refl = ReflexionRepository(db)
    refl.speichern(Wochenreflexion(KW(2026, 46), ("a", "b", "c"), 4))
    refl.speichern(Wochenreflexion(KW(2026, 46), ("x", "", ""), None))
    gelesen = refl.fuer_kw(KW(2026, 46))
    assert gelesen.antworten == ("x", "", "") and gelesen.stimmung is None
    assert len(refl.alle()) == 1


def test_lebensbereich_hat_zuordnungen(db):
    repo = LebensbereichRepository(db)
    garten = repo.speichern(Lebensbereich("Garten", Bereichstyp.MINDESTZIEL, "#C2255C", 2.0))
    assert not repo.hat_zuordnungen(garten.id)
    AktivitaetRepository(db).speichern(
        Aktivitaet("Beet", garten.id, date(2026, 11, 10), 30, Aktivitaetsstatus.GEPLANT)
    )
    assert repo.hat_zuordnungen(garten.id)


def test_demodaten_markierung(db):
    repo = AktivitaetRepository(db)
    bid = _bewegung(db).id
    repo.einfuegen_viele(
        [Aktivitaet("D", bid, date(2026, 11, 10), 30, Aktivitaetsstatus.GEPLANT, ist_demo=True)]
    )
    repo.speichern(Aktivitaet("E", bid, date(2026, 11, 10), 30, Aktivitaetsstatus.GEPLANT))
    assert repo.gibt_demo()
    assert repo.loesche_demo() == 1
    assert not repo.gibt_demo()
    assert [a.titel for a in repo.alle()] == ["E"]


def test_alle_nutzdaten_loeschen_stellt_erststart_her(db):
    bereiche = LebensbereichRepository(db)
    b = bereiche.nach_schluessel(StandardSchluessel.ARBEIT)
    b.name, b.soll_stunden = "Job", 30
    bereiche.speichern(b)
    RegelRepository(db).aktiv_setzen("R01", False)
    EinstellungenRepository(db).speichern(Einstellungen(alpha=0.2))
    AktivitaetRepository(db).speichern(
        Aktivitaet("A", b.id, date(2026, 11, 10), 30, Aktivitaetsstatus.GEPLANT)
    )
    alle_nutzdaten_loeschen(db)
    assert AktivitaetRepository(db).alle() == []
    arbeit = bereiche.nach_schluessel(StandardSchluessel.ARBEIT)
    assert (arbeit.name, arbeit.soll_stunden) == ("Arbeit", 40)
    assert all(r.aktiv for r in RegelRepository(db).alle())
    assert EinstellungenRepository(db).laden() == Einstellungen()
