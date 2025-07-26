from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import sqlite3
import io
import pandas as pd
import json
import csv
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = 'clave_segura'

DATABASE = 'votacion.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            identificacion TEXT UNIQUE NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidatos (
            nombre_candidato TEXT PRIMARY KEY,
            votos INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL,
            id_opcion TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (id_usuario) REFERENCES usuarios(id)
        )
    ''')
    candidatos_iniciales = ['candidato1', 'candidato2', 'candidato3']
    for cand in candidatos_iniciales:
        cursor.execute("INSERT OR IGNORE INTO candidatos (nombre_candidato, votos) VALUES (?, 0)", (cand,))
    conn.commit()
    conn.close()

with app.app_context():
    init_db()

# Diccionario de administradores
admins = {
    "admin": "123",
    "mau": "123",
    "juan": "123",
    "juandi": "123"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    nombre = request.form.get('nombre')
    identificacion = request.form.get('identificacion')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (nombre, identificacion) VALUES (?, ?)", (nombre, identificacion))
        conn.commit()
        flash("Registro exitoso. Ahora puedes votar.")
        session['identificacion'] = identificacion
        return redirect(url_for('votacion'))
    except sqlite3.IntegrityError:
        flash("Ya existe un usuario con esa identificación.")
        return redirect(url_for('index'))
    finally:
        conn.close()

@app.route('/votacion')
def votacion():
    identificacion = session.get('identificacion')
    if not identificacion:
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE identificacion = ?", (identificacion,))
    usuario = cursor.fetchone()
    if not usuario:
        return redirect(url_for('index'))
    cursor.execute("SELECT id FROM votos WHERE id_usuario = ?", (usuario['id'],))
    voto = cursor.fetchone()
    if voto:
        flash("Ya has votado.")
        return redirect(url_for('index'))
    cursor.execute("SELECT nombre_candidato FROM candidatos")
    candidatos = [row['nombre_candidato'] for row in cursor.fetchall()]
    conn.close()
    return render_template('votacion.html', candidatos=candidatos)

@app.route('/votar', methods=['POST'])
def votar():
    identificacion = session.get('identificacion')
    eleccion = request.form.get('eleccion')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM usuarios WHERE identificacion = ?", (identificacion,))
    usuario = cursor.fetchone()
    if not usuario:
        return redirect(url_for('index'))
    cursor.execute("SELECT id FROM votos WHERE id_usuario = ?", (usuario['id'],))
    voto = cursor.fetchone()
    if voto:
        flash("Ya has votado.")
        return redirect(url_for('index'))
    cursor.execute("INSERT INTO votos (id_usuario, id_opcion) VALUES (?, ?)", (usuario['id'], eleccion))
    cursor.execute("UPDATE candidatos SET votos = votos + 1 WHERE nombre_candidato = ?", (eleccion,))
    conn.commit()
    conn.close()
    return render_template('success.html', nombre=identificacion, identificacion=identificacion)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        user = request.form.get('admin_user')
        password = request.form.get('admin_pass')
        if user in admins and admins[user] == password:
            session['admin'] = user
            return redirect(url_for('panel_admin'))
        else:
            flash("Credenciales incorrectas")
            return redirect(url_for('admin'))
    return render_template('admin_login.html')

@app.route('/panel_admin')
def panel_admin():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    return render_template('home.html')

@app.route('/resultados')
def resultados():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_candidato, votos FROM candidatos ORDER BY votos DESC")
    resultados_candidatos = cursor.fetchall()
    total_votos = sum(row['votos'] for row in resultados_candidatos)
    cursor.execute("""
        SELECT u.identificacion, u.nombre, v.id_opcion, v.timestamp
        FROM votos v
        JOIN usuarios u ON v.id_usuario = u.id
        ORDER BY v.timestamp DESC
    """)
    todos_los_votos = cursor.fetchall()
    conn.close()
    return render_template('resultados_parciales.html',
                           resultados=resultados_candidatos,
                           total=total_votos,
                           todos_los_votos=todos_los_votos)

@app.route('/descargar_votos_excel')
def descargar_votos_excel():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.identificacion, u.nombre, v.id_opcion, v.timestamp
        FROM votos v
        JOIN usuarios u ON v.id_usuario = u.id
        ORDER BY v.timestamp DESC
    """)
    todos_los_votos = cursor.fetchall()
    conn.close()
    data_for_df = []
    for row in todos_los_votos:
        data_for_df.append({
            'Identificacion': row['identificacion'],
            'Nombre': row['nombre'],
            'Eleccion': row['id_opcion'].replace('candidato', 'Candidato '),
            'Fecha_Voto': row['timestamp']
        })
    df = pd.DataFrame(data_for_df)
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Todos_los_Votos')
    excel_buffer.seek(0)
    return send_file(
        excel_buffer,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='todos_los_votos.xlsx'
    )

@app.route('/descargar_votos_json')
def descargar_votos_json():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.identificacion, u.nombre, v.id_opcion, v.timestamp
        FROM votos v
        JOIN usuarios u ON v.id_usuario = u.id
        ORDER BY v.timestamp DESC
    """)
    todos_los_votos = cursor.fetchall()
    conn.close()
    data_for_json = []
    for row in todos_los_votos:
        data_for_json.append({
            'identificacion': row['identificacion'],
            'nombre': row['nombre'],
            'eleccion': row['id_opcion'].replace('candidato', 'Candidato '),
            'fecha_voto': row['timestamp']
        })
    json_buffer = io.BytesIO(json.dumps(data_for_json, indent=4).encode('utf-8'))
    json_buffer.seek(0)
    return send_file(
        json_buffer,
        mimetype='application/json',
        as_attachment=True,
        download_name='todos_los_votos.json'
    )

@app.route('/descargar_votantes_excel')
def descargar_votantes_excel():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, identificacion FROM usuarios ORDER BY nombre ASC")
    usuarios = cursor.fetchall()
    conn.close()

    # Crear archivo CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output)

    # Escribir encabezados
    writer.writerow(['Nombre', 'Identificación'])

    # Escribir filas
    for usuario in usuarios:
        writer.writerow([usuario['nombre'], usuario['identificacion']])

    # Convertir a BytesIO para enviar como archivo descargable
    csv_bytes = io.BytesIO()
    csv_bytes.write(output.getvalue().encode('utf-8'))  # Sin 'utf-8-sig'
    csv_bytes.seek(0)

    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name='votantes.csv'
    )



@app.route('/descargar_votantes_json')
def descargar_votantes_json():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, identificacion FROM usuarios ORDER BY nombre ASC")
    usuarios = cursor.fetchall()
    conn.close()
    data_for_json = [dict(u) for u in usuarios]
    json_buffer = io.BytesIO(json.dumps(data_for_json, indent=4).encode('utf-8'))
    json_buffer.seek(0)
    return send_file(
        json_buffer,
        mimetype='application/json',
        as_attachment=True,
        download_name='votantes.json'
    )

@app.route('/resultados_graficos')
def resultados_graficos():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_candidato, votos FROM candidatos ORDER BY nombre_candidato ASC")
    datos = cursor.fetchall()
    conn.close()

    return render_template('resultados_graficos.html', datos=datos)



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/votantes')
def votantes():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre, identificacion FROM usuarios ORDER BY nombre ASC")
    usuarios = cursor.fetchall()
    conn.close()
    return render_template('votantes.html', usuarios=usuarios)

if __name__ == '__main__':
    app.run(debug=True)