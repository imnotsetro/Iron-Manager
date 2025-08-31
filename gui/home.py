from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableView, QLabel, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QTabWidget, QHeaderView, QCompleter
)
from PySide6.QtSql import QSqlQueryModel, QSqlQuery, QSqlDatabase
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QStackedLayout
import datetime
from gui.payment import PaymentWindow
from gui.statistics import StatisticsWindow
from gui.status_clients import ClientStatusViewer
from gui.payment_edit import PaymentEditWindow

class PagosViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Iron Manager")
        self.resize(1280, 720)
        self.db = QSqlDatabase.database()
        self.setup_ui()
        self.load_filters()
        self.update_table()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()

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

        self.month_combo = QComboBox()
        spanish_months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        for i, mes in enumerate(spanish_months, start=1):
            self.month_combo.addItem(mes, i)
        self.month_combo.setCurrentIndex(datetime.datetime.now().month - 1)
        self.month_combo.currentIndexChanged.connect(self.update_table)

        self.year_combo = QComboBox()
        self.year_combo.currentIndexChanged.connect(self.update_table)

        self.add_payment_button = QPushButton("Agregar Pago")
        self.add_payment_button.clicked.connect(self.open_payment_window)
        self.add_payment_button.setStyleSheet("background-color: #4CAF50; color: white;")

        self.edit_payment_button = QPushButton("Editar Pago")
        self.edit_payment_button.clicked.connect(self.edit_payment)
        self.edit_payment_button.setStyleSheet("background-color: #FFD600; color: black;")

        self.delete_payment_button = QPushButton("Borrar Pago")
        self.delete_payment_button.clicked.connect(self.borrar_pago)
        self.delete_payment_button.setStyleSheet("background-color: #F44336; color: white;")

        self.status_btn = QPushButton("Lista de Clientes")
        self.status_btn.clicked.connect(self.open_status)
        filter_layout.addWidget(self.status_btn)

        self.stats_button = QPushButton("Estadisticas")
        self.stats_button.clicked.connect(self.open_statistics)
        filter_layout.addWidget(self.stats_button)

        self.statistics_window = None

        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Mes"))
        filter_layout.addWidget(self.month_combo)
        filter_layout.addWidget(QLabel("Año"))
        filter_layout.addWidget(self.year_combo)
        filter_layout.addWidget(self.add_payment_button)
        filter_layout.addWidget(self.edit_payment_button)
        filter_layout.addWidget(self.delete_payment_button)

        self.table = QTableView()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)

        self.no_data_label = QLabel("No existen pagos registrados en este mes")
        self.no_data_label.setAlignment(Qt.AlignCenter)
        self.no_data_label.setStyleSheet("font-size: 18px; color: gray;")
        self.no_data_label.setVisible(False)

        # Use QStackedLayout to overlay label and table
        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self.table)
        self.stacked_layout.addWidget(self.no_data_label)

        layout.addLayout(filter_layout)
        layout.addLayout(self.stacked_layout)

        self.setup_autocomplete()

    def setup_autocomplete(self):
        # Asegura DB abierta
        if not self.db.isOpen():
            self.db.open()

        # Modelo de consulta para completado
        self.completer_model = QSqlQueryModel(self)
        self.completer_model.setQuery("SELECT name FROM clients", self.db)

        # Completer
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCompletionColumn(0)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setMaxVisibleItems(10)

        self.search_input.setCompleter(self.completer)

    def refresh_autocomplete(self):
        try:
            if not hasattr(self, "completer_model") or self.completer_model is None:
                # si no existía, configura completo
                self.setup_autocomplete()
                return

            # Re-ejecutar la consulta
            self.completer_model.setQuery("SELECT name FROM clients", self.db)

            # Forzar actualización del completer (en algunas plataformas ayuda)
            if hasattr(self, "completer") and self.completer is not None:
                self.completer.setModel(self.completer_model)
        except Exception as e:
            print("DEBUG: refresh_autocomplete failed:", e)

    def open_statistics(self):
        if self.statistics_window is None:
            self.statistics_window = StatisticsWindow()
        self.statistics_window.show()
        self.statistics_window.raise_()
        self.statistics_window.activateWindow()

    def open_payment_window(self):
        self.payment_window = PaymentWindow()
        self.payment_window.payment_added.connect(self.on_payment_added)
        self.payment_window.show()

    def open_status(self):
        self.status_window = ClientStatusViewer()
        self.status_window.show()

    def on_payment_added(self):
        # refrescar filtros y tabla
        self.load_filters()
        self.update_table()

        # refrescar autocompletar para incluir clientes recién creados
        self.refresh_autocomplete()

    def edit_payment(self):
        index = self.table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Seleccionar pago", "Seleccione un pago para editar.")
            return
        payment_id = self.get_selected_payment_id()
        if payment_id is None:
            QMessageBox.warning(self, "Error", "No se pudo obtener el ID del pago.")
            return
        self.payment_window = PaymentEditWindow(payment_id=payment_id)
        self.payment_window.payment_added.connect(self.update_table)
        self.payment_window.show()

    def borrar_pago(self):
        index = self.table.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Seleccionar pago", "Seleccione un pago para borrar.")
            return
        payment_id = self.get_selected_payment_id()
        if payment_id is None:
            QMessageBox.warning(self, "Error", "No se pudo obtener el ID del pago.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmar borrado",
            "¿Está seguro de que desea borrar este pago?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # Get client_id before deleting
        q = QSqlQuery(self.db)
        q.prepare("SELECT client_id FROM payments WHERE id = ?")
        q.addBindValue(payment_id)
        if not q.exec() or not q.next():
            QMessageBox.warning(self, "Error", "No se encontró el pago.")
            return
        client_id = q.value(0)

        # Delete the payment
        q2 = QSqlQuery(self.db)
        q2.prepare("DELETE FROM payments WHERE id = ?")
        q2.addBindValue(payment_id)
        if not q2.exec():
            QMessageBox.critical(self, "Error", "No se pudo borrar el pago.")
            return

        # Find the latest payment for the client
        q3 = QSqlQuery(self.db)
        q3.prepare("SELECT id FROM payments WHERE client_id = ? ORDER BY year DESC, month DESC, id DESC LIMIT 1")
        q3.addBindValue(client_id)
        if not q3.exec():
            QMessageBox.warning(self, "Error", "No se pudo buscar el último pago.")
            return
        if q3.next():
            ultimo_pago_id = q3.value(0)
            # Update clientes.ultimo_pago_id
            q4 = QSqlQuery(self.db)
            q4.prepare("UPDATE clients SET last_payment_id = ? WHERE id = ?")
            q4.addBindValue(ultimo_pago_id)
            q4.addBindValue(client_id)
            if not q4.exec():
                QMessageBox.warning(self, "Error", "No se pudo actualizar el último pago del cliente.")
        else:
            # No more payments, delete client
            q5 = QSqlQuery(self.db)
            q5.prepare("DELETE FROM clients WHERE id = ?")
            q5.addBindValue(client_id)
            if not q5.exec():
                QMessageBox.warning(self, "Error", "No se pudo borrar el cliente.")

        self.update_table()

    def get_selected_payment_id(self):
        index = self.table.currentIndex()
        if not index.isValid():
            return None
        row = index.row()
        model = self.table.model()
        # Assuming the model has a hidden column with payment id as the first column
        # If not, you need to adjust the query in update_table to include p.id
        return model.data(model.index(row, 0))

    def load_filters(self):
        self.year_combo.blockSignals(True)
        self.year_combo.clear()
        current_year = datetime.datetime.now().year
        query = QSqlQueryModel()
        query.setQuery("SELECT DISTINCT year FROM payments ORDER BY year DESC", self.db)
        default_index = 0
        for i in range(query.rowCount()):
            year = query.record(i).value("year")
            self.year_combo.addItem(str(year), year)
            if year == current_year:
                default_index = i
        self.year_combo.setCurrentIndex(default_index)
        self.year_combo.blockSignals(False)

    def update_table(self):
        name = self.search_input.text()
        month = self.month_combo.currentData()
        year = self.year_combo.currentData()

        sql = """
              SELECT p.id              AS PagoID,
                     c.name AS Cliente,
                     p.amount           AS Monto,
                     p.date      AS "Fecha de Pago",
                     p.description     AS Descripcion
              FROM payments p
                       JOIN clients c ON p.client_id = c.id
              WHERE 1 = 1 \
              """
        params = []

        if name:
            sql += " AND c.name LIKE ?"
            params.append(f"%{name}%")
        if month:
            sql += " AND p.month = ?"
            params.append(month)
        if year:
            sql += " AND p.year = ?"
            params.append(year)

        sql += " ORDER BY c.name ASC"

        query = QSqlQueryModel(self)
        q = QSqlQuery(self.db)
        q.prepare(sql)
        for i, val in enumerate(params):
            q.bindValue(i, val)
        q.exec()
        query.setQuery(q)
        self.table.setModel(query)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.table.hideColumn(0)  # Hide PagoID column

        if query.rowCount() == 0:
            self.stacked_layout.setCurrentWidget(self.no_data_label)
        else:
            self.stacked_layout.setCurrentWidget(self.table)

        self.table.hideColumn(0)  # Hide PagoID column