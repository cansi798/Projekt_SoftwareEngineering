# PyInstaller-Spezifikation für den Probebuild von BalanceOS (Ordner-Build, ohne Konsole).
# Aufruf im Ordner app/:  pyinstaller balanceos.spec
# Ergebnis: dist/BalanceOS/BalanceOS.exe (dist/ und build/ werden nicht eingecheckt).

a = Analysis(
    ["src/balanceos/__main__.py"],
    pathex=["src"],
    datas=[],
    hiddenimports=[],
    excludes=["tkinter", "unittest", "pytest", "PySide6.QtWebEngineCore", "PySide6.Qt3DCore"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="BalanceOS",
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="BalanceOS", upx=False)
