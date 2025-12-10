import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap

ASSETS = Path(__file__).parent / "assets"
WINDOW_W, WINDOW_H = 960, 640
RECORDS_FILE = Path(__file__).parent / "records.json"
ASSETS.mkdir(exist_ok=True)

def cargar_records():
    if RECORDS_FILE.exists():
        try:
            return json.loads(RECORDS_FILE.read_text(encoding="utf-8"))
        except:
            return []
    return []

def guardar_records(records):
    try:
        RECORDS_FILE.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print("Error guardando records:", e)


def cargar_imagen(nombre, w=None, h=None):
    ruta = ASSETS / nombre
    if ruta.exists():
        pm = QPixmap(str(ruta))
        if w and h:
            return pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pm
    pm = QPixmap(w, h)
    pm.fill(QColor(120, 120, 120))
    return pm