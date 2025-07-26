import sqlite3

conn = sqlite3.connect("votaciones.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    identificacion TEXT NOT NULL UNIQUE
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS opciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_opcion TEXT NOT NULL,
    imagen TEXT
);
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS votos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    id_opcion INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(id_usuario) REFERENCES usuarios(id),
    FOREIGN KEY(id_opcion) REFERENCES opciones(id)
);
""")

conn.commit()
conn.close()

print("✅ Base de datos creada o verificada.")