import pytest
import os
import sqlite3
from app import app
from database import init_db, get_db_connection

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    init_db()

    with app.test_client() as client:
        yield client

def login_client(client, username="admin", password="123"):
    return client.post('/login', data={
        'username': username,
        'password': password
    }, follow_redirects=True)

def test_unauthenticated_redirect(client):
    """Las rutas protegidas deben redirigir a /login si no hay sesión."""
    res = client.get('/dashboard')
    assert res.status_code == 302
    assert '/login' in res.location

    res = client.get('/gastos')
    assert res.status_code == 302
    assert '/login' in res.location

    res = client.get('/reportes')
    assert res.status_code == 302
    assert '/login' in res.location

def test_login_successful(client):
    """Inicio de sesión con credenciales válidas."""
    res = login_client(client, "admin", "123")
    assert res.status_code == 200
    assert b"Dali" in res.data
    assert b"Panel Financiero" in res.data

def test_login_failed(client):
    """Rechazo ante credenciales incorrectas."""
    res = login_client(client, "admin", "clave_erronea")
    assert res.status_code == 200
    assert b"Credenciales incorrectas" in res.data

def test_dashboard_view(client):
    """Carga correcta del dashboard analítico."""
    login_client(client)
    res = client.get('/dashboard')
    assert res.status_code == 200
    assert b"Gasto Total Acumulado" in res.data
    assert b"S/" in res.data

def test_gastos_crud(client):
    """Creación, edición y eliminación de gastos."""
    login_client(client)

    # 1. Crear nuevo gasto
    res = client.post('/gastos/crear', data={
        'fecha': '2026-11-13',
        'descripcion': 'Prueba Automatizada Pytest',
        'monto': '125.50',
        'categoria': 'Alimentación'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Prueba Automatizada Pytest" in res.data
    assert b"125.50" in res.data

    # Obtener el ID del gasto creado
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM gastos WHERE descripcion = 'Prueba Automatizada Pytest'").fetchone()
    conn.close()
    assert row is not None
    gasto_id = row['id']

    # 2. Editar gasto
    res_edit = client.post(f'/gastos/{gasto_id}/editar', data={
        'fecha': '2026-11-13',
        'descripcion': 'Prueba Editada Exitosa',
        'monto': '150.00',
        'categoria': 'Tecnología'
    }, follow_redirects=True)
    assert res_edit.status_code == 200
    assert b"Prueba Editada Exitosa" in res_edit.data

    # 3. Eliminar gasto
    res_del = client.post(f'/gastos/{gasto_id}/eliminar', follow_redirects=True)
    assert res_del.status_code == 200
    assert b"Gasto eliminado satisfactoriamente" in res_del.data

def test_categoria_otros_con_detalle(client):
    """La categoría Otros debe almacenar correctamente el detalle opcional."""
    login_client(client)
    res = client.post('/gastos/crear', data={
        'fecha': '2026-11-13',
        'descripcion': 'Gasto con categoría Otros',
        'monto': '45.00',
        'categoria': 'Otros',
        'detalle_otro': 'Reparación de cerrajería'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Reparaci\xc3\xb3n de cerrajer\xc3\xada" in res.data

def test_validacion_monto_invalido(client):
    """Monto negativo o cero debe ser rechazado."""
    login_client(client)
    res = client.post('/gastos/crear', data={
        'fecha': '2026-11-13',
        'descripcion': 'Gasto negativo',
        'monto': '-50.00',
        'categoria': 'Alimentación'
    }, follow_redirects=True)
    assert b"El monto debe ser un valor positivo" in res.data

def test_reportes_filtros_y_csv(client):
    """Filtrado de reportes y exportación en formato CSV."""
    login_client(client)

    # Vista de reportes
    res = client.get('/reportes?categoria=Alimentación')
    assert res.status_code == 200
    assert b"Reportes" in res.data
    assert b"Detalle de Gastos del Reporte" in res.data

    # Descarga CSV
    res_csv = client.get('/reportes/exportar/csv?categoria=Alimentación')
    assert res_csv.status_code == 200
    assert res_csv.mimetype == 'text/csv'
    assert b"ID,Fecha,Descripcion,Categoria" in res_csv.data

def test_error_404(client):
    """Ruta inexistente debe retornar 404."""
    res = client.get('/ruta-inexistente-12345')
    assert res.status_code == 404
    assert b"P\xc3\xa1gina no encontrada" in res.data
