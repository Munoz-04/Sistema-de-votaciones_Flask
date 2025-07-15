from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clave_segura'

# Diccionario de administradores
admins = {
    "admin": "123",
    "mau": "123",
    "juan": "123",
    "juandi": "123"
}

# Página principal con formulario de registro
@app.route('/')
def index():
    return render_template('index.html')

# Procesar registro
@app.route('/register', methods=['POST'])
def register():
    nombre = request.form.get('nombre')
    identificacion = request.form.get('identificacion')
    return render_template('success.html', nombre=nombre, identificacion=identificacion)

# Ruta de login admin
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        user = request.form.get('admin_user')
        password = request.form.get('admin_pass')
        if user in admins and admins[user] == password:
            return f"<h2>Bienvenido, {user.capitalize()}</h2>"
        else:
            flash("Credenciales incorrectas")
            return redirect(url_for('admin'))
    return render_template('admin_login.html')

if __name__ == '__main__':
    app.run(debug=True)
