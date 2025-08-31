from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QMessageBox
)
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Signal, Qt
import datetime

class PaymentEditWindow(QWidget):
    payment_added = Signal()
    def __init__(self, payment_id):
        super().__init__()
        self.setWindowTitle("Editar Pago")
        self.db = QSqlDatabase.database()
        self.payment_id = payment_id
        self.setup_ui()
        self.load_payment()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setReadOnly(True)  # No editing client name

        self.amount_input = QLineEdit()
        validator = QDoubleValidator(0.00, 1e9, 2, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.amount_input.setValidator(validator)

        self.month_combo = QComboBox()
        spanish_months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        for i, month in enumerate(spanish_months, start=1):
            self.month_combo.addItem(month, i)

        self.year_combo = QComboBox()
        current_year = datetime.datetime.now().year
        for y in range(current_year - 5, current_year + 5):
            self.year_combo.addItem(str(y), y)

        self.description_input = QLineEdit()

        form_layout.addRow("Nombre del cliente:", self.name_input)
        form_layout.addRow("Monto a pagar:", self.amount_input)
        form_layout.addRow("Mes a pagar:", self.month_combo)
        form_layout.addRow("Año a pagar:", self.year_combo)
        form_layout.addRow("Descripción:", self.description_input)

        self.submit_btn = QPushButton("Guardar Cambios")
        self.submit_btn.clicked.connect(self.save_changes)

        layout.addLayout(form_layout)
        layout.addWidget(self.submit_btn)

    def load_payment(self):
        q = QSqlQuery(self.db)
        q.prepare("""
                  SELECT c.name, p.amount, p.month, p.year, p.client_id, p.description
                  FROM payments p
                           JOIN clients c ON p.client_id = c.id
                  WHERE p.id = ?
          """)
        q.addBindValue(self.payment_id)
        q.exec()
        if q.next():
            self.name_input.setText(q.value(0))
            self.amount_input.setText(str(q.value(1)))
            month = q.value(2)
            year = q.value(3)
            self.client_id = q.value(4)
            self.month_combo.setCurrentIndex(month - 1)
            idx = self.year_combo.findData(year)
            self.description_input.setText(q.value(5) or "")
            if idx >= 0:
                self.year_combo.setCurrentIndex(idx)
        else:
            QMessageBox.critical(self, "Error", "No se pudo cargar el pago.")
            self.close()

    def save_changes(self):
        amount_text = self.amount_input.text().strip()
        month = self.month_combo.currentData()
        year = self.year_combo.currentData()

        if not amount_text:
            QMessageBox.warning(self, "Error", "Debe completar todos los campos")
            return

        try:
            amount = float(amount_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Monto inválido. Ingrese un número válido.")
            return

        # Check for duplicate payment for same month/year (excluding this payment)
        dup = QSqlQuery(self.db)
        dup.prepare("""
            SELECT 1 FROM payments 
            WHERE client_id = ? AND month = ? AND year = ? AND id != ?
        """)
        dup.addBindValue(self.client_id)
        dup.addBindValue(month)
        dup.addBindValue(year)
        dup.addBindValue(self.payment_id)
        dup.exec()
        if dup.next():
            QMessageBox.warning(self, "Advertencia", "El cliente ya pagó ese month.")
            return

        upd = QSqlQuery(self.db)
        description= self.description_input.text().strip()
        upd.prepare("""
                    UPDATE payments
                    SET amount       = ?,
                        month  = ?,
                        year = ?,
                        description = ?
                    WHERE id = ?
                    """)
        upd.addBindValue(amount)
        upd.addBindValue(month)
        upd.addBindValue(year)
        upd.addBindValue(description)
        upd.addBindValue(self.payment_id)
        if not upd.exec():
            QMessageBox.critical(self, "Error", "No se pudo actualizar el pago")
            return

        # Update last_payment_id if this is the latest payment
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT id FROM payments 
            WHERE client_id = ? 
            ORDER BY date DESC, id DESC LIMIT 1
        """)
        q.addBindValue(self.client_id)
        q.exec()
        if q.next() and q.value(0) == self.payment_id:
            upd2 = QSqlQuery(self.db)
            upd2.prepare("UPDATE clients SET last_payment_id = ? WHERE id = ?")
            upd2.addBindValue(self.payment_id)
            upd2.addBindValue(self.client_id)
            upd2.exec()

        QMessageBox.information(self, "Éxito", "Pago actualizado correctamente")
        self.payment_added.emit()
        self.close()