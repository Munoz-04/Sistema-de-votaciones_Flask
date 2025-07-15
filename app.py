from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3
import os
import io
import base64
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json # Asegúrate de que json esté importado

# Inicialización de la aplicación Flask
app = Flask(__name__)
# app.secret_key = 'super_secret_key' # Esta línea sigue comentada o eliminada

# -- Configuración de la Base de Datos --
DATABASE = 'votacion.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identificacion TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            eleccion TEXT NOT NULL,
            fecha_voto TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS candidatos (
            nombre_candidato TEXT PRIMARY KEY,
            votos INTEGER DEFAULT 0
        )
    ''')

    candidatos_iniciales = ['candidato1', 'candidato2', 'candidato3']
    for cand in candidatos_iniciales:
        cursor.execute("INSERT OR IGNORE INTO candidatos (nombre_candidato, votos) VALUES (?, 0)", (cand,))

    conn.commit()
    conn.close()
    print("Base de datos 'votacion.db' y tablas inicializadas o verificadas.")

with app.app_context():
    init_db()

# --- Rutas de la Aplicación ---

@app.route('/')
def main_home():
    return render_template('main_home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == 'admin' and password == '123':
            return redirect(url_for('home'))
        else:
            return render_template('login.html')
    return render_template('login.html')

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/votacion')
def votacion_page():
    return render_template('votacion.html')


@app.route('/votar', methods=['POST'])
def votar():
    identificacion = request.form['identificacion']
    nombre = request.form['nombre']
    eleccion = request.form.get('eleccion')

    if not eleccion:
        return redirect(url_for('votacion_page'))

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO votos (identificacion, nombre, eleccion) VALUES (?, ?, ?)",
            (identificacion, nombre, eleccion)
        )
        cursor.execute(
            "UPDATE candidatos SET votos = votos + 1 WHERE nombre_candidato = ?",
            (eleccion,)
        )
        conn.commit()
        return render_template('voto_confirmado.html')

    except sqlite3.IntegrityError:
        return render_template('voto_ya_registrado.html', identificacion=identificacion)
    except Exception as e:
        conn.rollback()
        return render_template('error_generico.html', mensaje="Ocurrió un error inesperado al procesar tu voto.")
    finally:
        conn.close()


@app.route('/resultados')
def resultados_lista():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener el resumen de votos por candidato (como antes)
    cursor.execute("SELECT nombre_candidato, votos FROM candidatos ORDER BY votos DESC")
    resultados_candidatos = cursor.fetchall()
    total_votos = sum(row['votos'] for row in resultados_candidatos)

    # Obtener todos los registros de votos individuales (NUEVA PARTE)
    cursor.execute("SELECT identificacion, nombre, eleccion, fecha_voto FROM votos ORDER BY fecha_voto DESC")
    todos_los_votos = cursor.fetchall() # Esto contendrá cada voto registrado
    
    conn.close()
    
    return render_template('resultados_parciales.html', 
                           resultados=resultados_candidatos, 
                           total=total_votos,
                           todos_los_votos=todos_los_votos) # Pasar todos los votos a la plantilla

# NUEVA RUTA PARA DESCARGAR TODOS LOS VOTOS EN EXCEL
@app.route('/descargar_votos_excel')
def descargar_votos_excel():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT identificacion, nombre, eleccion, fecha_voto FROM votos ORDER BY fecha_voto DESC")
    todos_los_votos = cursor.fetchall()
    conn.close()

    # Convertir los resultados a un formato de lista de diccionarios para pandas
    data_for_df = []
    for row in todos_los_votos:
        data_for_df.append({
            'Identificacion': row['identificacion'],
            'Nombre': row['nombre'],
            'Eleccion': row['eleccion'].replace('candidato', 'Candidato '),
            'Fecha_Voto': row['fecha_voto']
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

# NUEVA RUTA PARA DESCARGAR TODOS LOS VOTOS EN JSON
@app.route('/descargar_votos_json')
def descargar_votos_json():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT identificacion, nombre, eleccion, fecha_voto FROM votos ORDER BY fecha_voto DESC")
    todos_los_votos = cursor.fetchall()
    conn.close()

    data_for_json = []
    for row in todos_los_votos:
        data_for_json.append({
            'identificacion': row['identificacion'],
            'nombre': row['nombre'],
            'eleccion': row['eleccion'].replace('candidato', 'Candidato '),
            'fecha_voto': row['fecha_voto']
        })
    
    json_buffer = io.BytesIO(json.dumps(data_for_json, indent=4).encode('utf-8'))
    json_buffer.seek(0)

    return send_file(
        json_buffer,
        mimetype='application/json',
        as_attachment=True,
        download_name='todos_los_votos.json'
    )


@app.route('/resultados_graficos')
def resultados_graficos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nombre_candidato, votos FROM candidatos ORDER BY votos DESC")
    resultados_db = cursor.fetchall()
    total_votos = sum(row['votos'] for row in resultados_db)
    conn.close()

    nombres_candidatos = [row['nombre_candidato'].replace('candidato', 'Candidato ') for row in resultados_db]
    votos_candidatos = [row['votos'] for row in resultados_db]

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6c757d', '#17a2b8']
    bars = ax.bar(nombres_candidatos, votos_candidatos, color=colors[:len(nombres_candidatos)])

    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 0.5, int(yval), ha='center', va='bottom', fontsize=10)

    ax.set_xlabel('Candidatos')
    ax.set_ylabel('Número de Votos')
    ax.set_title('Resultados de la Votación')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    img_bytes = io.BytesIO()
    plt.savefig(img_bytes, format='png', bbox_inches='tight')
    img_bytes.seek(0)
    plt.close(fig)

    encoded_img = base64.b64encode(img_bytes.read()).decode('utf-8')

    return render_template('resultados_graficos.html', encoded_img=encoded_img, total=total_votos)


# --- Rutas para páginas de mensaje (opcionales, pero útiles para UX) ---
@app.route('/voto_ya_registrado')
def voto_ya_registrado_page():
    return render_template('voto_ya_registrado.html')

@app.route('/error_generico')
def error_generico():
    return render_template('error_generico.html', mensaje="Un error desconocido ha ocurrido.")


if __name__ == '__main__':
    app.run(debug=True)