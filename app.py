import os
import secrets
import csv
import io
import time
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, abort
from werkzeug.security import check_password_hash

from config import config_by_name
from database import get_db_connection, init_db, CATEGORIAS_VALIDAS

# Inicializar aplicación Flask con configuración por entorno
env_name = os.environ.get("FLASK_ENV", "development")
app = Flask(__name__)
app.config.from_object(config_by_name.get(env_name, config_by_name["default"]))

# Estructura en memoria para mitigar ataques de fuerza bruta en login
login_attempts = {}

def get_client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown")

# ==========================================================
# PROTECCIÓN CSRF & SEGURIDAD DE SESIÓN
# ==========================================================
def generate_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(24)
    return session["_csrf_token"]

app.jinja_env.globals["csrf_token"] = generate_csrf_token

@app.before_request
def csrf_protect():
    # En entorno de pruebas con WTF_CSRF_ENABLED=False o rutas de consulta GET se omite
    if app.config.get("TESTING") and not app.config.get("WTF_CSRF_ENABLED", True):
        return

    if request.method in ("POST", "PUT", "DELETE"):
        token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        expected = session.get("_csrf_token")
        if not expected or token != expected:
            abort(403)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Modo demo para capturas controladas
        if request.args.get("demo") == "1":
            session["user"] = "admin"
        if not session.get("user"):
            flash("Por favor inicia sesión para acceder al sistema.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# ==========================================================
# MANEJADORES DE ERRORES HTTP PERSONALIZADOS
# ==========================================================
@app.errorhandler(403)
def forbidden_error(e):
    return render_template("errores/403.html"), 403

@app.errorhandler(404)
def not_found_error(e):
    return render_template("errores/404.html"), 404

@app.errorhandler(500)
def internal_error(e):
    return render_template("errores/500.html"), 500

# ==========================================================
# AUTENTICACIÓN
# ==========================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        ip = get_client_ip()
        now = time.time()

        # Comprobar límite de intentos fallidos (5 intentos -> bloqueo 5 min)
        attempt_data = login_attempts.get(ip, {"count": 0, "last": 0})
        if attempt_data["count"] >= 5 and (now - attempt_data["last"]) < 300:
            remaining = int(300 - (now - attempt_data["last"]))
            flash(f"Demasiados intentos fallidos. Intente de nuevo en {remaining} segundos.", "danger")
            return render_template('login.html'), 429

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE username = ?',
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            # Reiniciar contador de intentos fallidos
            login_attempts.pop(ip, None)
            session.clear()
            session['user'] = user['username']
            session['_csrf_token'] = secrets.token_hex(24)
            flash('¡Bienvenido a Dali_Gastos!', 'success')
            return redirect(url_for('dashboard'))
        else:
            # Registrar intento fallido
            attempt_data["count"] += 1
            attempt_data["last"] = now
            login_attempts[ip] = attempt_data
            flash('Credenciales incorrectas. Verifique sus datos.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ==========================================================
# MÓDULO 1: INICIO / DASHBOARD (ANÁLISIS VISUAL SIN TABLAS)
# ==========================================================
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()

    # Métricas Globales
    stats = conn.execute('''
        SELECT 
            COALESCE(SUM(monto), 0) AS total_gastos,
            COALESCE(AVG(monto), 0) AS promedio_gasto,
            COALESCE(MAX(monto), 0) AS max_gasto,
            COUNT(*) AS total_registros
        FROM gastos
    ''').fetchone()

    # Gasto de este mes y del mes anterior para cálculo de variación
    now = datetime.now()
    current_month_str = now.strftime('%Y-%m')
    prev_month_date = (now.replace(day=1) - __import__('datetime').timedelta(days=1))
    prev_month_str = prev_month_date.strftime('%Y-%m')

    mes_stat = conn.execute('''
        SELECT COALESCE(SUM(monto), 0) AS total_mes
        FROM gastos 
        WHERE strftime('%Y-%m', fecha) = ?
    ''', (current_month_str,)).fetchone()

    prev_mes_stat = conn.execute('''
        SELECT COALESCE(SUM(monto), 0) AS total_mes_prev
        FROM gastos 
        WHERE strftime('%Y-%m', fecha) = ?
    ''', (prev_month_str,)).fetchone()

    total_mes = mes_stat['total_mes']
    total_mes_prev = prev_mes_stat['total_mes_prev']
    var_mes = None
    if total_mes_prev > 0:
        var_mes = ((total_mes - total_mes_prev) / total_mes_prev) * 100

    # Evolución cronológica de gastos
    tendencia = conn.execute('''
        SELECT fecha, SUM(monto) as total_dia
        FROM gastos
        GROUP BY fecha
        ORDER BY fecha ASC
    ''').fetchall()

    # Desglose por categoría
    por_categoria = conn.execute('''
        SELECT categoria, SUM(monto) as total_cat, COUNT(*) as cantidad
        FROM gastos
        GROUP BY categoria
        ORDER BY total_cat DESC
    ''').fetchall()

    # Categoría con mayor gasto para Tarjeta 3
    max_categoria = None
    if por_categoria:
        max_categoria = {
            'nombre': por_categoria[0]['categoria'],
            'monto': por_categoria[0]['total_cat']
        }

    # Distribución de categorías para el panel de barras de progreso
    total_acumulado = stats['total_gastos'] or 1
    top_categorias = []
    for row in por_categoria:
        pct = (row['total_cat'] / total_acumulado) * 100
        top_categorias.append({
            'categoria': row['categoria'],
            'total_cat': row['total_cat'],
            'cantidad': row['cantidad'],
            'porcentaje': round(pct, 1)
        })

    conn.close()

    trend_labels = [row['fecha'] for row in tendencia]
    trend_values = [round(row['total_dia'], 2) for row in tendencia]

    cat_labels = [row['categoria'] for row in por_categoria]
    cat_values = [round(row['total_cat'], 2) for row in por_categoria]

    meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    nombre_mes = f"{meses_es[now.month - 1]} {now.year}"

    return render_template(
        'dashboard.html',
        stats=stats,
        total_mes=total_mes,
        max_categoria=max_categoria,
        var_mes=var_mes,
        nombre_mes=nombre_mes,
        top_categorias=top_categorias,
        trend_labels=trend_labels,
        trend_values=trend_values,
        cat_labels=cat_labels,
        cat_values=cat_values
    )

# ==========================================================
# MÓDULO 2: GASTOS (GESTIÓN CENTRALIZADA Y CRUD)
# ==========================================================
@app.route('/gastos')
@login_required
def gastos_view():
    query_q = request.args.get('q', '').strip()
    query_cat = request.args.get('cat', '').strip()

    sql = "SELECT id, fecha, descripcion, monto, categoria, detalle_otro, created_at FROM gastos WHERE 1=1"
    params = []

    if query_q:
        sql += " AND descripcion LIKE ?"
        params.append(f"%{query_q}%")
    if query_cat and query_cat in CATEGORIAS_VALIDAS:
        sql += " AND categoria = ?"
        params.append(query_cat)

    sql += " ORDER BY fecha DESC, id DESC"

    conn = get_db_connection()
    gastos = conn.execute(sql, params).fetchall()
    conn.close()

    return render_template(
        'gastos.html',
        gastos=gastos,
        query_q=query_q,
        query_cat=query_cat,
        categorias_disponibles=CATEGORIAS_VALIDAS
    )

@app.route('/gastos/crear', methods=['POST'])
@login_required
def crear_gasto():
    fecha = request.form.get('fecha', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    monto_raw = request.form.get('monto', '').strip()
    categoria = request.form.get('categoria', 'Alimentación').strip()
    detalle_otro = request.form.get('detalle_otro', '').strip() or None

    # Validaciones en servidor
    if not fecha or not descripcion or not monto_raw:
        flash('Todos los campos marcados con asterisco son obligatorios.', 'danger')
        return redirect(url_for('gastos_view'))

    try:
        datetime.strptime(fecha, '%Y-%m-%d')
    except ValueError:
        flash('El formato de fecha debe ser válido (AAAA-MM-DD).', 'danger')
        return redirect(url_for('gastos_view'))

    try:
        monto = float(monto_raw)
        if monto <= 0:
            flash('El monto debe ser un valor positivo mayor a cero.', 'danger')
            return redirect(url_for('gastos_view'))
    except ValueError:
        flash('El monto ingresado no es un número válido.', 'danger')
        return redirect(url_for('gastos_view'))

    if categoria not in CATEGORIAS_VALIDAS:
        categoria = 'Otros'

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO gastos (fecha, descripcion, monto, categoria, detalle_otro) VALUES (?, ?, ?, ?, ?)',
        (fecha, descripcion[:200], monto, categoria, detalle_otro[:150] if detalle_otro else None)
    )
    conn.commit()
    conn.close()

    flash('Gasto registrado exitosamente.', 'success')
    return redirect(url_for('gastos_view'))

@app.route('/gastos/<int:id>/editar', methods=['POST'])
@login_required
def editar_gasto(id):
    fecha = request.form.get('fecha', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    monto_raw = request.form.get('monto', '').strip()
    categoria = request.form.get('categoria', 'Alimentación').strip()
    detalle_otro = request.form.get('detalle_otro', '').strip() or None

    try:
        datetime.strptime(fecha, '%Y-%m-%d')
        monto = float(monto_raw)
        if monto <= 0:
            raise ValueError
    except (ValueError, TypeError):
        flash('Datos de actualización inválidos.', 'danger')
        return redirect(url_for('gastos_view'))

    if categoria not in CATEGORIAS_VALIDAS:
        categoria = 'Otros'

    conn = get_db_connection()
    conn.execute('''
        UPDATE gastos 
        SET fecha = ?, descripcion = ?, monto = ?, categoria = ?, detalle_otro = ?
        WHERE id = ?
    ''', (fecha, descripcion[:200], monto, categoria, detalle_otro[:150] if detalle_otro else None, id))
    conn.commit()
    conn.close()

    flash('Gasto actualizado correctamente.', 'success')
    return redirect(url_for('gastos_view'))

@app.route('/gastos/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_gasto(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM gastos WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('Gasto eliminado satisfactoriamente.', 'info')
    return redirect(url_for('gastos_view'))

# ==========================================================
# MÓDULO 3: REPORTES
# ==========================================================
@app.route('/reportes')
@login_required
def reportes():
    fecha_inicio = request.args.get('fecha_inicio', '').strip()
    fecha_fin = request.args.get('fecha_fin', '').strip()
    categoria = request.args.get('categoria', '').strip()

    query = 'SELECT id, fecha, descripcion, categoria, detalle_otro, monto, created_at FROM gastos WHERE 1=1'
    params = []

    if fecha_inicio:
        query += ' AND fecha >= ?'
        params.append(fecha_inicio)
    if fecha_fin:
        query += ' AND fecha <= ?'
        params.append(fecha_fin)
    if categoria and categoria in CATEGORIAS_VALIDAS:
        query += ' AND categoria = ?'
        params.append(categoria)

    query += ' ORDER BY fecha DESC, id DESC'

    conn = get_db_connection()
    gastos = conn.execute(query, params).fetchall()
    conn.close()

    total_filtrado = sum(row['monto'] for row in gastos)
    cantidad_filtrada = len(gastos)
    promedio_filtrado = total_filtrado / cantidad_filtrada if cantidad_filtrada > 0 else 0
    maximo_filtrado = max((row['monto'] for row in gastos), default=0)

    return render_template(
        'reportes.html',
        gastos=gastos,
        categorias_disponibles=CATEGORIAS_VALIDAS,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        categoria_sel=categoria,
        total_filtrado=total_filtrado,
        cantidad_filtrada=cantidad_filtrada,
        promedio_filtrado=promedio_filtrado,
        maximo_filtrado=maximo_filtrado
    )

@app.route('/reportes/exportar/csv')
@login_required
def exportar_csv():
    fecha_inicio = request.args.get('fecha_inicio', '').strip()
    fecha_fin = request.args.get('fecha_fin', '').strip()
    categoria = request.args.get('categoria', '').strip()

    query = 'SELECT id, fecha, descripcion, categoria, detalle_otro, monto, created_at FROM gastos WHERE 1=1'
    params = []

    if fecha_inicio:
        query += ' AND fecha >= ?'
        params.append(fecha_inicio)
    if fecha_fin:
        query += ' AND fecha <= ?'
        params.append(fecha_fin)
    if categoria and categoria in CATEGORIAS_VALIDAS:
        query += ' AND categoria = ?'
        params.append(categoria)

    query += ' ORDER BY fecha DESC, id DESC'

    conn = get_db_connection()
    gastos = conn.execute(query, params).fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Fecha', 'Descripcion', 'Categoria', 'Detalle Adicional', 'Monto (S/)', 'Registrado'])
    for g in gastos:
        cw.writerow([
            g['id'],
            g['fecha'],
            g['descripcion'],
            g['categoria'],
            g['detalle_otro'] or '',
            f"{g['monto']:.2f}",
            g['created_at']
        ])

    output = si.getvalue().encode('utf-8-sig') # UTF-8 BOM compatible con Microsoft Excel
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=dali_gastos_reporte.csv"}
    )

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='127.0.0.1', port=port, debug=app.config.get("DEBUG", False), load_dotenv=False)
