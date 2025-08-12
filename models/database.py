from PySide6.QtSql import QSqlDatabase, QSqlQuery

def create_connection(db_filename="gym.db"):
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(db_filename)
    if not db.open():
        raise Exception("No se puede abrir la base de datos")
    return db

def initialize_db(db):
    query = QSqlQuery(db)
    query.exec_("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_completo TEXT NOT NULL UNIQUE,
            ultimo_pago_id INTEGER,
            FOREIGN KEY(ultimo_pago_id) REFERENCES pagos(id)
        );
    """)
    # Pagos
    query.exec_("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha_pago TEXT NOT NULL,
            monto REAL NOT NULL,
            mes_pagado INTEGER NOT NULL,
            anio_pagado INTEGER NOT NULL,
            descripcion TEXT,
            FOREIGN KEY(cliente_id) REFERENCES clientes(id),
            UNIQUE(cliente_id, mes_pagado, anio_pagado)
        );
    """)

