from PySide6.QtSql import QSqlDatabase, QSqlQuery

def create_connection(db_filename="data.db"):
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(db_filename)
    if not db.open():
        raise Exception("No se puede abrir la base de datos")
    return db

def initialize_db(db):
    query = QSqlQuery(db)
    query.exec_("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            last_payment_id INTEGER,
            FOREIGN KEY(last_payment_id) REFERENCES payment(id)
        );
    """)
    # Pagos
    query.exec_("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            description TEXT,
            FOREIGN KEY(client_id) REFERENCES clients(id),
            UNIQUE(client_id, month, year)
        );
    """)

