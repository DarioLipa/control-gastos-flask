import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = os.environ.get("DATABASE_PATH", "gastos.db")

# Catálogo centralizado oficial de categorías
CATEGORIAS_VALIDAS = [
    "Alimentación",
    "Movilidad",
    "Alquiler",
    "Vestimenta",
    "Universidad",
    "Otros"
]

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(reset_demo_data=False):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Tabla de Usuarios con contraseña protegida por hash
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Tabla de Gastos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            categoria TEXT NOT NULL DEFAULT 'Alimentación',
            detalle_otro TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migración de columnas si fueran necesarias
    cursor.execute("PRAGMA table_info(gastos)")
    columns = [col[1] for col in cursor.fetchall()]
    if "detalle_otro" not in columns:
        cursor.execute("ALTER TABLE gastos ADD COLUMN detalle_otro TEXT")

    # Usuario por defecto para práctica local: admin / 123
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "123")

    cursor.execute("SELECT id, password_hash FROM usuarios WHERE username = ?", (admin_user,))
    row = cursor.fetchone()
    if not row:
        hash_pass = generate_password_hash(admin_pass)
        cursor.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)", (admin_user, hash_pass))
    else:
        if not row[1] or not row[1].startswith(("pbkdf2:", "scrypt:")):
            hash_pass = generate_password_hash(admin_pass)
            cursor.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (hash_pass, row[0]))

    if reset_demo_data:
        cursor.execute("DELETE FROM gastos")

    # Sembrar EXACTAMENTE los 5 registros requeridos si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM gastos")
    count = cursor.fetchone()[0]
    if count == 0:
        cinco_gastos_iniciales = [
            ('2026-11-09', 'Alimentación', 35.50, 'Alimentación', None),
            ('2026-11-10', 'Movilidad', 12.00, 'Movilidad', None),
            ('2026-11-11', 'Alquiler', 480.00, 'Alquiler', None),
            ('2026-11-12', 'Ropa', 95.00, 'Vestimenta', None),
            ('2026-11-13', 'Universidad', 260.00, 'Universidad', None)
        ]
        cursor.executemany("""
            INSERT INTO gastos (fecha, descripcion, monto, categoria, detalle_otro)
            VALUES (?, ?, ?, ?, ?)
        """, cinco_gastos_iniciales)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db(reset_demo_data=True)
    print("Base de datos Dali_Gastos inicializada con exactamente 5 registros.")
