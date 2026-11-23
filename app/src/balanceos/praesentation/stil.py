"""Farben, Schrift und Stylesheet der Oberfläche."""

GRUEN = "#2F9E44"
ROT = "#E03131"
ORANGE = "#E8590C"
BLAU = "#1C7ED6"
TEXT = "#212529"
TEXT_LEISE = "#6C757D"
RAHMEN = "#DEE2E6"
FLAECHE = "#F8F9FA"
KARTE = "#FFFFFF"
LEISTE = "#1F2A37"
AKZENT = "#3A7D44"

FARBE_HINWEISART = {"WARNUNG": ORANGE, "POSITIV": GRUEN, "SYSTEM": BLAU}
SYMBOL_HINWEISART = {"WARNUNG": "⚠", "POSITIV": "✔", "SYSTEM": "ℹ"}

STYLESHEET = f"""
QWidget {{
    font-family: "Segoe UI", "Arial";
    font-size: 10pt;
    color: {TEXT};
}}
QMainWindow, QDialog, QStackedWidget, QScrollArea, QScrollArea > QWidget > QWidget {{
    background: {FLAECHE};
}}
QListWidget#seitenleiste {{
    background: {LEISTE};
    border: none;
    padding-top: 12px;
    outline: 0;
}}
QListWidget#seitenleiste::item {{
    color: #CED4DA;
    padding: 10px 18px;
    margin: 2px 8px;
    border-radius: 6px;
}}
QListWidget#seitenleiste::item:selected {{
    background: {AKZENT};
    color: white;
}}
QListWidget#seitenleiste::item:hover:!selected {{
    background: #2D3B4C;
}}
QLabel#logo {{
    background: {LEISTE};
    color: white;
    font-size: 15pt;
    font-weight: 600;
    padding: 16px 18px 4px 18px;
}}
QWidget#kopfzeile {{
    background: {KARTE};
    border-bottom: 1px solid {RAHMEN};
}}
QLabel#seitentitel {{
    font-size: 15pt;
    font-weight: 600;
}}
QLabel#kwLabel {{
    font-size: 11pt;
    font-weight: 600;
    min-width: 230px;
    qproperty-alignment: AlignCenter;
}}
QFrame#karte {{
    background: {KARTE};
    border: 1px solid {RAHMEN};
    border-radius: 8px;
}}
QLabel#kartentitel {{
    color: {TEXT_LEISE};
    font-size: 9pt;
    font-weight: 600;
    text-transform: uppercase;
}}
QLabel#grosszahl {{
    font-size: 22pt;
    font-weight: 600;
}}
QLabel#leise {{
    color: {TEXT_LEISE};
}}
QLabel#feldfehler {{
    color: {ROT};
    font-size: 9pt;
}}
QLabel#etikett {{
    border-radius: 9px;
    padding: 1px 8px;
    font-size: 8pt;
    font-weight: 600;
    color: white;
}}
QPushButton {{
    background: {KARTE};
    border: 1px solid #CED4DA;
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background: #F1F3F5;
}}
QPushButton:disabled {{
    color: #ADB5BD;
    background: #F1F3F5;
}}
QPushButton#primaer {{
    background: {AKZENT};
    border-color: {AKZENT};
    color: white;
    font-weight: 600;
}}
QPushButton#primaer:hover {{
    background: #2F6A39;
}}
QPushButton#primaer:disabled {{
    background: #A9C9AE;
    border-color: #A9C9AE;
}}
QPushButton#gefahr {{
    background: {ROT};
    border-color: {ROT};
    color: white;
    font-weight: 600;
}}
QPushButton#gefahr:disabled {{
    background: #F1AEB5;
    border-color: #F1AEB5;
}}
QPushButton#link {{
    border: none;
    background: transparent;
    color: {BLAU};
    padding: 2px 4px;
}}
QLineEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
    background: {KARTE};
    border: 1px solid #CED4DA;
    border-radius: 5px;
    padding: 4px 6px;
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus, QTimeEdit:focus {{
    border: 1px solid {AKZENT};
}}
*[fehler="true"] {{
    border: 2px solid {ROT};
}}
QTableWidget {{
    background: {KARTE};
    border: 1px solid {RAHMEN};
    gridline-color: #F1F3F5;
    selection-background-color: #D3F9D8;
    selection-color: {TEXT};
}}
QHeaderView::section {{
    background: #F1F3F5;
    border: none;
    border-bottom: 1px solid {RAHMEN};
    padding: 6px;
    font-weight: 600;
}}
QTabWidget::pane {{
    border: 1px solid {RAHMEN};
    background: {KARTE};
    border-radius: 6px;
}}
QTabBar::tab {{
    padding: 8px 16px;
}}
QTabBar::tab:selected {{
    border-bottom: 2px solid {AKZENT};
    font-weight: 600;
}}
QFrame#infokasten {{
    background: #E7F5FF;
    border: 1px solid #A5D8FF;
    border-radius: 6px;
}}
QFrame#warnkasten {{
    background: #FFF4E6;
    border: 1px solid #FFD8A8;
    border-radius: 6px;
}}
"""
"""Globales Qt-Stylesheet."""
