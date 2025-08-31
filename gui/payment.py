from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QCompleter
)
from PySide6.QtSql import QSqlQuery, QSqlDatabase
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Signal, Qt
import datetime

class PaymentWindow(QWidget):
    payment_added = Signal()
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agregar Pago")
        self.db = QSqlDatabase.database()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.nombre_input = QLineEdit()

        # --- Autocomplete setup ---
        names = []
        query = QSqlQuery(self.db)
        query.exec("SELECT name FROM clients")
        while query.next():
            names.append(query.value(0))
        completer = QCompleter(names, self)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.nombre_input.setCompleter(completer)
        # --------------------------

        # Enter to register payment
        self.nombre_input.returnPressed.connect(self.register_payment)

        self.monto_input = QLineEdit()
        # limit 2 to float
        validator = QDoubleValidator(0.00, 1e9, 2, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.monto_input.setValidator(validator)
        # Enter to continue
        self.monto_input.returnPressed.connect(self.register_payment)

        self.month_combo = QComboBox()
        spanish_months = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
        ]
        for i, mes in enumerate(spanish_months, start=1):
            self.month_combo.addItem(mes, i)
        self.month_combo.setCurrentIndex(datetime.datetime.now().month - 1)

        self.year_combo = QComboBox()
        current_year = datetime.datetime.now().year
        for y in range(current_year - 5, current_year + 5):
            self.year_combo.addItem(str(y), y)
        self.year_combo.setCurrentText(str(current_year))

        self.descripcion_input = QLineEdit()

        form_layout.addRow("Nombre del cliente:", self.nombre_input)
        form_layout.addRow("Monto a pagar:", self.monto_input)
        form_layout.addRow("Mes a pagar:", self.month_combo)
        form_layout.addRow("Año a pagar:", self.year_combo)
        form_layout.addRow("Descripción:", self.descripcion_input)

        self.submit_btn = QPushButton("Registrar Pago")
        self.submit_btn.clicked.connect(self.register_payment)

        layout.addLayout(form_layout)
        layout.addWidget(self.submit_btn)

    def register_payment(self):
        nombre = self.nombre_input.text().strip()
        monto_text = self.monto_input.text().strip()
        mes = self.month_combo.currentData()
        anio = self.year_combo.currentData()

        if not nombre or not monto_text:
            QMessageBox.warning(self, "Error", "Debe completar todos los campos")
            return

        # Validar monto
        try:
            monto = float(monto_text)
        except ValueError:
            QMessageBox.warning(self, "Error", "Monto inválido. Ingrese un número válido.")
            return

        descripcion = self.descripcion_input.text().strip()

        query = QSqlQuery(self.db)
        query.prepare("SELECT id, last_payment_id FROM clients WHERE name = ?")
        query.addBindValue(nombre)
        query.exec()
        if query.next():
            cliente_id = query.value(0)
            ultimo_pago_id = query.value(1)
        else:
            insert_cli = QSqlQuery(self.db)
            insert_cli.prepare("INSERT INTO clients (name, last_payment_id) VALUES (?, NULL)")
            insert_cli.addBindValue(nombre)
            if not insert_cli.exec():
                QMessageBox.critical(self, "Error", "No se pudo crear el cliente")
                return
            cliente_id = insert_cli.lastInsertId()
            ultimo_pago_id = None

        # Verificar duplicado
        dup = QSqlQuery(self.db)
        dup.prepare("SELECT 1 FROM payments WHERE client_id = ? AND month = ? AND year = ?")
        dup.addBindValue(cliente_id)
        dup.addBindValue(mes)
        dup.addBindValue(anio)
        dup.exec()
        if dup.next():
            QMessageBox.warning(self, "Advertencia", "El cliente ya pagó ese mes.")
            return

        update_last_payment = False
        if ultimo_pago_id is not None:
            last = QSqlQuery(self.db)
            last.prepare("SELECT month, year FROM payments WHERE id = ?")
            last.addBindValue(ultimo_pago_id)
            last.exec()
            if last.next():
                ultimo_mes, ultimo_anio = last.value(0), last.value(1)
                # Compare (anio, mes) tuples
                if (anio, mes) > (ultimo_anio, ultimo_mes):
                    update_last_payment = True
                # Calculate next expected month/year
                if ultimo_mes == 12:
                    expected_month = 1
                    expected_year = ultimo_anio + 1
                else:
                    expected_month = ultimo_mes + 1
                    expected_year = ultimo_anio
                if (anio, mes) != (expected_year, expected_month):
                    reply = QMessageBox.question(
                        self, "Advertencia",
                        f"El siguiente pago esperado es para {expected_month}/{expected_year}.\n"
                        f"¿Desea registrar el pago de todas formas?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return
        else:
            update_last_payment = True  # No previous payment

        hoy = datetime.date.today().isoformat()
        ins = QSqlQuery(self.db)
        ins.prepare(
            "INSERT INTO payments (client_id, date, amount, month, year, description)"
            " VALUES (?, ?, ?, ?, ?, ?)"
        )
        ins.addBindValue(cliente_id)
        ins.addBindValue(hoy)
        ins.addBindValue(monto)
        ins.addBindValue(mes)
        ins.addBindValue(anio)
        ins.addBindValue(descripcion)
        if not ins.exec():
            QMessageBox.critical(self, "Error", "No se pudo registrar el pago")
            return
        new_pago_id = ins.lastInsertId()

        if update_last_payment:
            upd = QSqlQuery(self.db)
            upd.prepare(
                "UPDATE clients SET last_payment_id = ? WHERE id = ?"
            )
            upd.addBindValue(new_pago_id)
            upd.addBindValue(cliente_id)
            upd.exec()

        QMessageBox.information(self, "Éxito", "Pago registrado correctamente")
        self.nombre_input.clear()
        self.monto_input.clear()

        self.payment_added.emit()
        self.close()