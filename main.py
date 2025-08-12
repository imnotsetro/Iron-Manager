import sys
from PySide6.QtWidgets import QApplication
from gui.home import PagosViewer
from models.database import create_connection, initialize_db

if __name__ == '__main__':
    app = QApplication(sys.argv)

    db = create_connection()
    initialize_db(db)

    window = PagosViewer()
    window.show()

    sys.exit(app.exec())