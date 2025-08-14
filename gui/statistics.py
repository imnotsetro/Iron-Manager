# statistics.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableView
from PySide6.QtSql import QSqlQueryModel, QSqlQuery, QSqlDatabase
from PySide6.QtCore import Qt

class MonthlyStatsModel(QSqlQueryModel):
    def __init__(self, year, parent=None):
        super().__init__(parent)
        self.year = str(year) if year is not None else None
        self.refresh()

    def refresh(self):
        sql = """
        SELECT
            CAST(strftime('%m', date) AS INTEGER) AS Mes,
            SUM(amount) AS "Total Recaudado"
        FROM payments
        WHERE date IS NOT NULL
          AND strftime('%Y', date) = ?
        GROUP BY CAST(strftime('%m', date) AS INTEGER)
        ORDER BY Mes;
        """
        db = QSqlDatabase.database()
        q = QSqlQuery(db)
        prepared = q.prepare(sql)
        if not prepared:
            print("DEBUG: prepare failed (MonthlyStatsModel):", q.lastError().text())
        q.addBindValue(self.year)
        ok = q.exec()
        if not ok:
            print("DEBUG: exec failed (MonthlyStatsModel):", q.lastError().text())
        self.setQuery(q)

class StatisticsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Estadísticas de Recaudación")
        self.resize(400, 400)
        self.db = QSqlDatabase.database()
        self.model = None
        self.setup_ui()
        self.load_years()
        self.update_table()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh()

    def update_table(self):
        year = self.year_selector.currentText()
        if not year:
            self.table.setModel(None)
            return
        self.model = MonthlyStatsModel(year, self)
        self.table.setModel(self.model)
        self.model.setHeaderData(0, Qt.Horizontal, "Mes")
        self.model.setHeaderData(1, Qt.Horizontal, "Total Recaudado")

    def setup_ui(self):
        layout = QVBoxLayout(self)

        year_layout = QHBoxLayout()
        year_layout.addWidget(QLabel("Año:"))
        self.year_selector = QComboBox()
        self.year_selector.currentIndexChanged.connect(self.update_table)
        year_layout.addWidget(self.year_selector)
        layout.addLayout(year_layout)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

    def load_years(self):
        """
        Obtiene años existentes a partir de payment_date (strftime '%Y').
        """
        self.year_selector.clear()
        q = QSqlQuery(self.db)
        sql = "SELECT DISTINCT strftime('%Y', date) AS year FROM payments WHERE date IS NOT NULL ORDER BY year DESC;"
        if not q.exec(sql):
            print("DEBUG: load_years exec failed:", q.lastError().text())
            return
        years = []
        while q.next():
            y = q.value(0)
            if y:
                years.append(str(y))
        self.year_selector.addItems(years)

    def refresh(self):
        self.year_selector.clear()
        self.load_years()
        if self.year_selector.count() > 0:
            self.year_selector.setCurrentIndex(0)
        self.update_table()