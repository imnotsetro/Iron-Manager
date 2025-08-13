import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

def apply_default_light_style(app: QApplication):
    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#ffffff"))
    palette.setColor(QPalette.WindowText, QColor("#000000"))
    palette.setColor(QPalette.Base, QColor("#f2f2f2"))
    palette.setColor(QPalette.AlternateBase, QColor("#e0e0e0"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#000000"))
    palette.setColor(QPalette.Text, QColor("#000000"))
    palette.setColor(QPalette.Button, QColor("#e0e0e0"))
    palette.setColor(QPalette.ButtonText, QColor("#000000"))
    palette.setColor(QPalette.Highlight, QColor("#4285f4"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    app.setStyleSheet("""
        QPushButton {
            border: 1px solid #888888;
            border-radius: 4px;
            background-color: #f0f0f0;
            color: #000000;
            padding: 6px 12px;
            font-size: 13px;
        }
        QPushButton:hover {
            background-color: #e0e0e0;
        }
        QPushButton:pressed {
            background-color: #d0d0d0;
        }

        QPushButton#sidebarButton {
            background-color: #ffffff;
            border: 1px solid #bbbbbb;
            font-weight: bold;
        }
        QPushButton#sidebarButton:hover {
            background-color: #f5f5f5;
        }

        QLineEdit#searchBar {
            font-size: 14px;
            min-height: 28px;
            max-height: 28px;
            color: #000000;
            background-color: #ffffff;
        }
        QComboBox#monthSelector, QComboBox#yearSelector {
            font-size: 14px;
            min-height: 28px;
            max-height: 28px;
            color: #000000;
        }

        /* Texto más grande en tabla (celdas) */
        QTableView {
            font-size: 18px;
        }
    """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_default_light_style(app)

    from gui.home import PagosViewer
    from models.database import create_connection, initialize_db

    db = create_connection()
    initialize_db(db)

    window = PagosViewer()
    # Aumentar fuente del header
    header = window.table.horizontalHeader()
    font = header.font()
    font.setPointSize(14)
    header.setFont(font)

    window.show()
    sys.exit(app.exec())
