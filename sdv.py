from flask import Flask, jsonify, send_file, Response
import csv
import io
import json
import os


# Archivo donde se guardan los votantes
DATA_FILE = 'votantes.json'

# Cargar datos desde el archivo si existe
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
else:
    data = []

app = Flask(__name__)

# Página de inicio con formulario y enlaces
@app.route('/', methods=['GET'])
def index():
    return '''
    <html>
    <head>
    <title>Sistema de Votaciones</title>
    <link href="https://fonts.googleapis.com/css?family=Roboto:400,700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: 'Roboto', Arial, sans-serif; background: #f4f6fa; margin: 0; padding: 0; }
        .container { max-width: 700px; margin: 30px auto; background: #fff; border-radius: 10px; box-shadow: 0 2px 8px #0001; padding: 30px; }
        h1 { color: #2c3e50; text-align: center; }
        form { margin-bottom: 25px; display: flex; flex-direction: column; gap: 10px; }
        label { font-weight: 700; }
        input, select { padding: 6px 10px; border-radius: 5px; border: 1px solid #ccc; }
        button { background: #2980b9; color: #fff; border: none; border-radius: 5px; padding: 10px 0; font-size: 1em; font-weight: bold; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #1c5d85; }
        ul { list-style: none; padding: 0; }
        .usuarios { margin-bottom: 30px; }
        .usuarios li { background: #eaf1fb; margin-bottom: 6px; padding: 8px 12px; border-radius: 5px; }
        .links { margin-bottom: 20px; }
        .links li { display: inline-block; margin-right: 15px; }
        .chart-container { background: #f9fafc; border-radius: 10px; padding: 20px; }
    </style>
    </head>
    <body>
    <div class="container">
    <h1>Sistema de Votaciones</h1>
    <form action="/add" method="post">
        <label>Nombre: <input type="text" name="nombre" required></label>
        <label>Identificación: <input type="text" name="identificacion" required></label>
        <label>¿Por quién votas?
            <select name="voto" required>
                <option value="">Selecciona un candidato</option>
                <option value="Candidato A">Candidato A</option>
                <option value="Candidato B">Candidato B</option>
                <option value="Candidato C">Candidato C</option>
            </select>
        </label>
        <button type="submit">Registrar voto</button>
    </form>
    <ul class="links">
        <li><a href="/export/json">Exportar a JSON</a></li>
        <li><a href="/export/csv">Exportar a CSV</a></li>
        <li><a href="/chart/data">Ver datos para gráficos</a></li>
    </ul>
    <h2>Votantes registrados</h2>
    <ul class="usuarios">
        %s
    </ul>
    <div class="chart-container">
        <h2>Gráfico de Votos</h2>
        <canvas id="chartVotos" width="400" height="200"></canvas>
    </div>
    </div>
    <script>
    fetch('/chart/data')
      .then(response => response.json())
      .then(data => {
        const ctx = document.getElementById('chartVotos').getContext('2d');
        new Chart(ctx, {
          type: 'bar',
          data: {
            labels: data.labels,
            datasets: [{
              label: 'Cantidad de votos',
              data: data.values,
              backgroundColor: [
                'rgba(54, 162, 235, 0.5)',
                'rgba(255, 99, 132, 0.5)',
                'rgba(255, 206, 86, 0.5)'
              ],
              borderColor: [
                'rgba(54, 162, 235, 1)',
                'rgba(255, 99, 132, 1)',
                'rgba(255, 206, 86, 1)'
              ],
              borderWidth: 1
            }]
          },
          options: {
            plugins: { legend: { display: false } },
            scales: {
              y: { beginAtZero: true, stepSize: 1 }
            }
          }
        });
      });
    </script>
    </body>
    </html>
    ''' % ''.join(f'<li>{u["nombre"]} (ID: {u["identificacion"]}, Voto: {u["voto"]})</li>' for u in data)

# Endpoint para agregar usuario
from flask import request, redirect, url_for
@app.route('/add', methods=['POST'])
def add_user():
    nombre = request.form.get('nombre')
    identificacion = request.form.get('identificacion')
    voto = request.form.get('voto')
    if nombre and identificacion and voto:
        data.append({"nombre": nombre, "identificacion": identificacion, "voto": voto})
        # Guardar en archivo
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return redirect(url_for('index'))

# Endpoint para exportar a JSON
@app.route('/export/json')
def export_json():
    return jsonify(data)

# Endpoint para exportar a CSV
@app.route('/export/csv')
def export_csv():
    si = io.StringIO()
    writer = csv.DictWriter(si, fieldnames=["nombre", "identificacion", "voto"])
    writer.writeheader()
    writer.writerows(data)
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=votantes.csv"})

# Endpoint para datos de gráficos
@app.route('/chart/data')
def chart_data():
    # Contar votos por candidato
    votos = {}
    for d in data:
        v = d["voto"]
        votos[v] = votos.get(v, 0) + 1
    chart = {
        "labels": list(votos.keys()),
        "values": list(votos.values())
    }
    return jsonify(chart)

if __name__ == '__main__':
    app.run(debug=True)
