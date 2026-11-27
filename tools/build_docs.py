"""Build- und Abgabe-Werkzeug für das Portfolio „Projekt: Software Engineering“.

Baut die LaTeX-Dokumente, prüft wichtige Formalia, fügt die Dokumente je
Phase zu einer PDF-Datei mit dem vorgeschriebenen Dateinamen zusammen und
erstellt die ZIP-Datei des Repositorys für Phase 3.

Beispiele (aus dem Projektordner):
    python tools/build_docs.py                 # Phase 1: Dokumente bauen + prüfen
    python tools/build_docs.py --phase 1 --abgabe
    python tools/build_docs.py --phase 2 --abgabe
    python tools/build_docs.py --phase 3 --abgabe --zip
    python tools/build_docs.py --doc Anforderungsdokument   # nur ein Dokument

Benötigt: MiKTeX (lualatex, pdflatex, latexmk, biber) und Git.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LATEX = ROOT / "docs" / "latex"
PDF_DIR = ROOT / "docs" / "pdf"
APP_DIR = ROOT / "app"
ABGABE = {
    1: ROOT / "abgabe" / "Phase1_Konzeption",
    2: ROOT / "abgabe" / "Phase2_Erarbeitung",
    3: ROOT / "abgabe" / "Phase3_Finalisierung",
}
DIST = ROOT / "dist"
DIAGRAMME = ROOT / "docs" / "diagramme"
DIAGRAMM_EXPORT = DIAGRAMME / "export"
DIAGRAMM_BUILD = DIAGRAMME / ".build"
DIAGRAMM_VORLAGE = DIAGRAMME / "_vorlage"


@dataclass(frozen=True)
class Dokument:
    ordner: str
    name: str
    ab_phase: int


# Reihenfolge = Reihenfolge in der zusammengefügten PDF (Aufgabenstellung 4.1)
DOKUMENTE = [
    Dokument("01_Projektdokumentation", "Projektdokumentation", 1),
    Dokument("02_Anforderungsdokument", "Anforderungsdokument", 1),
    Dokument("03_Spezifikationsdokument", "Spezifikationsdokument", 1),
    Dokument("04_Architekturdokument", "Architekturdokument", 2),
    Dokument("05_Testdokument", "Testdokument", 3),
    Dokument("06_Abstract", "Abstract", 3),
]

# Harmloser LuaTeX-Hinweis („ignored error“) bei seitenübergreifenden longtables
IGNORIERT = ("Infinite glue shrinkage",)

# Konsole unter Windows auf UTF-8 stellen (Umlaute in der Ausgabe)
for _strom in (sys.stdout, sys.stderr):
    if hasattr(_strom, "reconfigure"):
        _strom.reconfigure(encoding="utf-8")


class Fehler(Exception):
    pass


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------
def meta() -> dict[str, str]:
    """Liest Vorname, Nachname und Matrikelnummer aus meta.tex."""
    text = (LATEX / "_gemeinsam" / "meta.tex").read_text(encoding="utf-8")
    werte = {}
    for feld in ("Vorname", "Nachname", "Matrikelnummer"):
        treffer = re.search(r"\\newcommand\{\\" + feld + r"\}\{([^}]*)\}", text)
        if not treffer:
            raise Fehler(f"{feld} nicht in meta.tex gefunden")
        werte[feld] = treffer.group(1).strip()
    return werte


def dateipraefix(m: dict[str, str]) -> str:
    """Nachname-Vorname_Matrikelnummer (Aufgabenstellung 4.2)."""
    return f"{m['Nachname']}-{m['Vorname']}_{m['Matrikelnummer']}"


def platzhalter_in_meta(m: dict[str, str]) -> bool:
    return m["Vorname"] == "VORNAME" or m["Nachname"] == "NACHNAME" or set(m["Matrikelnummer"]) == {"0"}


def run(cmd: list[str], cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")


def tex_escape(text: str) -> str:
    return text.replace("\\", "/").replace("_", r"\_").replace("&", r"\&").replace("#", r"\#").replace("%", r"\%")


# ---------------------------------------------------------------------------
# Quellcode-Anhang (Anleitung „Schriftliche Prüfungsleistungen mit Dateianlagen“:
# Quellcode maschinenlesbar und kopierfähig im Anhang)
# ---------------------------------------------------------------------------
AUSSCHLUSS = {".venv", "venv", "build", "dist", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


# Zeichen, die in der Code-Schrift (Consolas) fehlen, und die Ersatzschrift aus iu-pse.cls
_ERSATZSCHRIFT = {0x25B6: "iusymbolschrift", 0x25C0: "iusymbolschrift", 0x2714: "iusymbolschrift",
                  0x26A0: "iusymbolschrift", 0x2139: "iusymbolschrift", 0xFFFD: "iuuischrift"}


def _listing_zeichen(z: str) -> str:
    """Setzt Zeichen jenseits von U+00FF als \\symbol{…} in einen Escape-Abschnitt (§…§)."""
    code = ord(z)
    if code <= 0xFF:
        return z
    if code in _ERSATZSCHRIFT:
        return f"§{{\\{_ERSATZSCHRIFT[code]}\\symbol{{{code}}}}}§"
    return f"§\\symbol{{{code}}}§"


def quellcode_anhang(build_dir: Path) -> int:
    dateien = sorted(
        p for p in APP_DIR.rglob("*.py")
        if not any(teil in AUSSCHLUSS for teil in p.relative_to(APP_DIR).parts)
    )
    build_dir.mkdir(parents=True, exist_ok=True)
    zeilen = [
        "% automatisch erzeugt von tools/build_docs.py – nicht von Hand bearbeiten",
        "Der folgende Quellcode ist vollständig und als kopierbarer Text wiedergegeben.",
        "Das Repository ist unter \\url{\\GitHubURL} abrufbar.",
        "",
    ]
    if not dateien:
        zeilen.append("\\TODO{Noch kein Quellcode in app/ vorhanden}")
    for datei in dateien:
        rel_app = datei.relative_to(ROOT).as_posix()
        # Pfad relativ zum Dokumentordner docs/latex/01_Projektdokumentation
        # listings setzt unter LuaLaTeX Zeichen jenseits von U+00FF an die falsche
        # Stelle. Deshalb eine Kopie, in der diese Zeichen als \symbol{…} in einem
        # Escape-Abschnitt (§…§) stehen; beim Kopieren aus dem PDF bleibt das Zeichen.
        kopie = build_dir / "quellcode" / datei.relative_to(APP_DIR)
        kopie.parent.mkdir(parents=True, exist_ok=True)
        kopie.write_text("".join(map(_listing_zeichen, datei.read_text(encoding="utf-8"))), encoding="utf-8")
        rel_doc = os.path.relpath(kopie, LATEX / "01_Projektdokumentation").replace("\\", "/")
        zeilen += [
            "\\par\\medskip\\textbf{Datei: " + tex_escape(rel_app) + "}\\par\\nopagebreak",
            "\\lstinputlisting[style=python,escapechar=§]{" + rel_doc + "}",
            "",
        ]
    (build_dir / "quellcode.tex").write_text("\n".join(zeilen), encoding="utf-8")
    return len(dateien)


# ---------------------------------------------------------------------------
# Bauen und prüfen
# ---------------------------------------------------------------------------
def baue_diagramme(alle: bool = False) -> None:
    """Übersetzt jede TikZ-Quelldatei docs/diagramme/<Ordner>/<name>.tex nach
    docs/diagramme/export/<name>.pdf (nur wenn Quelle oder Stil neuer ist)."""
    quellen = sorted(q for q in DIAGRAMME.glob("*/*.tex")
                     if q.parent.name not in {"export", ".build", "_vorlage"})
    if not quellen:
        return
    stil = DIAGRAMM_VORLAGE / "iu-diagramm.sty"
    DIAGRAMM_BUILD.mkdir(exist_ok=True)
    DIAGRAMM_EXPORT.mkdir(exist_ok=True)
    env = dict(os.environ, TEXINPUTS=f"{DIAGRAMM_VORLAGE}{os.pathsep}")
    neu = 0
    for q in quellen:
        ziel = DIAGRAMM_EXPORT / f"{q.stem}.pdf"
        aktuell = ziel.exists() and ziel.stat().st_mtime >= max(q.stat().st_mtime, stil.stat().st_mtime)
        if aktuell and not alle:
            continue
        erg = run(["lualatex", "-interaction=nonstopmode", "-halt-on-error",
                   f"-output-directory={DIAGRAMM_BUILD}", q.name], q.parent, env)
        pdf = DIAGRAMM_BUILD / f"{q.stem}.pdf"
        if erg.returncode != 0 or not pdf.exists():
            fehler = [z for z in erg.stdout.splitlines() if z.startswith("!") or ".tex:" in z]
            raise Fehler(f"Diagramm {q.relative_to(ROOT)} fehlerhaft: " + " | ".join(fehler[:5]))
        shutil.copy2(pdf, ziel)
        neu += 1
    print(f"Diagramme: {len(quellen)} Quelle(n), {neu} neu übersetzt")


def baue(dok: Dokument, phase: int) -> Path:
    ordner = LATEX / dok.ordner
    build = ordner / "build"
    if dok.name == "Projektdokumentation" and phase >= 2:
        n = quellcode_anhang(build)
        print(f"  Quellcode-Anhang: {n} Python-Datei(en)")
    env = dict(os.environ, IU_PHASE=str(phase))
    ergebnis = run(["latexmk", "-r", "../.latexmkrc", "-g", f"{dok.name}.tex"], ordner, env)
    log = build / f"{dok.name}.log"
    pdf = build / f"{dok.name}.pdf"
    if not pdf.exists() or not log.exists():
        print(ergebnis.stdout[-3000:], ergebnis.stderr[-2000:])
        raise Fehler(f"{dok.name}: kein PDF erzeugt")
    pruefe(dok, ordner, log)
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    ziel = PDF_DIR / f"{dok.name}.pdf"
    shutil.copy2(pdf, ziel)
    return ziel


def seiten(log_text: str) -> int:
    treffer = re.search(r"Output written on .*?\((\d+) pages?", log_text, re.S)
    return int(treffer.group(1)) if treffer else 0


def pruefe(dok: Dokument, ordner: Path, log: Path) -> None:
    text = log.read_text(encoding="utf-8", errors="replace")
    fehler = [
        z for z in text.splitlines()
        if (z.startswith("!") or re.match(r"^\.?/?[^:\s]+\.tex:\d+: ", z) or re.match(r"^[A-Za-z]:/.+:\d+: ", z))
        and not any(i in z for i in IGNORIERT)
    ]
    platzhalter = sorted(set(re.findall(r"IU-PSE-PLATZHALTER: (\S+)", text)))
    undefiniert = "There were undefined references" in text or "Citation" in text and "undefined" in text

    # \TODO, die tatsächlich im PDF stehen (die Klasse schreibt je \TODO
    # „IU-PSE-TODO“ ins Log; Kapitel späterer Phasen zählen so nicht mit)
    todos = text.count("IU-PSE-TODO")

    # Abbildungs-/Tabellenverzeichnis ab drei Einträgen Pflicht (Richtlinien 3.1)
    haupt = (ordner / f"{dok.name}.tex").read_text(encoding="utf-8")
    def aktiv(befehl: str) -> bool:
        return any(re.match(r"^\s*\\" + befehl + r"\b", z) for z in haupt.splitlines())
    hinweise = []
    for endung, befehl, art in (("lof", "abbildungsverzeichnis", "Abbildungen"), ("lot", "tabellenverzeichnis", "Tabellen")):
        datei = ordner / "build" / f"{dok.name}.{endung}"
        anzahl = datei.read_text(encoding="utf-8", errors="replace").count("\\contentsline") if datei.exists() else 0
        if anzahl >= 3 and not aktiv(befehl):
            hinweise.append(f"{anzahl} {art}: \\{befehl} ist Pflicht (ab 3)")
        if anzahl < 3 and aktiv(befehl):
            hinweise.append(f"nur {anzahl} {art}: \\{befehl} kann entfallen (Pflicht erst ab 3)")

    # Abstract: genau 2 Seiten Textteil (Aufgabenstellung 4.3)
    if dok.name == "Abstract":
        n = seiten(text) - 1  # ohne Titelblatt
        if n != 2:
            hinweise.append(f"Textteil hat {n} Seite(n) – gefordert sind 2 Seiten (ggf. Literaturverzeichnis abziehen)")

    status = "OK" if not (fehler or platzhalter or todos or hinweise) else "PRÜFEN"
    print(f"  [{status}] {dok.name}: {seiten(text)} Seiten")
    for z in fehler[:10]:
        print(f"    FEHLER: {z}")
    if todos:
        print(f"    offen: {todos} × \\TODO")
    if platzhalter:
        print(f"    fehlende Grafiken: {', '.join(platzhalter)}")
    if undefiniert:
        print("    Hinweis: undefinierte Verweise/Zitate – Schlüssel in literatur.bib prüfen")
    for h in hinweise:
        print(f"    Hinweis: {h}")


# ---------------------------------------------------------------------------
# Zusammenfügen (Aufgabenstellung 4.1 / 4.2)
# ---------------------------------------------------------------------------
def git(*args: str) -> str:
    return run(["git", *args], ROOT).stdout.strip()


def schutz_eingefrorene_abgabe(ziel: Path, phase: int, force: bool) -> None:
    """Phase-1/2-Ergebnisse müssen separat erhalten bleiben (Prüfungsleitfaden)."""
    tag = f"phase{phase}-abgabe"
    if ziel.exists() and git("tag", "--list", tag) and not force:
        raise Fehler(
            f"{ziel.name} wurde bereits eingereicht (Git-Tag {tag}). "
            "Die eingereichte Fassung muss unverändert erhalten bleiben. "
            "Nur mit --force überschreiben."
        )


def fuege_zusammen(pdfs: list[Path], ziel: Path, anlage: Path | None = None) -> None:
    build = ROOT / "abgabe" / ".build"
    build.mkdir(parents=True, exist_ok=True)
    teile = []
    for i, pdf in enumerate(pdfs):
        rel = os.path.relpath(pdf, build).replace("\\", "/")
        titel = pdf.stem
        opt = f"pages=-,addtotoc={{1,section,1,{titel},dok{i}}}"
        if i == 0 and anlage is not None:
            # Dateianlage oben links auf dem Deckblatt (Anleitung Dateianlagen, Kap. 3.1)
            rel_a = os.path.relpath(anlage, build).replace("\\", "/")
            opt += (",picturecommand*={\\put(40,780){\\attachfile2[icon=Paperclip,"
                    f"description={{{anlage.name}: Endung .txt entfernen, um die ZIP-Datei zu erhalten}}]"
                    f"{{{rel_a}}}}}}}")
        teile.append(f"\\includepdf[{opt}]{{{rel}}}")
    tex = "\n".join([
        "\\documentclass[a4paper]{article}",
        "\\usepackage{pdfpages}",
        "\\usepackage{attachfile2}",
        "\\usepackage[hidelinks,bookmarksopen]{hyperref}",
        "\\begin{document}",
        *teile,
        "\\end{document}",
    ])
    (build / "sammel.tex").write_text(tex, encoding="utf-8")
    for _ in range(2):  # zweimal für Lesezeichen
        ergebnis = run(["pdflatex", "-interaction=nonstopmode", "sammel.tex"], build)
    if not (build / "sammel.pdf").exists():
        print(ergebnis.stdout[-3000:])
        raise Fehler("Zusammenfügen fehlgeschlagen")
    ziel.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(build / "sammel.pdf", ziel)
    print(f"  -> {ziel.relative_to(ROOT)}")


def erstelle_zip(praefix: str) -> Path:
    """ZIP mit dem Inhalt des Repositorys (identisch zu GitHub, Aufgabenstellung 1.3)."""
    if git("status", "--porcelain"):
        raise Fehler("Es gibt nicht committete Änderungen. Erst committen und pushen, dann ZIP erstellen.")
    run(["git", "fetch", "origin"], ROOT)
    lokal, remote = git("rev-parse", "HEAD"), git("rev-parse", "@{u}")
    if lokal != remote:
        raise Fehler("Lokaler Stand ist nicht identisch mit GitHub (git push fehlt?). ZIP muss GitHub entsprechen.")
    DIST.mkdir(exist_ok=True)
    ziel = DIST / f"{praefix}_PSE_P3_Abgabe.zip"
    ergebnis = run(["git", "archive", "--format=zip", "-o", str(ziel), "HEAD"], ROOT)
    if ergebnis.returncode != 0:
        raise Fehler(ergebnis.stderr)
    print(f"  -> {ziel.relative_to(ROOT)} (Stand {lokal[:7]} = GitHub)")
    return ziel


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phase", type=int, choices=(1, 2, 3), default=1)
    parser.add_argument("--doc", help="nur dieses Dokument bauen (z. B. Anforderungsdokument)")
    parser.add_argument("--abgabe", action="store_true", help="Phasen-PDF mit IU-Dateinamen in abgabe/ erzeugen")
    parser.add_argument("--zip", action="store_true", help="(Phase 3) ZIP des Repositorys in dist/ erzeugen")
    parser.add_argument("--anlage", action="store_true",
                        help="(Phase 3) ZIP als .zip.txt-Dateianlage oben links auf dem Deckblatt einbetten")
    parser.add_argument("--diagramme", action="store_true", help="alle TikZ-Diagramme neu übersetzen")
    parser.add_argument("--force", action="store_true", help="eingefrorene Abgabe-PDF trotzdem überschreiben")
    args = parser.parse_args()

    try:
        m = meta()
        praefix = dateipraefix(m)
        if platzhalter_in_meta(m):
            print("WARNUNG: Name/Matrikelnummer in docs/latex/_gemeinsam/meta.tex sind noch Platzhalter.\n")

        if args.zip and not (args.abgabe or args.anlage or args.doc):
            # Nur verpacken: ein Neubau würde die Zeitstempel der PDFs ändern
            # und das Repository wieder vom GitHub-Stand abweichen lassen.
            erstelle_zip(praefix)
            return 0

        auswahl = [d for d in DOKUMENTE if d.ab_phase <= args.phase]
        if args.doc:
            auswahl = [d for d in DOKUMENTE if d.name.lower() == args.doc.lower()]
            if not auswahl:
                raise Fehler(f"Unbekanntes Dokument: {args.doc}")

        baue_diagramme(args.diagramme)
        print(f"Phase {args.phase}: baue {len(auswahl)} Dokument(e) …")
        pdfs = {d.name: baue(d, args.phase) for d in auswahl}

        if args.abgabe and not args.doc:
            if platzhalter_in_meta(m):
                raise Fehler("Abgabedateien werden erst erzeugt, wenn Name und Matrikelnummer in meta.tex stehen "
                             "(Dateiname: Nachname-Vorname_Matrikelnummer_PSE_P…).")
            print("Abgabedateien:")
            ordner = ABGABE[args.phase]
            if args.phase in (1, 2):
                ziel = ordner / f"{praefix}_PSE_P{args.phase}_Abgabe.pdf"
                schutz_eingefrorene_abgabe(ziel, args.phase, args.force)
                fuege_zusammen([pdfs[d.name] for d in auswahl], ziel)
            else:
                ordner.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pdfs["Abstract"], ordner / f"{praefix}_PSE_P3_Abstract.pdf")
                print(f"  -> {(ordner / f'{praefix}_PSE_P3_Abstract.pdf').relative_to(ROOT)}")
                final = f"{praefix}_PSE_P3_FinalesProdukt.pdf"
                fuege_zusammen([pdfs[d.name] for d in auswahl], ordner / final)
                if args.zip or args.anlage:
                    # Erst NACH Commit + Push der finalen PDFs aufrufen, damit die
                    # ZIP-Datei exakt dem GitHub-Stand entspricht.
                    zip_datei = erstelle_zip(praefix)
                    if args.anlage:
                        # Variante mit eingebetteter ZIP (.zip.txt) nur in dist/,
                        # damit das Repository unverändert bleibt.
                        anlage = DIST / (zip_datei.name + ".txt")
                        shutil.copy2(zip_datei, anlage)
                        fuege_zusammen([pdfs[d.name] for d in auswahl], DIST / final, anlage)
                for p in (1, 2):
                    alt = ABGABE[p] / f"{praefix}_PSE_P{p}_Abgabe.pdf"
                    status = "vorhanden" if alt.exists() else "FEHLT"
                    print(f"  Erneute Einreichung Phase {p}: {alt.relative_to(ROOT)} ({status})")
        elif args.zip:
            erstelle_zip(praefix)
    except Fehler as e:
        print(f"\nABBRUCH: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
