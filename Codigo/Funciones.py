from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
import sqlite3
import datetime

ASSETS = Path(__file__).parent / "assets"
WINDOW_W, WINDOW_H = 960, 640
DB_FILE = Path(__file__).parent / "pixel_kong.db"
ASSETS.mkdir(exist_ok=True)

def cargar_imagen(nombre, w=None, h=None): #para cargar mas facil las imagenes
    ruta = ASSETS / nombre
    if ruta.exists():
        pm = QPixmap(str(ruta))
        if w and h:
            return pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pm
    pm = QPixmap(w, h)
    pm.fill(QColor(120, 120, 120))
    return pm


# ========== FUNCIONES DE BASE DE DATOS SQLite ==========

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS records
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       nombre
                       TEXT
                       NOT
                       NULL,
                       puntos
                       INTEGER
                       NOT
                       NULL,
                       nivel
                       INTEGER
                       NOT
                       NULL,
                       fecha
                       TIMESTAMP
                       DEFAULT
                       CURRENT_TIMESTAMP
                   )
                   ''')

    cursor.execute('''
                   CREATE INDEX IF NOT EXISTS idx_puntos
                       ON records(puntos DESC)
                   ''')

    conn.commit()
    conn.close()


def cargar_records():
    init_db()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
                   SELECT nombre, puntos, nivel, fecha
                   FROM records
                   ORDER BY puntos DESC, fecha DESC LIMIT 100
                   ''')

    records = []
    for row in cursor.fetchall():
        fecha = row[3]
        if fecha:
            try:
                fecha_obj = datetime.datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
                fecha_formateada = fecha_obj.strftime('%d/%m/%Y %H:%M')
            except:
                fecha_formateada = fecha
        else:
            fecha_formateada = "Sin fecha"

        records.append({
            "nombre": row[0],
            "puntos": row[1],
            "nivel": row[2],
            "fecha": fecha_formateada
        })


    conn.close()
    return records


def guardar_record(nombre, puntos, nivel):
    init_db()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
                   INSERT INTO records (nombre, puntos, nivel)
                   VALUES (?, ?, ?)
                   ''', (nombre, puntos, nivel))

    conn.commit()
    conn.close()
