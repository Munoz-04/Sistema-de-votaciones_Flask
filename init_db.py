import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import json # Asegúrate de que json esté importado_hbascjascas
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
    identificacion TEXT UNIQUE NOT NULL
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

CREATE INDEX IF NOT EXISTS idx_votos_opcion ON votos(id_opcion);
CREATE INDEX IF NOT EXISTS idx_votos_usuario ON votos(id_usuario);

CREATE TRIGGER IF NOT EXISTS evitar_voto_duplicado
BEFORE INSERT ON votos
FOR EACH ROW
WHEN (SELECT COUNT(*) FROM votos WHERE id_usuario = NEW.id_usuario) > 0
BEGIN
    SELECT RAISE(ABORT, 'El usuario ya ha votado');
END;
""")

# Opciones (candidatos o ideas)
opciones = ["Candidato A", "Candidato B", "Candidato C"]
for nombre_opcion in opciones:
    cursor.execute("INSERT INTO opciones (nombre_opcion) VALUES (?)", (nombre_opcion,))

conn.commit()
conn.close()

print("✅ Base de datos creada sin usuarios y con identificaciones únicas.")