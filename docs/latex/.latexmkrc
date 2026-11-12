# latexmk-Konfiguration für alle Portfolio-Dokumente
# Aufruf aus einem Dokumentordner, z. B.:
#   cd docs/latex/01_Projektdokumentation && latexmk Projektdokumentation.tex
# oder komfortabel für alle Dokumente:  python tools/build_docs.py

$pdf_mode = 4;            # 4 = LuaLaTeX
$bibtex_use = 2;          # Biber automatisch ausführen
$lualatex = 'lualatex -interaction=nonstopmode -file-line-error -synctex=1 %O %S';
$out_dir = 'build';
$aux_dir = 'build';

# Gemeinsame Dateien (Klasse, meta.tex, Literatur) finden.
# Relativ, weil jedes Dokument genau eine Ebene unter docs/latex/ liegt
# (absolute Pfade scheitern am Leerzeichen im Projektordnernamen).
ensure_path('TEXINPUTS', '../_gemeinsam//');
ensure_path('BIBINPUTS', '../_gemeinsam//');
