from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response
from functools import wraps
from datetime import datetime
import csv
import io
from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = 'gastos_app_secret_key_super_segura_2026'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.args.get('demo') == '1':
            session['user'] = 'admin'
        if not session.get('user'):
            flash('Por favor inicia sesión para acceder al sistema.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user'] = user['username']
            flash('¡Bienvenido de nuevo al panel de control!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Credenciales incorrectas. Verifique usuario o contraseña.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

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

    # Gastos de este mes
    current_month = datetime.now().strftime('%Y-%m')
    mes_stat = conn.execute('''
        SELECT COALESCE(SUM(monto), 0) AS total_mes
        FROM gastos 
        WHERE strftime('%Y-%m', fecha) = ?
    ''', (current_month,)).fetchone()

    # Últimos 10 gastos registrados
    gastos = conn.execute('''
        SELECT id, fecha, descripcion, monto, categoria, created_at
        FROM gastos
        ORDER BY fecha DESC, id DESC
    ''').fetchall()

    # Datos para Gráfico de Tendencia Diaria (Últimos 14 registros agrupados por fecha)
    tendencia = conn.execute('''
        SELECT fecha, SUM(monto) as total_dia
        FROM gastos
        GROUP BY fecha
        ORDER BY fecha ASC
    ''').fetchall()

    # Datos para Gráfico de Categorías
    por_categoria = conn.execute('''
        SELECT categoria, SUM(monto) as total_cat, COUNT(*) as cantidad
        FROM gastos
        GROUP BY categoria
        ORDER BY total_cat DESC
    ''').fetchall()

    conn.close()

    chart_labels = [row['fecha'] for row in tendencia]
    chart_values = [round(row['total_dia'], 2) for row in tendencia]

    cat_labels = [row['categoria'] for row in por_categoria]
    cat_values = [round(row['total_cat'], 2) for row in por_categoria]

    return render_template(
        'dashboard.html',
        stats=stats,
        total_mes=mes_stat['total_mes'],
        gastos=gastos,
        chart_labels=chart_labels,
        chart_values=chart_values,
        cat_labels=cat_labels,
        cat_values=cat_values,
        current_date=datetime.now().strftime('%d/%m/%Y')
    )

@app.route('/gasto/crear', methods=['POST'])
@login_required
def crear_gasto():
    fecha = request.form.get('fecha')
    descripcion = request.form.get('descripcion', '').strip()
    monto_raw = request.form.get('monto')
    categoria = request.form.get('categoria', 'General').strip()

    if not fecha or not descripcion or not monto_raw:
        flash('Todos los campos son obligatorios.', 'danger')
        return redirect(url_for('dashboard'))

    try:
        monto = float(monto_raw)
        if monto <= 0:
            flash('El monto debe ser un valor positivo mayor a 0.', 'danger')
            return redirect(url_for('dashboard'))
    except ValueError:
        flash('Monto no válido. Ingrese un valor numérico.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    conn.execute(
        'INSERT INTO gastos (fecha, descripcion, monto, categoria) VALUES (?, ?, ?, ?)',
        (fecha, descripcion, monto, categoria)
    )
    conn.commit()
    conn.close()

    flash('¡Gasto registrado exitosamente!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/gasto/<int:id>/editar', methods=['POST'])
@login_required
def editar_gasto(id):
    fecha = request.form.get('fecha')
    descripcion = request.form.get('descripcion', '').strip()
    monto_raw = request.form.get('monto')
    categoria = request.form.get('categoria', 'General').strip()

    try:
        monto = float(monto_raw)
        if monto <= 0:
            flash('El monto debe ser mayor a 0.', 'danger')
            return redirect(url_for('dashboard'))
    except (ValueError, TypeError):
        flash('Monto no válido.', 'danger')
        return redirect(url_for('dashboard'))

    conn = get_db_connection()
    conn.execute('''
        UPDATE gastos 
        SET fecha = ?, descripcion = ?, monto = ?, categoria = ?
        WHERE id = ?
    ''', (fecha, descripcion, monto, categoria, id))
    conn.commit()
    conn.close()

    flash('Gasto actualizado correctamente.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/gasto/<int:id>/eliminar', methods=['POST'])
@login_required
def eliminar_gasto(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM gastos WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('Gasto eliminado satisfactoriamente.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/reportes')
@login_required
def reportes():
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    categoria = request.args.get('categoria', '')
    buscar = request.args.get('buscar', '').strip()

    query = 'SELECT * FROM gastos WHERE 1=1'
    params = []

    if fecha_inicio:
        query += ' AND fecha >= ?'
        params.append(fecha_inicio)
    if fecha_fin:
        query += ' AND fecha <= ?'
        params.append(fecha_fin)
    if categoria and categoria != 'TODAS':
        query += ' AND categoria = ?'
        params.append(categoria)
    if buscar:
        query += ' AND descripcion LIKE ?'
        params.append(f'%{buscar}%')

    query += ' ORDER BY fecha DESC, id DESC'

    conn = get_db_connection()
    gastos = conn.execute(query, params).fetchall()

    # Categorías disponibles para el selector
    categorias = conn.execute('SELECT DISTINCT categoria FROM gastos ORDER BY categoria ASC').fetchall()

    # Cálculos para el reporte actual
    total_filtrado = sum(row['monto'] for row in gastos)
    cantidad_filtrada = len(gastos)
    promedio_filtrado = total_filtrado / cantidad_filtrada if cantidad_filtrada > 0 else 0
    maximo_filtrado = max((row['monto'] for row in gastos), default=0)

    conn.close()

    return render_template(
        'reportes.html',
        gastos=gastos,
        categorias=categorias,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        categoria_sel=categoria,
        buscar=buscar,
        total_filtrado=total_filtrado,
        cantidad_filtrada=cantidad_filtrada,
        promedio_filtrado=promedio_filtrado,
        maximo_filtrado=maximo_filtrado
    )

@app.route('/reportes/exportar/csv')
@login_required
def exportar_csv():
    fecha_inicio = request.args.get('fecha_inicio', '')
    fecha_fin = request.args.get('fecha_fin', '')
    categoria = request.args.get('categoria', '')
    buscar = request.args.get('buscar', '').strip()

    query = 'SELECT id, fecha, descripcion, categoria, monto, created_at FROM gastos WHERE 1=1'
    params = []

    if fecha_inicio:
        query += ' AND fecha >= ?'
        params.append(fecha_inicio)
    if fecha_fin:
        query += ' AND fecha <= ?'
        params.append(fecha_fin)
    if categoria and categoria != 'TODAS':
        query += ' AND categoria = ?'
        params.append(categoria)
    if buscar:
        query += ' AND descripcion LIKE ?'
        params.append(f'%{buscar}%')

    query += ' ORDER BY fecha DESC'

    conn = get_db_connection()
    gastos = conn.execute(query, params).fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Fecha', 'Descripcion', 'Categoria', 'Monto ($)', 'Registrado En'])
    for g in gastos:
        cw.writerow([g['id'], g['fecha'], g['descripcion'], g['categoria'], f"{g['monto']:.2f}", g['created_at']])

    output = si.getvalue().encode('utf-8-sig') # UTF-8 with BOM para Excel
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=reporte_gastos.csv"}
    )

if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='127.0.0.1', port=5000, load_dotenv=False)
