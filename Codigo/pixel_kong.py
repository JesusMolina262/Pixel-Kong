import sys, random, json
from pathlib import Path
from PySide6.QtCore import Qt, QTimer, QUrl, QRect
from PySide6.QtGui import QPainter, QColor, QFont, QPixmap, QFontDatabase
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout, QPushButton, QDialog, QFormLayout, QLineEdit, QMessageBox, QListWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


ASSETS = Path(__file__).parent / "assets"
WINDOW_W, WINDOW_H = 960, 640
RECORDS_FILE = Path(__file__).parent / "records.json"
ASSETS.mkdir(exist_ok=True)

def cargar_imagen(nombre, w=None, h=None):
    ruta = ASSETS / nombre
    if ruta.exists():
        pm = QPixmap(str(ruta))
        if w and h:
            return pm.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return pm
    pm = QPixmap(w or 32, h or 32)
    pm.fill(QColor(120, 120, 120))
    return pm

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

# ---------- MENU ----------
class MenuWidget(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.init_ui()
        self.init_audio()

    def init_ui(self):
        self.setFixedSize(WINDOW_W, WINDOW_H)
        self.setStyleSheet("background: black;")
        layout = QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        fondo = QLabel()
        fondo_pm = cargar_imagen("fondo.png", WINDOW_W, WINDOW_H)
        fondo.setPixmap(fondo_pm)
        fondo.setFixedSize(WINDOW_W, WINDOW_H)

        overlay = QWidget(fondo)
        overlay.setGeometry(0,0,WINDOW_W,WINDOW_H)
        v = QVBoxLayout(overlay)
        v.setContentsMargins(220, 130, 220, 130)
        v.setSpacing(18)

        font_id = QFontDatabase.addApplicationFont(f"{ASSETS}/arcadeclassic.regular.ttf")
        font_families = QFontDatabase.applicationFontFamilies(font_id)
        pixel_font_family = font_families[0]
        pixel_font = QFont(pixel_font_family)
        pixel_font.setPixelSize(24)
        titulo = QLabel("PIXEL KONG")
        titulo.setFont(pixel_font)
        titulo.setAlignment(Qt.AlignCenter)
        titulo.setStyleSheet("color: white; font-size: 44px; font-weight: bold;")
        v.addWidget(titulo)

        btn_jugar = QPushButton("JUGAR")
        btn_jugar.setFont(pixel_font)
        btn_records = QPushButton("RECORDS")
        btn_records.setFont(pixel_font)
        btn_salir = QPushButton("SALIR")
        btn_salir.setFont(pixel_font)
        for b in (btn_jugar, btn_records, btn_salir):
            b.setFixedHeight(54)
            b.setStyleSheet("background: black; font-size: 16px; color:white;")
            v.addWidget(b)

        btn_jugar.clicked.connect(self.abrir_fachada)
        btn_records.clicked.connect(self.abrir_records)
        btn_salir.clicked.connect(lambda: QApplication.quit())

        layout.addWidget(fondo)
        self.setLayout(layout)

    def init_audio(self):
        ruta = ASSETS / "musica.mp3"
        if ruta.exists():
            self.player = QMediaPlayer(self)
            self.out = QAudioOutput(self)
            self.player.setAudioOutput(self.out)
            self.player.setSource(QUrl.fromLocalFile(str(ruta)))
            self.out.setVolume(0.15)
            self.player.play()
        else:
            self.player = None

    def abrir_fachada(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Crear/Unirse a sala (fachada)")
        dlg.setFixedSize(360,220)
        form = QFormLayout(dlg)
        txt_nombre = QLineEdit(); txt_nombre.setPlaceholderText("Tu nombre")
        txt_rival = QLineEdit(); txt_rival.setPlaceholderText("Nombre rival (simulado)")
        txt_ip = QLineEdit(); txt_ip.setPlaceholderText("IP (fachada)")
        btn = QPushButton("INICIAR (simulado)")
        btn.clicked.connect(lambda: self._iniciar(dlg, txt_nombre.text(), txt_rival.text()))
        form.addRow("Tu nombre:", txt_nombre)
        form.addRow("Rival (simulado):", txt_rival)
        form.addRow("IP (fachada):", txt_ip)
        form.addRow(btn)
        dlg.exec()

    def _iniciar(self, dlg, nombre, rival):
        if not nombre:
            QMessageBox.warning(self, "Falta nombre", "Introduce tu nombre para iniciar.")
            return
        dlg.accept()
        if self.player:
            self.player.stop()
        self.app_window.iniciar_juego(nombre or "Jugador", rival or "Rival")

    def abrir_records(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("RECORDS - PIXEL KONG")
        dlg.setFixedSize(480,420)
        v = QVBoxLayout(dlg)
        lista = QListWidget()
        regs = cargar_records()
        if not regs:
            lista.addItem("Aún no hay records.")
        else:
            regs_sorted = sorted(regs, key=lambda r: r.get("puntos",0), reverse=True)
            for r in regs_sorted[:100]:
                lista.addItem(f"{r.get('nombre','?')} - {r.get('puntos',0)} pts - Nivel {r.get('nivel',1)}")
        v.addWidget(lista)
        btn = QPushButton("Cerrar"); btn.clicked.connect(dlg.accept); v.addWidget(btn)
        dlg.exec()

# ---------- JUEGO COMPLETO ----------
class JuegoWidget(QWidget):
    def __init__(self, app_window, nombre, rival):
        super().__init__()
        self.app_window = app_window
        self.nombre = nombre
        self.rival = rival

        # --- recursos ---
        self.pm_fondo = cargar_imagen("fondo.png", WINDOW_W, WINDOW_H)
        self.pm_donkey = cargar_imagen("donkey.png", 48, 48)
        self.pm_barril = cargar_imagen("barril.png", 28, 28)
        self.pm_cascara = cargar_imagen("cascara.png", 26, 22)
        self.pm_bomba = cargar_imagen("bomba.png", 30, 30)
        self.pm_power_inmune = cargar_imagen("power_inmune.png", 28, 28)
        self.pm_power_lento = cargar_imagen("power_lento.png", 28, 28)
        self.pm_power_salto = cargar_imagen("power_salto.png", 28, 28)
        self.pm_vida = cargar_imagen("vida.png", 24, 24)

        # --- estado jugador ---
        self.j_w, self.j_h = 40, 44
        self.jx, self.jy = 80.0, 460.0
        self.jvx, self.jvy = 0.0, 0.0
        self.salto_vel = -12.0
        self.gravedad = 0.7
        self.en_trepada = False

        self.key_left = self.key_right = False
        self.key_up = self.key_down = False
        self.key_space = False

        self.puntos = 0
        self.nivel = 1
        self.vidas = 3
        self.inmune = False

        # --- listas inicializadas ANTES ---
        self.plataformas = []
        self.escaleras = []
        self.obstaculos = []
        self.powerups = []

        # --- construir nivel ---
        self.construir_nivel()
        # --- timer principal que actualiza el juego ---
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus(Qt.OtherFocusReason)
        self.setAttribute(Qt.WA_InputMethodEnabled, True)
        self.grabKeyboard()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.bucle)
        self.timer.start(28)

        # --- timers adicionales ---
        self.spawn_timer = QTimer(self)
        self.spawn_timer.timeout.connect(self.generar_obstaculo)
        self.spawn_timer.start(1200)

        self.power_timer = QTimer(self)
        self.power_timer.timeout.connect(self.generar_powerup)
        self.power_timer.start(7000)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.timer.timeout.connect(lambda: self.setFocus())

        # --- audio de choque ---
        self.audio_player = QMediaPlayer(self)
        self.aout = QAudioOutput(self)
        self.audio_player.setAudioOutput(self.aout)
        ruta_choque = ASSETS / "choque.mp3"
        self.ruta_choque = ruta_choque if ruta_choque.exists() else None

        # --- temporizador auxiliar para power-ups ---
        self.timer_power_aux = QTimer(self)
        self.timer_power_aux.setSingleShot(True)
        self.timer_power_aux.timeout.connect(self.restaurar_velocidades)



    def construir_nivel(self):
            # Ejemplo simple: plataformas y escaleras
        self.plataformas = [
            QRect(0, 500, 960, 20),
            QRect(100, 400, 760, 20),
            QRect(0, 300, 960, 20),
            QRect(100, 200, 760, 20),
        ]
        self.escaleras = [
            QRect(150, 400, 40, 100),
            QRect(800, 300, 40, 100),
            ]

    def generar_obstaculo(self):
        # Barriles, cáscaras o bombas
        tipo = random.choice(["barril", "cascara", "bomba"])
        x = 0 if tipo == "barril" else random.randint(0, 900)
        y = 470  # nivel inferior
        self.obstaculos.append({"tipo": tipo, "x": x, "y": y, "vx": random.choice([2, 3])})

    def generar_powerup(self):
        tipo = random.choice(["inmune", "lento", "salto"])
        x = random.randint(50, 900)
        y = random.randint(50, 450)
        self.powerups.append({"tipo": tipo, "x": x, "y": y})

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pm_fondo)

        painter.drawPixmap(int(self.jx), int(self.jy), self.pm_donkey)

            # Dibujar plataformas
        painter.setBrush(QColor(100, 100, 100))
        for plat in self.plataformas:
            painter.drawRect(plat)

            # Dibujar escaleras
        painter.setBrush(QColor(180, 120, 0))
        for esc in self.escaleras:
            painter.drawRect(esc)

            # Dibujar obstáculos
        for obs in self.obstaculos:
            pm = self.pm_barril if obs["tipo"] == "barril" else self.pm_cascara if obs["tipo"] == "cascara" else self.pm_bomba
            painter.drawPixmap(int(obs["x"]), int(obs["y"]), pm)

            # Dibujar power-ups
        for p in self.powerups:
            pm = self.pm_power_inmune if p["tipo"] == "inmune" else self.pm_power_lento if p["tipo"]=="lento" else self.pm_power_salto
            painter.drawPixmap(int(p["x"]), int(p["y"]), pm)

            # HUD: puntos y vidas
        painter.setFont(QFont("Arial", 18))
        painter.setPen(Qt.white)
        painter.drawText(10, 30, f"Puntos: {self.puntos}  Nivel: {self.nivel}")
        for i in range(self.vidas):
            painter.drawPixmap(10 + i * 30, 40, self.pm_vida)

    def bucle(self):
            # Movimiento horizontal
        if self.key_left:
            self.jx -= 4
        if self.key_right:
            self.jx += 4

            # Gravedad
        self.jvy += self.gravedad
        self.jy += self.jvy

            # Colisión con plataformas
        on_platform = False
        pj_rect = QRect(int(self.jx), int(self.jy), self.j_w, self.j_h)
        for plat in self.plataformas:
            if pj_rect.intersects(plat) and self.jvy >= 0:
                self.jy = plat.top() - self.j_h
                self.jvy = 0
                on_platform = True

        #salto
        if self.key_space and on_platform:
            self.jvy = self.salto_vel

            # Limitar dentro de la pantalla
        self.jx = max(0, min(self.jx, WINDOW_W - self.j_w))
        self.jy = min(self.jy, WINDOW_H - self.j_h)

        self.update()

            # Mover obstáculos
        for obs in self.obstaculos:
            obs["x"] += obs["vx"]
            # Quitar los que salieron de pantalla
        self.obstaculos = [o for o in self.obstaculos if o["x"] < WINDOW_W]

            # Colisiones con obstáculos
        pj_rect = QRect(int(self.jx), int(self.jy), self.j_w, self.j_h)
        for obs in self.obstaculos[:]:
            obs_rect = QRect(int(obs["x"]), int(obs["y"]), 28, 28)
            if pj_rect.intersects(obs_rect) and not self.inmune:
                self.perder_vida()
                self.obstaculos.remove(obs)
                break

            # Colisiones con power-ups
        for p in self.powerups[:]:
            p_rect = QRect(p["x"], p["y"], 28, 28)
            if pj_rect.intersects(p_rect):
                self.aplicar_powerup(p["tipo"])
                self.powerups.remove(p)

            # Subir de nivel
        if self.jy < 10:
            self.subir_nivel()

    def perder_vida(self):
        self.vidas -= 1
        if self.vidas <= 0:
            QMessageBox.information(self, "Game Over", f"{self.nombre} perdió todas las vidas!")
            self.app_window.volver_menu()
        else:
            self.jx, self.jy = 80, 460

    def aplicar_powerup(self, tipo):
        if tipo == "inmune":
            self.inmune = True
            QTimer.singleShot(5000, lambda: setattr(self, 'inmune', False))

        elif tipo == "lento":
            # Reducir velocidad de obstáculos
            for o in self.obstaculos:
                o["vx"] *= 0.5

            # Programar restauración con temporizador propio
            self.timer_power_aux.start(5000)

        elif tipo == "salto":
            self.salto_vel = -18
            QTimer.singleShot(5000, lambda: setattr(self, 'salto_vel', -12))

    def restaurar_velocidades(self):
        for o in self.obstaculos:
            o["vx"] *= 2


    def subir_nivel(self):
        self.nivel += 1
        self.jx, self.jy = 80, 460
        self.obstaculos.clear()
        self.powerups.clear()
        QMessageBox.information(self, "Nivel Completado", f"¡Nivel {self.nivel}!")

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_A): self.key_left = True
        if event.key() in (Qt.Key_Right, Qt.Key_D): self.key_right = True
        if event.key() in (Qt.Key_Up, Qt.Key_W): self.key_up = True
        if event.key() in (Qt.Key_Down, Qt.Key_S): self.key_down = True
        if event.key() == Qt.Key_Space: self.key_space = True

    def keyReleaseEvent(self, event):
        if event.key() in (Qt.Key_Left, Qt.Key_A): self.key_left = False
        if event.key() in (Qt.Key_Right, Qt.Key_D): self.key_right = False
        if event.key() in (Qt.Key_Up, Qt.Key_W): self.key_up = False
        if event.key() in (Qt.Key_Down, Qt.Key_S): self.key_down = False
        if event.key() == Qt.Key_Space: self.key_space = False


# ---------- VENTANA PRINCIPAL ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PIXEL KONG")
        self.setFixedSize(WINDOW_W, WINDOW_H)
        self.menu = MenuWidget(self)
        self.setCentralWidget(self.menu)

    def iniciar_juego(self, nombre, rival):
        self.juego = JuegoWidget(self, nombre, rival)
        self.setCentralWidget(self.juego)
        self.juego.setFocus()

    def volver_menu(self):
        self.menu = MenuWidget(self)
        self.setCentralWidget(self.menu)

# ---------- EJECUTAR ----------
def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
