% =====================================================================
%  iu-pse.cls – Dokumentklasse für das Portfolio
%  „Projekt: Software Engineering (DLMCSPSE01_D)“, IU Internationale Hochschule
%
%  Setzt die „Richtlinien für die Gestaltung wissenschaftlicher Arbeiten
%  an der IU“ (Stand 01.10.2025) und den „Allgemeinen Zitierleitfaden“
%  (APA 7, Stand 01.10.2026) um:
%    - DIN A4, alle Ränder exakt 2,00 cm
%    - Arial 11 pt, einfarbig schwarz, Blocksatz, Silbentrennung
%    - Zeilenabstand 1,5; Absatz ohne Einzug, 6 pt Abstand danach
%    - Überschriften linksbündig fett: 16/14/11 pt,
%      Abstände 12/12 pt (Ebene 1) bzw. 12/6 pt (Ebene 2 und 3), max. 3 Ebenen
%    - Fußnoten Arial 10 pt, Blocksatz
%    - Seitenzahlen zentriert unten; Vorspann römisch (I, II, …), Titelblatt
%      zählt als I ohne Anzeige; Textteil arabisch ab 1 bis inkl. Anhang
%    - Inhaltsverzeichnis: nur Ebene 1 fett
%    - Abbildungen/Tabellen: Überschrift „Abb. 1 …“ / „Tab. 1 …“ oben,
%      „Quelle: …“ darunter in 10 pt
%    - Literaturverzeichnis APA 7 (biblatex-apa), linksbündig,
%      hängender Einzug 1,27 cm
%    - Anhänge „Anhang A: …“ mit Anhangsverzeichnis
%
%  Optionen:
%    abstract  – Formalia des Abstracts laut Aufgabenstellung
%                (Überschriften 12 pt, sonst wie oben)
%
%  Kompilieren mit LuaLaTeX + Biber (siehe .latexmkrc / tools/build_docs.py).
% =====================================================================
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{iu-pse}[2026/11/12 IU Portfolio Projekt Software Engineering]

\newif\if@iuabstract \@iuabstractfalse
\DeclareOption{abstract}{\@iuabstracttrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax

\LoadClass[11pt,a4paper,oneside]{article}

% ---------------------------------------------------------------------
%  Sprache, Schrift, Satzspiegel
% ---------------------------------------------------------------------
\RequirePackage{iftex}
\ifLuaTeX\else
  \ClassError{iu-pse}{Bitte mit LuaLaTeX kompilieren}{Die Klasse benötigt fontspec (Arial).}
\fi
\RequirePackage[ngerman]{babel}
\RequirePackage[autostyle=true,german=quotes]{csquotes}
\RequirePackage{fontspec}
% Arial explizit über die Windows-Schriftdateien laden (sonst wählt
% fontspec u. U. „Arial Narrow“ als Kursivschnitt).
\setmainfont{arial}[
  Extension      = .ttf,
  UprightFont    = *,
  BoldFont       = *bd,
  ItalicFont     = *i,
  BoldItalicFont = *bi]
\setsansfont{arial}[
  Extension      = .ttf,
  UprightFont    = *,
  BoldFont       = *bd,
  ItalicFont     = *i,
  BoldItalicFont = *bi]
% Quellcode im Anhang: Consolas (Windows-Standard, Monospace)
\setmonofont{consola}[
  Extension      = .ttf,
  UprightFont    = *,
  BoldFont       = *b,
  ItalicFont     = *i,
  BoldItalicFont = *z,
  Scale          = 0.95]
\renewcommand{\familydefault}{\sfdefault}

\RequirePackage[a4paper,top=2cm,bottom=2cm,left=2cm,right=2cm,
  includefoot=false,footskip=1cm]{geometry}
\RequirePackage[onehalfspacing]{setspace}
\RequirePackage{microtype}

% Absätze: keine Einrückung, 6 pt Abstand nach dem Absatz
\setlength{\parindent}{0pt}
\setlength{\parskip}{6pt plus 1pt}
% Blocksatz ist Standard; etwas toleranter, damit Silbentrennung
% statt überlanger Zeilen greift
\tolerance=1500
\emergencystretch=1.5em

% Einfarbig schwarz
\RequirePackage[table]{xcolor}
\color{black}

% Fußnoten: 10 pt, Blocksatz, einzeilig
\renewcommand{\footnotesize}{\fontsize{10pt}{12pt}\selectfont}
\RequirePackage[hang,flushmargin]{footmisc}

% ---------------------------------------------------------------------
%  Überschriften (max. 3 Ebenen)
%  Hinweis: \parskip (6 pt) wird von LaTeX vor und nach jeder Überschrift
%  zusätzlich eingefügt. Die Werte unten sind darum um 6 pt reduziert,
%  sodass sich effektiv 12 pt vor / 12 pt (Ebene 1) bzw. 6 pt (Ebene 2/3)
%  nach der Überschrift ergeben.
% ---------------------------------------------------------------------
\RequirePackage[raggedright]{titlesec}
\setcounter{secnumdepth}{3}
\setcounter{tocdepth}{3}
\if@iuabstract
  \titleformat{\section}{\fontsize{12pt}{15pt}\selectfont\bfseries}{\thesection}{0.6em}{}
  \titleformat{\subsection}{\fontsize{11pt}{14pt}\selectfont\bfseries}{\thesubsection}{0.6em}{}
  \titleformat{\subsubsection}{\fontsize{11pt}{14pt}\selectfont\bfseries}{\thesubsubsection}{0.6em}{}
\else
  \titleformat{\section}{\fontsize{16pt}{19pt}\selectfont\bfseries}{\thesection}{0.6em}{}
  \titleformat{\subsection}{\fontsize{14pt}{17pt}\selectfont\bfseries}{\thesubsection}{0.6em}{}
  \titleformat{\subsubsection}{\fontsize{11pt}{14pt}\selectfont\bfseries}{\thesubsubsection}{0.6em}{}
\fi
\titlespacing*{\section}{0pt}{6pt}{6pt}
\titlespacing*{\subsection}{0pt}{6pt}{0pt}
\titlespacing*{\subsubsection}{0pt}{6pt}{0pt}
% Eine 4. Ebene ist laut Richtlinien nicht vorgesehen.
\renewcommand{\paragraph}[1]{%
  \ClassError{iu-pse}{\string\paragraph\space ist nicht erlaubt}%
  {Die IU-Richtlinien erlauben maximal drei Gliederungsebenen.}}

% Neue Hauptkapitel beginnen auf einer neuen Seite? -> Nein (nicht gefordert),
% kann bei Bedarf mit \clearpage im Dokument gesetzt werden.

% ---------------------------------------------------------------------
%  Verzeichnisse
% ---------------------------------------------------------------------
\RequirePackage[titles]{tocloft}
\renewcommand{\cfttoctitlefont}{\fontsize{16pt}{19pt}\selectfont\bfseries}
\renewcommand{\cftloftitlefont}{\fontsize{16pt}{19pt}\selectfont\bfseries}
\renewcommand{\cftlottitlefont}{\fontsize{16pt}{19pt}\selectfont\bfseries}
\setlength{\cftbeforetoctitleskip}{0pt}
\setlength{\cftbeforeloftitleskip}{0pt}
\setlength{\cftbeforelottitleskip}{0pt}
\setlength{\cftaftertoctitleskip}{12pt}
\setlength{\cftafterloftitleskip}{12pt}
\setlength{\cftafterlottitleskip}{12pt}
% Nur Ebene 1 fett
\renewcommand{\cftsecfont}{\bfseries}
\renewcommand{\cftsecpagefont}{\bfseries}
\renewcommand{\cftsubsecfont}{\normalfont}
\renewcommand{\cftsubsecpagefont}{\normalfont}
\renewcommand{\cftsubsubsecfont}{\normalfont}
\renewcommand{\cftsubsubsecpagefont}{\normalfont}
\renewcommand{\cftsecleader}{\cftdotfill{\cftdotsep}}
\setlength{\cftbeforesecskip}{3pt}
% Abbildungs-/Tabellenverzeichnis im Stil „Abb. 1 Titel …… 5“
\renewcommand{\cftfigpresnum}{Abb.~}
\renewcommand{\cfttabpresnum}{Tab.~}
\setlength{\cftfignumwidth}{4em}
\setlength{\cfttabnumwidth}{4em}
\setlength{\cftfigindent}{0pt}
\setlength{\cfttabindent}{0pt}
\renewcommand{\listfigurename}{Abbildungsverzeichnis}
\renewcommand{\listtablename}{Tabellenverzeichnis}
\renewcommand{\contentsname}{Inhaltsverzeichnis}

% Anhangsverzeichnis (eigene Liste)
\newcommand{\listanhangname}{Anhangsverzeichnis}
\newlistof{anhang}{anh}{\listanhangname}
\renewcommand{\cftanhtitlefont}{\fontsize{16pt}{19pt}\selectfont\bfseries}
\setlength{\cftbeforeanhtitleskip}{0pt}
\setlength{\cftafteranhtitleskip}{12pt}
\setlength{\cftanhangindent}{0pt}
\setlength{\cftanhangnumwidth}{0pt}

% ---------------------------------------------------------------------
%  Abbildungen, Tabellen, Quellenangaben
% ---------------------------------------------------------------------
\RequirePackage{graphicx}
\RequirePackage{float}
\RequirePackage{booktabs}
\RequirePackage{tabularx}
\RequirePackage{longtable}
\RequirePackage{array}
\RequirePackage{multirow}
\RequirePackage{makecell}
\RequirePackage[shortlabels]{enumitem}
\setlist{itemsep=0pt,topsep=2pt,parsep=0pt}
\RequirePackage[
  labelsep=space,
  justification=raggedright,
  singlelinecheck=false,
  labelfont=bf,
  font=normalsize,
  skip=4pt]{caption}
\captionsetup[figure]{name=Abb.,position=top}
\captionsetup[table]{name=Tab.,position=top}
\captionsetup[longtable]{name=Tab.,position=top}
\graphicspath{{../../diagramme/export/}{../../bilder/}{../../diagramme/}}

% \grafik[Breite]{Dateiname ohne Endung}
% Sucht nacheinander in docs/diagramme/export/ und docs/bilder/ nach
% .pdf, .png, .jpg. Fehlt die Datei noch, erscheint ein gerahmter
% Platzhalter (und tools/build_docs.py meldet ihn).
\newcommand{\iu@grafikgefunden}{}
\newcommand{\grafik}[2][\linewidth]{%
  \def\iu@grafikgefunden{}%
  \@for\iu@ort:={../../diagramme/export/,../../bilder/}\do{%
    \@for\iu@ext:={.pdf,.png,.jpg}\do{%
      \ifx\iu@grafikgefunden\@empty
        \IfFileExists{\iu@ort#2\iu@ext}{\edef\iu@grafikgefunden{\iu@ort#2\iu@ext}}{}%
      \fi}}%
  \ifx\iu@grafikgefunden\@empty
    \fbox{\parbox[c][4cm][c]{\dimexpr#1-2\fboxsep-2\fboxrule}{\centering
      \textbf{[PLATZHALTER: Grafik \enquote{\detokenize{#2}} fehlt]}\\[4pt]
      \fontsize{9pt}{11pt}\selectfont Export nach docs/diagramme/export/\detokenize{#2}.pdf}}%
    \typeout{IU-PSE-PLATZHALTER: #2}%
  \else
    \includegraphics[width=#1,height=0.75\textheight,keepaspectratio]{\iu@grafikgefunden}%
  \fi}

% \quelle{Eigene Darstellung.}  -> „Quelle: Eigene Darstellung.“ (10 pt)
% Varianten laut Zitierleitfaden Kap. 2.2.5:
%   Eigene Darstellung.
%   Eigene Darstellung in Anlehnung an Autor, Jahr, S. x.
%   Eigene Darstellung (geändert) in Anlehnung an Autor, Jahr, S. x.
%   Eigene Darstellung auf der Basis von Autor, Jahr, S. x.
%   Übernommen aus Autor, Jahr.
\newcommand{\quelle}[1]{%
  \par\vspace{2pt}{\raggedright\fontsize{10pt}{12pt}\selectfont Quelle: #1\par}}

% Tabellen: Standardabstände und Spaltentypen
% Richtlinien Kap. 2: „Tabellen und Abbildungen: bei Bedarf kleinere Schrift
% als 11 Pt.“ -> einheitlich 10 pt, einzeilig; Beschriftung bleibt 11 pt
% (caption: font=normalsize), Quellenangabe 10 pt (\quelle).
\RequirePackage{etoolbox}
\newcommand{\iu@tabellensatz}{%
  \singlespacing\fontsize{10pt}{12pt}\selectfont\renewcommand{\arraystretch}{1.15}}
% Mindestens ca. 6 Textzeilen Platz vor einer longtable, damit nie nur
% Beschriftung und Tabellenkopf am Seitenende stehen
\RequirePackage{needspace}
\AtBeginEnvironment{longtable}{\needspace{6\baselineskip}\iu@tabellensatz}
\AtBeginEnvironment{table}{\iu@tabellensatz}
\renewcommand{\arraystretch}{1.25}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{Y}{>{\raggedright\arraybackslash}X}
\setlength{\LTpre}{6pt}
\setlength{\LTpost}{0pt}

% ---------------------------------------------------------------------
%  Literatur (APA 7 gemäß IU-Zitierleitfaden)
%  Kurzbelege IMMER mit Seitenangabe (IU strenger als APA):
%     \parencite[S.~12]{key}   -> (Autor, Jahr, S. 12)
%     \textcite[S.~12]{key}    -> Autor (Jahr, S. 12)
% ---------------------------------------------------------------------
\RequirePackage[style=apa,backend=biber,sortcites=true]{biblatex}
\setlength{\bibhang}{1.27cm}
\setlength{\bibitemsep}{0pt}
\DefineBibliographyStrings{ngerman}{
  andothers = {et al\adddot},
}
\renewcommand*{\bibfont}{\normalfont\raggedright}
\newcommand{\literaturverzeichnis}{%
  \clearpage
  \printbibliography[heading=bibintoc,title=Literaturverzeichnis]}

% ---------------------------------------------------------------------
%  Quellcode (Anhang) – maschinenlesbar und kopierfähig
%  Laut Anleitung „Schriftliche Prüfungsleistungen mit Dateianlagen“
%  muss Quellcode als kopierbarer Text (nicht als Screenshot) im Anhang
%  stehen. Leerzeichen werden deshalb als echte Leerzeichen-Zeichen
%  ausgegeben, damit die Python-Einrückung beim Kopieren erhalten bleibt.
% ---------------------------------------------------------------------
\RequirePackage{listings}
\lstset{
  basicstyle=\ttfamily\fontsize{8.5pt}{10.5pt}\selectfont,
  columns=fullflexible,
  keepspaces=true,
  showspaces=true,
  showstringspaces=false,
  breaklines=true,
  breakatwhitespace=false,
  postbreak=\mbox{$\hookrightarrow$\space},
  % keine Zeilennummern: sonst würden sie beim Kopieren (Plagiatsprüfung)
  % mitkopiert und die Python-Einrückung verfälschen
  numbers=none,
  frame=single,
  rulecolor=\color{black},
  tabsize=4,
  upquote=true,
  extendedchars=true,
  literate=
    {ä}{{ä}}1 {ö}{{ö}}1 {ü}{{ü}}1 {Ä}{{Ä}}1 {Ö}{{Ö}}1 {Ü}{{Ü}}1 {ß}{{ß}}1
    {€}{{€}}1 {„}{{„}}1 {“}{{“}}1 {–}{{–}}1 {—}{{—}}1 {…}{{…}}1
    {é}{{é}}1 {è}{{è}}1 {à}{{à}}1,
}
\lstdefinestyle{python}{language=Python}
\def\lst@visiblespace{\char32}  % echtes Leerzeichen statt „␣“

% ---------------------------------------------------------------------
%  Abkürzungsverzeichnis
%  Verwendung:  \begin{abkuerzungen}[LÄNGSTE] \acro{GUI}{Graphical User Interface} … \end{abkuerzungen}
%  Im Text:     \ac{GUI}  (erste Verwendung ausgeschrieben)
% ---------------------------------------------------------------------
\RequirePackage[printonlyused]{acronym}
\newenvironment{abkuerzungen}[1][MMMMMM]{%
  \clearpage
  \section*{Abkürzungsverzeichnis}%
  \addcontentsline{toc}{section}{Abkürzungsverzeichnis}%
  \begin{acronym}[#1]}{\end{acronym}}

% ---------------------------------------------------------------------
%  Hyperlinks (schwarz, PDF-Lesezeichen)
% ---------------------------------------------------------------------
\RequirePackage[hidelinks,bookmarksnumbered,bookmarksopen,unicode]{hyperref}
\RequirePackage{bookmark}
\urlstyle{same}
\RequirePackage{xurl}

% ---------------------------------------------------------------------
%  Metadaten (aus meta.tex) und Titelblatt
% ---------------------------------------------------------------------
\newcommand{\dokumenttitel}[1]{\def\@dokumenttitel{#1}}
\newcommand{\dokumentuntertitel}[1]{\def\@dokumentuntertitel{#1}}
\newcommand{\abgabedatum}[1]{\def\@abgabedatum{#1}}
\dokumenttitel{}
\dokumentuntertitel{}
\abgabedatum{\AbgabedatumStandard}

% Titelblatt laut Richtlinien (Kap. 3.2, Anhang C): nur diese Angaben
\newcommand{\titelblatt}{%
  \begin{titlepage}
    \pagenumbering{Roman}%
    \thispagestyle{empty}%
    \hypersetup{pdftitle={\@dokumenttitel},pdfauthor={\Vorname\space\Nachname}}%
    \centering
    \vspace*{1.5cm}
    {\fontsize{14pt}{18pt}\selectfont \Pruefungsform\par}
    \vspace{4pt}
    {\fontsize{12pt}{16pt}\selectfont \Kursname\par}
    \vspace{2.2cm}
    {\fontsize{12pt}{16pt}\selectfont \Hochschule\par}
    \vspace{4pt}
    {\fontsize{12pt}{16pt}\selectfont Studiengang: \Studiengang\par}
    \vspace{2.2cm}
    {\fontsize{20pt}{26pt}\selectfont\bfseries \@dokumenttitel\par}
    \ifx\@dokumentuntertitel\@empty\else
      \vspace{8pt}
      {\fontsize{14pt}{19pt}\selectfont \@dokumentuntertitel\par}
    \fi
    \vfill
    \begin{tabular}{@{}l@{\hspace{1em}}l@{}}
      Name:                          & \Vorname\ \Nachname \\
      Matrikelnummer:                & \Matrikelnummer \\
      Betreuende Person/Tutor:in:    & \Tutor \\
      Abgabedatum:                   & \@abgabedatum \\
    \end{tabular}
    \par\vspace*{1cm}
  \end{titlepage}
  \setcounter{page}{2}%
}

% Vorspann (römisch) -> Hauptteil (arabisch ab 1)
\newcommand{\verzeichnisse}{%
  \tableofcontents
  \clearpage}
\newcommand{\abbildungsverzeichnis}{%
  \listoffigures
  \addcontentsline{toc}{section}{\listfigurename}%
  \clearpage}
\newcommand{\tabellenverzeichnis}{%
  \listoftables
  \addcontentsline{toc}{section}{\listtablename}%
  \clearpage}
\newcommand{\hauptteil}{%
  \clearpage
  \pagenumbering{arabic}%
  \setcounter{page}{1}}

% Gender-Hinweis (optional, Richtlinien Anhang A) – vor dem Hauptteil
\newcommand{\genderhinweis}{%
  \clearpage
  \section*{Hinweis zur geschlechtergerechten Sprache}
  Aus Gründen der besseren Lesbarkeit wird in diesem Dokument überwiegend
  das generische Maskulinum verwendet. Selbstverständlich sind damit
  Personen aller Geschlechter gleichermaßen gemeint.
  \clearpage}

% ---------------------------------------------------------------------
%  Anhang:  \anhang  … \anhangsteil{Titel} …
%  -> „Anhang A: Titel“, Eintrag ins Anhangsverzeichnis
%  Seitenzahlen laufen arabisch weiter.
% ---------------------------------------------------------------------
\newcounter{iuanhang}
\renewcommand{\theiuanhang}{\Alph{iuanhang}}
\newcommand{\anhang}{%
  \clearpage
  \section*{\listanhangname}%
  \addcontentsline{toc}{section}{Anhang}%
  \@starttoc{anh}%
  \clearpage}
\newcommand{\anhangsteil}[1]{%
  \clearpage
  \refstepcounter{iuanhang}%
  \section*{Anhang \theiuanhang: #1}%
  \addcontentsline{anh}{anhang}{Anhang \theiuanhang: #1}}

% ---------------------------------------------------------------------
%  Arbeitshilfen
%  \TODO{…} markiert offene Stellen (fett in eckigen Klammern).
%  tools/build_docs.py warnt, solange noch \TODO im Text steht.
% ---------------------------------------------------------------------
\newcommand{\TODO}[1]{\typeout{IU-PSE-TODO}\textbf{[TODO: #1]}}
\newcommand{\anf}[1]{\enquote{#1}}

\pagestyle{plain}  % Seitenzahl zentriert am Seitenende
\endinput
