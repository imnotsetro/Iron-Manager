from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QTableView, QCompleter, QHeaderView
)
from PySide6.QtSql import QSqlQueryModel, QSqlQuery, QSqlDatabase
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import datetime

class StatusColorModel(QSqlQueryModel):
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.BackgroundRole and index.column() in (0, 1, 2):
            # Get month and year from the row
            month = self.index(index.row(), 1).data()
            year = self.index(index.row(), 2).data()
            if month != '-' and year != '-':
                try:
                    month = int(month)
                    year = int(year)
                    now = datetime.datetime.now()
                    current_month = now.month
                    current_year = now.year
                    # Calculate how many months ago was the last payment
                    months_ago = (current_year - year) * 12 + (current_month - month)
                    if months_ago == 0:
                        return None  # No color, paid this month
                    elif months_ago == 1:
                        return QColor('#FFA726')  # Orange, missed current month
                    elif months_ago > 1:
                        return QColor('#FF5252')  # Red, more than 2 months
                except Exception:
                    pass
            else:
                # No payment ever
                return QColor('#FF5252')
        return super().data(index, role)

class ClientStatusViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Estado de Pagos de Clientes")
        self.resize(662, 500)
        self.db = QSqlDatabase.database()
        self.setup_ui()
        self.update_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Buscar cliente:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar cliente...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                color: black;
            }
            QLineEdit::placeholder {
                color: black;
            }
        """)
        self.search_input.textChanged.connect(self.update_table)
        filter_layout.addWidget(self.search_input)
        layout.addLayout(filter_layout)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self.table)

        self.setup_autocomplete()

    def setup_autocomplete(self):
        if not self.db.isOpen():
            self.db.open()
        self.completer_model = QSqlQueryModel(self)
        self.completer_model.setQuery("SELECT name FROM clients", self.db)
        completer = QCompleter(self.completer_model, self)
        completer.setCompletionColumn(0)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        self.search_input.setCompleter(completer)

    def update_table(self):
        name = self.search_input.text()
        sql = """
              SELECT c.name                 AS Cliente,
                     COALESCE(p.month, '-') AS 'Último Mes',
                     COALESCE(p.year, '-')  AS 'Último Año'
              FROM clients c
                       LEFT JOIN payments p ON c.last_payment_id = p.id
              WHERE 1 = 1 \
              """
        params = []
        if name:
            sql += " AND c.name LIKE ?"
            params.append(f"%{name}%")

        model = StatusColorModel(self)
        q = QSqlQuery(self.db)
        q.prepare(sql)
        for i, val in enumerate(params):
            q.bindValue(i, val)
        q.exec()
        model.setQuery(q)
        self.table.setModel(model)

        # Table Header Configuration
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        col_count = model.columnCount()
        if col_count > 0:
            ancho = int(self.table.viewport().width() / col_count)
            for col in range(col_count):
                header.setSectionResizeMode(col, QHeaderView.Fixed)
                self.table.setColumnWidth(col, ancho)