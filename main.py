from flask import Flask, render_template, request, redirect, session, send_file, jsonify, url_for
import sqlite3
import csv
import io

app = Flask(__name__)
app.secret_key = 'supersecreto'

ADMIN_USERS = {
    "admin": "123",
    "mau": "123",
    "juan": "123",
    "juandi": "123"
}

def get_db_connection():
    conn = sqlite3.connect('votaciones.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/", methods=["GET", "POST"])
def index():
    mensaje = None
    if request.method == "POST":
        nombre = request.form["nombre"]
        identificacion = request.form["identificacion"]

        conn = get_db_connection()
        user = conn.execute("SELECT * FROM usuarios WHERE identificacion = ?", (identificacion,)).fetchone()

        if user:
            voto = conn.execute("SELECT * FROM votos WHERE id_usuario = ?", (user["id"],)).fetchone()
            if voto:
                mensaje = "⚠️ Esta identificación ya ha votado. Verifícala nuevamente."
            else:
                session["usuario_id"] = user["id"]
                return redirect("/home")
        else:
            conn.execute("INSERT INTO usuarios (nombre, identificacion) VALUES (?, ?)", (nombre, identificacion))
            conn.commit()
            user = conn.execute("SELECT * FROM usuarios WHERE identificacion = ?", (identificacion,)).fetchone()
            session["usuario_id"] = user["id"]
            conn.close()
            return redirect("/home")
    return render_template("index.html", mensaje=mensaje)

@app.route("/home", methods=["GET", "POST"])
def home():
    if "usuario_id" not in session:
        return redirect("/")

    conn = get_db_connection()
    opciones = conn.execute("SELECT * FROM opciones").fetchall()

    if request.method == "POST":
        id_opcion = request.form.get("opcion")
        usuario_id = session.get("usuario_id")

        ya_voto = conn.execute("SELECT * FROM votos WHERE id_usuario = ?", (usuario_id,)).fetchone()
        if ya_voto:
            conn.close()
            return render_template("mensaje.html", mensaje="⚠️ Ya has votado. No puedes volver a hacerlo.")

        conn.execute("INSERT INTO votos (id_usuario, id_opcion) VALUES (?, ?)", (usuario_id, id_opcion))
        conn.commit()
        conn.close()
        session.pop("usuario_id", None)
        return render_template("mensaje.html", mensaje="✅ ¡Gracias por tu voto!", volver_inicio=True)

    conn.close()
    return render_template("home.html", opciones=opciones)

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        usuario = request.form["usuario"]
        clave = request.form["clave"]
        if usuario in ADMIN_USERS and ADMIN_USERS[usuario] == clave:
            session["admin"] = usuario
            return redirect("/admin_dashboard")
        else:
            error = "Credenciales incorrectas"
    return render_template("admin_login.html", error=error)

@app.route("/admin_dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db_connection()
    resultados = conn.execute("""
        SELECT o.nombre_opcion, COUNT(v.id_opcion) as total
        FROM opciones o
        LEFT JOIN votos v ON o.id = v.id_opcion
        GROUP BY o.id
    """).fetchall()
    conn.close()

    labels = [row["nombre_opcion"] for row in resultados]
    values = [row["total"] for row in resultados]

    return render_template("resultados_parciales.html", resultados=resultados, labels=labels, values=values)

@app.route("/exportar_csv")
def exportar_csv():
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db_connection()
    votos = conn.execute("""
        SELECT u.nombre, u.identificacion, o.nombre_opcion, v.timestamp
        FROM votos v
        JOIN usuarios u ON v.id_usuario = u.id
        JOIN opciones o ON v.id_opcion = o.id
    """).fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Nombre", "Identificación", "Opción Votada", "Fecha y Hora"])
    for voto in votos:
        writer.writerow([voto["nombre"], voto["identificacion"], voto["nombre_opcion"], voto["timestamp"]])
    output.seek(0)

    return send_file(io.BytesIO(output.getvalue().encode()), mimetype="text/csv",
                     as_attachment=True, download_name="votaciones.csv")

@app.route("/exportar_json")
def exportar_json():
    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_db_connection()
    votos = conn.execute("""
        SELECT u.nombre, u.identificacion, o.nombre_opcion, v.timestamp
        FROM votos v
        JOIN usuarios u ON v.id_usuario = u.id
        JOIN opciones o ON v.id_opcion = o.id
    """).fetchall()
    conn.close()

    data = [dict(voto) for voto in votos]
    return jsonify(data)

@app.route("/logout_admin")
def logout_admin():
    session.pop("admin", None)
    return redirect("/admin_login")

if __name__ == "__main__":
    app.run(debug=True)

@app.route('/votar', methods=['POST'])
def votar():
    # lógica de votación...
    mensaje = "¡Gracias por tu voto!"
    return render_template("mensaje.html", mensaje=mensaje, volver_inicio=True)
