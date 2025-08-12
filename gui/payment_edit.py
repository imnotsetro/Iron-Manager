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

        self.nombre_input = QLineEdit()
        self.nombre_input.setReadOnly(True)  # No editing client name

        self.monto_input = QLineEdit()
        validator = QDoubleValidator(0.00, 1e9, 2, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.monto_input.setValidator(validator)

        self.month_combo = QComboBox()
        spanish_months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        for i, mes in enumerate(spanish_months, start=1):
            self.month_combo.addItem(mes, i)

        self.year_combo = QComboBox()
        current_year = datetime.datetime.now().year
        for y in range(current_year - 5, current_year + 5):
            self.year_combo.addItem(str(y), y)

        self.descripcion_input = QLineEdit()

        form_layout.addRow("Nombre del cliente:", self.nombre_input)
        form_layout.addRow("Monto a pagar:", self.monto_input)
        form_layout.addRow("Mes a pagar:", self.month_combo)
        form_layout.addRow("Año a pagar:", self.year_combo)
        form_layout.addRow("Descripción:", self.descripcion_input)

        self.submit_btn = QPushButton("Guardar Cambios")
        self.submit_btn.clicked.connect(self.guardar_cambios)

        layout.addLayout(form_layout)
        layout.addWidget(self.submit_btn)

    def load_payment(self):
        q = QSqlQuery(self.db)
        q.prepare("""
                  SELECT c.nombre_completo, p.monto, p.mes_pagado, p.anio_pagado, p.cliente_id, p.descripcion
                  FROM pagos p
                           JOIN clientes c ON p.cliente_id = c.id
                  WHERE p.id = ?
          """)
        q.addBindValue(self.payment_id)
        q.exec()
        if q.next():
            self.nombre_input.setText(q.value(0))
            self.monto_input.setText(str(q.value(1)))
            mes = q.value(2)
            anio = q.value(3)
            self.cliente_id = q.value(4)
            self.month_combo.setCurrentIndex(mes - 1)
            idx = self.year_combo.findData(anio)
            self.descripcion_input.setText(q.value(5) or "")
            if idx >= 0:
                self.year_combo.setCurrentIndex(idx)
        else:
            QMessageBox.critical(self, "Error", "No se pudo cargar el pago.")
            self.close()

    def guardar_cambios(self):
        monto_text = self.monto_input.text().strip()
        mes = self.month_combo.currentData()
        anio = self.year_combo.currentData()

        if not monto_text:
            QMessageBox.warning(self, "Error", "Debe completar todos los campos")
            return

        try:
            monto = float(monto_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Monto inválido. Ingrese un número válido.")
            return

        # Check for duplicate payment for same month/year (excluding this payment)
        dup = QSqlQuery(self.db)
        dup.prepare("""
            SELECT 1 FROM pagos 
            WHERE cliente_id = ? AND mes_pagado = ? AND anio_pagado = ? AND id != ?
        """)
        dup.addBindValue(self.cliente_id)
        dup.addBindValue(mes)
        dup.addBindValue(anio)
        dup.addBindValue(self.payment_id)
        dup.exec()
        if dup.next():
            QMessageBox.warning(self, "Advertencia", "El cliente ya pagó ese mes.")
            return

        upd = QSqlQuery(self.db)
        descripcion = self.descripcion_input.text().strip()
        upd.prepare("""
                    UPDATE pagos
                    SET monto       = ?,
                        mes_pagado  = ?,
                        anio_pagado = ?,
                        descripcion = ?
                    WHERE id = ?
                    """)
        upd.addBindValue(monto)
        upd.addBindValue(mes)
        upd.addBindValue(anio)
        upd.addBindValue(descripcion)
        upd.addBindValue(self.payment_id)
        if not upd.exec():
            QMessageBox.critical(self, "Error", "No se pudo actualizar el pago")
            return

        # Update ultimo_pago_id if this is the latest payment
        q = QSqlQuery(self.db)
        q.prepare("""
            SELECT id FROM pagos 
            WHERE cliente_id = ? 
            ORDER BY fecha_pago DESC, id DESC LIMIT 1
        """)
        q.addBindValue(self.cliente_id)
        q.exec()
        if q.next() and q.value(0) == self.payment_id:
            upd2 = QSqlQuery(self.db)
            upd2.prepare("UPDATE clientes SET ultimo_pago_id = ? WHERE id = ?")
            upd2.addBindValue(self.payment_id)
            upd2.addBindValue(self.cliente_id)
            upd2.exec()

        QMessageBox.information(self, "Éxito", "Pago actualizado correctamente")
        self.payment_added.emit()
        self.close()