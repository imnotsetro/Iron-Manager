from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QTableView
from PySide6.QtSql import QSqlQueryModel, QSqlQuery, QSqlDatabase
from PySide6.QtCore import Qt

class MonthlyStatsModel(QSqlQueryModel):
    def __init__(self, year, parent=None):
        super().__init__(parent)
        self.year = year
        self.refresh()

    def refresh(self):
        sql = """
        SELECT
            month AS Mes,
            SUM(amount) AS 'Total Recaudado'
        FROM payments
        WHERE year = ?
        GROUP BY month
        ORDER BY month
        """
        db = QSqlDatabase.database()
        q = QSqlQuery(db)
        q.prepare(sql)
        q.addBindValue(self.year)
        q.exec()
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
        sql = "SELECT DISTINCT year FROM payments ORDER BY year DESC"
        q = QSqlQuery(self.db)
        q.exec(sql)
        years = []
        while q.next():
            year = q.value(0)
            if year:
                years.append(str(year))
        self.year_selector.addItems(years)

    def refresh(self):
        self.year_selector.clear()
        self.load_years()
        if self.year_selector.count() > 0:
            self.year_selector.setCurrentIndex(0)
        self.update_table()