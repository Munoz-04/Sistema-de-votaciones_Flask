from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'  # Necesaria para usar flash

# Página principal (formulario)
@app.route('/')
def home():
    return render_template('index.html')

# Ruta que recibe el login
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('u')
    password = request.form.get('p')

    # Lógica simple de validación
    if username == "admin" and password == "1234":
        return f"<h2>¡Bienvenido, {username}!</h2>"
    else:
        flash("Usuario o contraseña incorrectos")
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)

