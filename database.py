import sqlite3
import os
from datetime import datetime, timedelta

DB_NAME = "gastos.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla de Usuarios
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Tabla de Gastos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            monto REAL NOT NULL,
            categoria TEXT DEFAULT 'General',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Usuario por defecto: admin / 123
    cursor.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (username, password) VALUES (?, ?)", ('admin', '123'))

    # Sembrar algunos datos de prueba representativos si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM gastos")
    count = cursor.fetchone()[0]
    if count == 0:
        today = datetime.now()
        sample_expenses = [
            ((today - timedelta(days=12)).strftime('%Y-%m-%d'), 'Servicio de Internet Fibra Óptica 300MB', 149.90, 'Servicios'),
            ((today - timedelta(days=10)).strftime('%Y-%m-%d'), 'Supermercado y Despensa Mensual', 385.50, 'Alimentación'),
            ((today - timedelta(days=8)).strftime('%Y-%m-%d'), 'Combustible Gasolina Premium', 120.00, 'Transporte'),
            ((today - timedelta(days=7)).strftime('%Y-%m-%d'), 'Suscripción Plataformas Cloud & Servidores', 85.00, 'Tecnología'),
            ((today - timedelta(days=5)).strftime('%Y-%m-%d'), 'Almuerzo Ejecutivo y Cafetería', 48.00, 'Alimentación'),
            ((today - timedelta(days=4)).strftime('%Y-%m-%d'), 'Mantenimiento Preventivo Vehicular', 220.00, 'Transporte'),
            ((today - timedelta(days=3)).strftime('%Y-%m-%d'), 'Farmacia y Medicamentos', 65.20, 'Salud'),
            ((today - timedelta(days=2)).strftime('%Y-%m-%d'), 'Cine y Entretenimiento Familiar', 75.00, 'Ocio'),
            ((today - timedelta(days=1)).strftime('%Y-%m-%d'), 'Luz y Energía Eléctrica', 115.80, 'Servicios'),
            (today.strftime('%Y-%m-%d'), 'Compra de Accesorios de Oficina', 95.00, 'Equipamiento')
        ]
        cursor.executemany("""
            INSERT INTO gastos (fecha, descripcion, monto, categoria)
            VALUES (?, ?, ?, ?)
        """, sample_expenses)

    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Base de datos inicializada correctamente.")
