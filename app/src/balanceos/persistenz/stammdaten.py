"""Stammdaten beim ersten Start: Standardbereiche, Kompass-Modelle und Regeln.

Die Werte stammen aus dem Spezifikationsdokument (Tabellen
„Standard-Lebensbereiche beim ersten Start“, „Regelkatalog der
Hinweisregeln“ und Abschnitt „Beziehungen und Klassendiagramm“).
"""

from balanceos.domaene.modell import KompassModell, Lebensbereich, Regel
from balanceos.domaene.typen import Bereichstyp, Evidenzart, StandardSchluessel
from balanceos.persistenz.datenbank import Datenbank

_M, _O = Bereichstyp.MINDESTZIEL, Bereichstyp.OBERGRENZE
_S = StandardSchluessel

STANDARDBEREICHE: list[Lebensbereich] = [
    Lebensbereich("Arbeit", _O, "#4C6EF5", 40, standard_schluessel=_S.ARBEIT),
    Lebensbereich("Schlaf", _M, "#5C4B8A", 56, standard_schluessel=_S.SCHLAF),
    Lebensbereich("Bewegung", _M, "#3A7D44", 3, standard_schluessel=_S.BEWEGUNG),
    Lebensbereich("Familie", _M, "#E8590C", 10, standard_schluessel=_S.FAMILIE),
    Lebensbereich("Hobbys", _M, "#F08C00", 4, standard_schluessel=_S.HOBBYS),
    Lebensbereich("Soziale Kontakte", _M, "#D6336C", 4, standard_schluessel=_S.SOZIALE_KONTAKTE),
    Lebensbereich("Freizeit", _M, "#1098AD", 6, standard_schluessel=_S.FREIZEIT),
    Lebensbereich("Erholung", _M, "#2B8A3E", 5, standard_schluessel=_S.ERHOLUNG),
    Lebensbereich(
        "Persönliche Entwicklung", _M, "#7048E8", 3, standard_schluessel=_S.PERSOENLICHE_ENTWICKLUNG
    ),
    Lebensbereich(
        "Alltägliche Verpflichtungen", _O, "#868E96", 12, standard_schluessel=_S.VERPFLICHTUNGEN
    ),
]
"""Die zehn Standardbereiche in Anzeigereihenfolge (Summe der Soll-Werte: 143 h)."""

FARBPALETTE: list[str] = [b.farbe for b in STANDARDBEREICHE] + ["#C2255C", "#0B7285"]
"""Auswahlfarben für Lebensbereiche."""

KOMPASSMODELLE: list[KompassModell] = [
    KompassModell(
        "LBM",
        "Lifestyle Balance Model",
        "Das Modell von Matuska und Christiansen versteht Lebensbalance als ein befriedigendes "
        "Muster täglicher Betätigungen, das gesund, bedeutsam und nachhaltig ist und zu den "
        "aktuellen Lebensumständen passt. Balance bedeutet danach nicht, dass alle Menschen "
        "dieselbe Zeit für dieselben Bereiche aufwenden. Maßstab ist das eigene Muster. "
        "BalanceOS übernimmt diesen Gedanken, indem es jede Woche an Ihrem persönlichen "
        "Wunschprofil misst.",
        Evidenzart.THEORIE,
        "Matuska, K. M., & Christiansen, C. H. (2008). A proposed model of lifestyle balance. "
        "Journal of Occupational Science, 15(1), 9–19.",
        "Das Modell ist ein theoretischer Vorschlag und kein Messinstrument. Die Score-Formel "
        "und die Schwellenwerte von BalanceOS sind programmeigen und nicht validiert; das Soll "
        "ist ein persönlicher Maßstab.",
    ),
    KompassModell(
        "ERM",
        "Effort-Recovery-Modell",
        "Das Effort-Recovery-Modell von Meijman und Mulder beschreibt, dass Anstrengung "
        "kurzfristige Beanspruchung erzeugt, die sich nur bei ausreichender Erholung wieder "
        "zurückbildet. Fehlt die Erholung über längere Zeit, können sich die Folgen der "
        "Beanspruchung aufsummieren. BalanceOS achtet deshalb auf Tage mit hoher Belastung "
        "und geringer Erholung sowie auf Wochenenden ohne Erholung.",
        Evidenzart.THEORIE,
        "Meijman, T. F., & Mulder, G. (1998). Psychological aspects of workload. In P. J. D. "
        "Drenth, H. Thierry, & C. J. de Wolff (Hrsg.), Handbook of work and organizational "
        "psychology: Vol. 2. Work psychology (2. Aufl., S. 5–33). Psychology Press.",
        "Die Skalen für Belastung und Erholung (1–5) sind programmeigen und nicht validiert. "
        "Die Regeln übertragen die Theorie in feste Schwellen und zeigen Zusammenhänge in Ihren "
        "Daten, keine Ursachen.",
    ),
    KompassModell(
        "JDR",
        "Job-Demands-Resources-Theorie",
        "Die Job-Demands-Resources-Theorie von Bakker und Demerouti unterscheidet "
        "Arbeitsanforderungen, die Kraft kosten, von Arbeitsressourcen, die bei der "
        "Bewältigung helfen. Hohe Anforderungen ohne ausreichende Ressourcen gelten als "
        "Risiko für Erschöpfung. BalanceOS weist darauf hin, wenn die Arbeitszeit wiederholt "
        "über Ihrem Wunsch liegt und die Belastung dabei hoch ist.",
        Evidenzart.THEORIE,
        "Bakker, A. B., & Demerouti, E. (2017). Job demands–resources theory: Taking stock and "
        "looking forward. Journal of Occupational Health Psychology, 22(3), 273–285.",
        "BalanceOS erfasst Ressourcen nicht direkt. Arbeitszeit und Belastungsskala sind nur "
        "Annäherungen; die Belastungsskala ist programmeigen.",
    ),
    KompassModell(
        "WHO_BEWEGUNG",
        "WHO-Bewegungsleitlinie",
        "Die Leitlinie der Weltgesundheitsorganisation empfiehlt Erwachsenen pro Woche 150 bis "
        "300 Minuten moderate oder 75 bis 150 Minuten intensive Ausdaueraktivität sowie an "
        "mindestens zwei Tagen muskelkräftigende Aktivitäten. BalanceOS zählt intensive Minuten "
        "deshalb doppelt und prüft die Tage mit Krafttraining.",
        Evidenzart.EMPFEHLUNG,
        "Bull, F. C., Al-Ansari, S. S., Biddle, S., Borodulin, K., Buman, M. P., Cardon, G., "
        "et al. (2020). World Health Organization 2020 guidelines on physical activity and "
        "sedentary behaviour. British Journal of Sports Medicine, 54(24), 1451–1462.",
        "Berücksichtigt werden nur erfasste Aktivitäten mit Bewegungsart. Die Empfehlung gilt "
        "allgemein für Erwachsene und ersetzt keine ärztliche Beratung.",
    ),
    KompassModell(
        "SCHLAF",
        "Schlafempfehlung",
        "Die gemeinsame Konsenserklärung der American Academy of Sleep Medicine und der Sleep "
        "Research Society empfiehlt Erwachsenen, regelmäßig mindestens sieben Stunden pro Nacht "
        "zu schlafen. BalanceOS vergleicht Ihre durchschnittliche Schlafdauer der Woche mit "
        "diesem Richtwert.",
        Evidenzart.EMPFEHLUNG,
        "Watson, N. F., Badr, M. S., Belenky, G., Bliwise, D. L., Buxton, O. M., Buysse, D., "
        "et al. (2015). Recommended amount of sleep for a healthy adult. Sleep, 38(6), 843–844.",
        "Erfasst wird nur die Dauer, nicht die Schlafqualität. Der Mittelwert wird erst ab vier "
        "Tagen mit Schlafeintrag gebildet; der Hinweis ersetzt keine ärztliche Beratung.",
    ),
    KompassModell(
        "SYSTEM",
        "BalanceOS-Systemregeln",
        "Diese Regeln stammen von BalanceOS selbst. Sie sorgen dafür, dass eine Woche nur dann "
        "bewertet wird, wenn genug Einträge vorliegen. Fehlende Einträge sollen nicht als "
        "schlechte Balance erscheinen. Deshalb gibt es Scores erst ab vier von sieben Tagen "
        "mit mindestens einer durchgeführten Aktivität.",
        Evidenzart.PROGRAMMEIGEN,
        "BalanceOS (2026). Programmeigene Festlegung, siehe Spezifikationsdokument, Kapitel 2.",
        "Die Grenze von vier Tagen ist eine Festlegung von BalanceOS und nicht wissenschaftlich "
        "begründet.",
    ),
]
"""Die sechs Modelle des Balance-Kompasses in Anzeigereihenfolge."""

REGELN: list[Regel] = [
    Regel("R01", "Ausdauerbewegung unter Richtwert", "WHO_BEWEGUNG", 150, 1),
    Regel("R02", "Muskelkräftigung unter Richtwert", "WHO_BEWEGUNG", 2, 1),
    Regel("R03", "Schlafdauer unter Empfehlung", "SCHLAF", 7, 1),
    Regel("R04", "Bereich dauerhaft unter Wunsch", "LBM", 0.5, 3),
    Regel("R05", "Hohe Belastung bei geringer Erholung", "ERM", 4, 1),
    Regel("R06", "Wochenende ohne Erholung", "ERM", 6, 1),
    Regel("R07", "Arbeit über Soll bei hoher Belastung", "JDR", 4, 3),
    Regel("R08", "Wunsch erreicht", "LBM", 1, 1),
    Regel("R09", "Zufriedenheit gestiegen", "LBM", 1, 2),
    Regel("R10", "Zu wenig Daten", "SYSTEM", 4, 1),
]
"""Regelkatalog R01–R10 mit Schwelle und Zeitraum in Wochen."""


def initialisiere(db: Datenbank) -> None:
    """Legt fehlende Stammdaten an; bereits vorhandene Daten bleiben unverändert."""
    with db.transaktion() as con:
        for nr, b in enumerate(STANDARDBEREICHE):
            con.execute(
                "INSERT OR IGNORE INTO lebensbereich (name, typ, farbe, soll_stunden, gewicht,"
                " aktiv, standard_schluessel, reihenfolge) VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
                (b.name, b.typ, b.farbe, b.soll_stunden, b.gewicht, b.standard_schluessel, nr),
            )
        for nr, m in enumerate(KOMPASSMODELLE):
            con.execute(
                "INSERT OR IGNORE INTO kompassmodell VALUES (?, ?, ?, ?, ?, ?, ?)",
                (m.schluessel, m.name, m.kurzbeschreibung, m.evidenzart, m.quelle, m.grenzen, nr),
            )
        for r in REGELN:
            con.execute(
                "INSERT OR IGNORE INTO regel VALUES (?, ?, ?, ?, ?, 1)",
                (r.kennung, r.bezeichnung, r.modell_schluessel, r.schwelle, r.zeitraum),
            )
        con.execute("INSERT OR IGNORE INTO einstellungen VALUES (1, 0.6, 0)")
