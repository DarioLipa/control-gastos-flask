import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = os.environ.get("DATABASE_PATH", "gastos.db")

CATEGORIAS_VALIDAS = [
    "Alimentación",
    "Transporte",
    "Vivienda",
    "Servicios básicos",
    "Salud",
    "Educación",
    "Compras",
    "Entretenimiento",
    "Tecnología",
    "Comunicación",
    "Vestimenta",
    "Viajes",
    "Deudas",
    "Imprevistos",
    "Otros"
]

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla de Usuarios con contraseña hasheada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de Gastos
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

    # Migración de esquema si falta columna detalle_otro
    cursor.execute("PRAGMA table_info(gastos)")
    columns = [col[1] for col in cursor.fetchall()]
    if "detalle_otro" not in columns:
        cursor.execute("ALTER TABLE gastos ADD COLUMN detalle_otro TEXT")

    # Migración de usuarios: comprobar si tiene columna password o password_hash
    cursor.execute("PRAGMA table_info(usuarios)")
    user_cols = [col[1] for col in cursor.fetchall()]
    if "password_hash" not in user_cols and "password" in user_cols:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN password_hash TEXT")
        # Hashear contraseñas existentes
        cursor.execute("SELECT id, password FROM usuarios")
        for u in cursor.fetchall():
            h = generate_password_hash(u[1])
            cursor.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (h, u[0]))

    # Usuario por defecto para práctica local: admin / 123
    admin_user = os.environ.get("ADMIN_USER", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD", "123")

    cursor.execute("SELECT id, password_hash FROM usuarios WHERE username = ?", (admin_user,))
    row = cursor.fetchone()
    if not row:
        hash_pass = generate_password_hash(admin_pass)
        cursor.execute("INSERT INTO usuarios (username, password_hash) VALUES (?, ?)", (admin_user, hash_pass))
    else:
        # Asegurarse de que el hash sea válido
        if not row[1] or not row[1].startswith(("pbkdf2:", "scrypt:")):
            hash_pass = generate_password_hash(admin_pass)
            cursor.execute("UPDATE usuarios SET password_hash = ? WHERE id = ?", (hash_pass, row[0]))

    # Sembrar gastos de muestra si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM gastos")
    count = cursor.fetchone()[0]
    if count == 0:
        today = datetime.now()
        sample_expenses = [
            ((today - timedelta(days=14)).strftime('%Y-%m-%d'), 'Supermercado Metro - Víveres quincenales', 285.50, 'Alimentación', None),
            ((today - timedelta(days=12)).strftime('%Y-%m-%d'), 'Recibo de Luz Enel y Agua Sedapal', 142.30, 'Servicios básicos', None),
            ((today - timedelta(days=10)).strftime('%Y-%m-%d'), 'Combustible Gasohol 95 Primax', 90.00, 'Transporte', None),
            ((today - timedelta(days=8)).strftime('%Y-%m-%d'), 'Cuota mensual Alquiler departamento', 650.00, 'Vivienda', None),
            ((today - timedelta(days=7)).strftime('%Y-%m-%d'), 'Farmacia InkaFarma - Vitaminas y analgésicos', 48.90, 'Salud', None),
            ((today - timedelta(days=5)).strftime('%Y-%m-%d'), 'Curso Online Especializado en Python & DevOps', 120.00, 'Educación', None),
            ((today - timedelta(days=4)).strftime('%Y-%m-%d'), 'Entradas Cineplanet y combo familiar', 65.00, 'Entretenimiento', None),
            ((today - timedelta(days=3)).strftime('%Y-%m-%d'), 'Pago plan celular Claro mensual', 55.90, 'Comunicación', None),
            ((today - timedelta(days=2)).strftime('%Y-%m-%d'), 'Renovación licencia Cloud Hosting', 78.50, 'Tecnología', None),
            ((today - timedelta(days=1)).strftime('%Y-%m-%d'), 'Zapatillas urbanas Ripley', 189.00, 'Vestimenta', None),
            (today.strftime('%Y-%m-%d'), 'Reparación de cerrajería de emergencia', 45.00, 'Otros', 'Servicio de cerrajero')
        ]
        cursor.executemany("""
            INSERT INTO gastos (fecha, descripcion, monto, categoria, detalle_otro)
            VALUES (?, ?, ?, ?, ?)
        """, sample_expenses)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Base de datos Dali_Gastos inicializada con éxito.")
