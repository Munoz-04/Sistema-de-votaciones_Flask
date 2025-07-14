import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

conn = sqlite3.connect("votaciones.db")
cursor = conn.cursor()

cursor.executescript("""
DROP TABLE IF EXISTS votos;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS opciones;
                     
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    correo TEXT UNIQUE NOT NULL,
    contraseña_hash TEXT NOT NULL
);
                     
CREATE TABLE opciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_opcion TEXT NOT NULL
);
                     
CREATE TABLE votos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    id_opcion INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (id_opcion) REFERENCES opciones(id) ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TRIGGER IF NOT EXISTS evitar_voto_duplicado
    BEFORE INSERT ON votos
    FOR EACH ROW
    WHEN (SELECT COUNT(*) FROM votos WHERE id_usuario = NEW.id_usuario) > 0
    BEGIN
        SELECT RAISE (ABORT, 'El usuario ya ha votado');
END;
    """)

# Insertar usuarios de prueba
usuarios = [
    ("Juan Pérez", "juan@example.com", "contraseña123"),
    ("María Gómez", "maria@example.com", "contraseña456"),
    ("Pedro López", "pedro@example.com", "contraseña789")
]

for nombre, correo, clave in usuarios:
    clave_hash = hash_password(clave)
    cursor.execute("INSERT INTO usuarios (nombre, correo, contraseña_hash) VALUES (?, ?, ?)", (nombre, correo, clave_hash))

# insertar opciones (candidatos o ideas)
opciones = ["Candidato A", "Candidato B", "Candidato C"]
for nombre_opcion in opciones:
    cursor.execute("INSERT INTO opciones (nombre_opcion) VALUES (?)", (nombre_opcion,))

# confirmar y cerrar
conn.commit()
conn.close()

print("Base de datos y tablas creadas correctamente con datos iniciales.")