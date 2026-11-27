# PyInstaller-Spezifikation für die ausgelieferte Anwendung (eine einzelne .exe, ohne Konsole).
# Aufruf im Ordner app/:  pyinstaller balanceos.spec --distpath release --workpath build
# Ergebnis: release/BalanceOS.exe (wird eingecheckt); build/ bleibt lokal.
#
# BalanceOS nutzt nur QtCore, QtGui und QtWidgets. Qt-Teile, die PyInstaller über
# Plugins mitzieht, aber nie geladen werden (Quick/QML, PDF, Netzwerk/TLS, virtuelle
# Tastatur, Software-OpenGL), bleiben draußen. Das hält die Datei klein und passt zu
# NFA05 (keine Netzwerkfunktionen).

UNNOETIG = (
    "opengl32sw",
    "qt6quick",
    "qt6qml",
    "qt6pdf",
    "qt6network",
    "qt6virtualkeyboard",
    "qtvirtualkeyboardplugin",
    "qpdf",
    "qnetworklistmanager",
    "qopensslbackend",
    "qschannelbackend",
    "qcertonlybackend",
    "libcrypto",
    "libssl",
)


def benoetigt(eintrag) -> bool:
    """Prüft, ob ein gesammelter Eintrag (Ziel, Quelle, Typ) in die exe gehört."""
    pfad = eintrag[0].replace("\\", "/").lower()
    name = pfad.rsplit("/", 1)[-1]
    if "/translations/" in pfad:
        # Nur die deutsche Übersetzung der Qt-Standardtexte („Ja“/„Nein“), NFA01.
        return name == "qtbase_de.qm"
    return not name.startswith(UNNOETIG)


a = Analysis(
    ["src/balanceos/__main__.py"],
    pathex=["src"],
    datas=[],
    hiddenimports=[],
    excludes=[
        "tkinter",
        "unittest",
        "pytest",
        "ssl",
        "PySide6.QtNetwork",
        "PySide6.QtQml",
        "PySide6.QtQuick",
        "PySide6.QtPdf",
        "PySide6.QtWebEngineCore",
        "PySide6.Qt3DCore",
    ],
    noarchive=False,
)
a.binaries = [b for b in a.binaries if benoetigt(b)]
a.datas = [d for d in a.datas if benoetigt(d)]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="BalanceOS",
    console=False,
    upx=False,
    runtime_tmpdir=None,
)
