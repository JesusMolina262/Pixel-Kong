import sys, random
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget,QMessageBox
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from Menu import MenuWidget
from Funciones import cargar_imagen, ASSETS, WINDOW_W, WINDOW_H

# ---------- JUEGO COMPLETO ----------
class JuegoWidget_servidor(QWidget):
    obstaculo = Signal(dict)
    powerup = Signal(dict)
    def __init__(self, app_window, nombre, rival):
        super().__init__()
        self.app_window = app_window
        self.nombre = nombre
        self.rival = rival

        # --- recursos ---
        self.pm_fondo = cargar_imagen("fondo.png", WINDOW_W, WINDOW_H)
        self.pm_mario = cargar_imagen("mario.png", 30, 30)
        self.pm_rival = cargar_imagen("mario2.png", 30, 30)
        self.pm_barril = cargar_imagen("barril.png", 28, 28)
        self.pm_cascara = cargar_imagen("cascara.jpg", 26, 22)
        self.pm_bomba = cargar_imagen("bomba.png", 30, 30)
        self.pm_power_inmune = cargar_imagen("power_inmune.png", 28, 28)
        self.pm_power_lento = cargar_imagen("power_lento.png", 28, 28)
        self.pm_power_salto = cargar_imagen("power_salto.png", 28, 28)
        self.pm_vida = cargar_imagen("vida.png", 24, 24)

        # --- estado jugador ---
        self.j_w, self.j_h = 25, 30
        self.jx, self.jy = 80.0, 460.0
        self.jvx, self.jvy = 0.0, 0.0
        self.salto_vel = -8.0
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
        self.spawn_timer.start(3000)

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
            QRect(0, 500, 960, 20), #abajo
            QRect(0, 400, 760, 20), #enmedio abajo
            QRect(100, 300, 960, 20), #enmedio arriba
            QRect(0, 200, 760, 20), #arriba
        ]
        self.escaleras = [
            QRect(150, 400, 40, 100), #abajo
            QRect(700, 300, 40, 100), #arriba
            ]

    def generar_obstaculo(self):
        # Barriles, cáscaras o bombas
        tipo = random.choice(["barril", "cascara", "bomba"])
        x = 0
        y = 170  # nivel superior
        vx = 2
        self.obstaculos.append({"tipo": tipo, "x": x, "y": y, "vx": vx})
        self.obstaculo.emit({"tipo": tipo, "x": x, "y": y, "vx": vx}) #emitir al cliente un nuevo obstaculo

    def generar_powerup(self):
        tipo = random.choice(["inmune", "lento", "salto"])
        x = random.randint(50, 900)
        y = random.randint(50, 450)
        self.powerups.append({"tipo": tipo, "x": x, "y": y})
        self.powerup.emit({"tipo": tipo, "x": x, "y": y}) #emitir al cliente un nuevo power up

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pm_fondo)

        painter.drawPixmap(int(self.jx), int(self.jy), self.pm_mario)

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

    def obstaculo_en_plataforma(self, obs):
        for plat in self.plataformas:
            distancia_y = plat.top() - (obs["y"] + 28)
            # Si el obstaculo esta encima de esa plataforma
            if -5 <= distancia_y <= 5:
                # Si el obstaculo esta horizontalmente en la plataforma
                if (obs["x"] + 28 > plat.left() and obs["x"] < plat.right()):
                    return True
        obs["vx"] *= -1
        return False

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

        # Mover obstáculos CON GRAVEDAD Y DETECCIÓN DE PLATAFORMAS
        for obs in self.obstaculos:
            # Aplicar gravedad si no está en plataforma
            if not self.obstaculo_en_plataforma(obs):
                obs["y"] += 4  # Velocidad de caída
            else:
                # Si está en plataforma, mover horizontalmente según su dirección
                obs["x"] += obs["vx"]

            # Quitar los que salieron de la pantalla por los costados o abajo
            if (obs["x"] < -50 or obs["x"] > WINDOW_W + 50 or
                    obs["y"] > WINDOW_H + 50):
                if obs in self.obstaculos:
                    self.obstaculos.remove(obs)

            # Colisiones y caida de obstáculos
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

class JuegoWidget_cliente(QWidget):
    obstaculo = Signal(dict)
    powerup = Signal(dict)
    def __init__(self, app_window, nombre, rival):
        super().__init__()
        self.app_window = app_window
        self.nombre = nombre
        self.rival = rival

        # --- recursos ---
        self.pm_fondo = cargar_imagen("fondo.png", WINDOW_W, WINDOW_H)
        self.pm_mario = cargar_imagen("mario.png", 30, 30)
        self.pm_rival = cargar_imagen("mario2.png", 30, 30)
        self.pm_barril = cargar_imagen("barril.png", 28, 28)
        self.pm_cascara = cargar_imagen("cascara.png", 26, 22)
        self.pm_bomba = cargar_imagen("bomba.png", 30, 30)
        self.pm_power_inmune = cargar_imagen("power_inmune.png", 28, 28)
        self.pm_power_lento = cargar_imagen("power_lento.png", 28, 28)
        self.pm_power_salto = cargar_imagen("power_salto.png", 28, 28)
        self.pm_vida = cargar_imagen("vida.png", 24, 24)

        # --- estado jugador ---
        self.j_w, self.j_h = 25, 30
        self.jx, self.jy = 80.0, 460.0
        self.jvx, self.jvy = 0.0, 0.0
        self.salto_vel = -8.0
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
        self.spawn_timer.start(3000)

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
            QRect(0, 500, 960, 20), #abajo
            QRect(0, 400, 760, 20), #enmedio abajo
            QRect(100, 300, 960, 20), #enmedio arriba
            QRect(0, 200, 760, 20), #arriba
        ]
        self.escaleras = [
            QRect(150, 400, 40, 100), #abajo
            QRect(700, 300, 40, 100), #arriba
            ]

    def generar_obstaculo(self,tipo, x, y, vx):
        self.obstaculos.append({"tipo": tipo, "x": x, "y": y, "vx": vx})

    def generar_powerup(self, tipo, x, y):
        self.powerups.append({"tipo": tipo, "x": x, "y": y})

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pm_fondo)

        painter.drawPixmap(int(self.jx), int(self.jy), self.pm_mario)

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

    def iniciar_juego(self, nombre, rival, rol):
        if rol == "SERVIDOR":
            self.juego = JuegoWidget_servidor(self, nombre, rival)
        else:
            self.juego = JuegoWidget_cliente(self, nombre, rival)
        self.setCentralWidget(self.juego)
        self.juego.setFocus()

    def volver_menu(self):
        self.menu = MenuWidget(self)
        self.setCentralWidget(self.menu)


app = QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec())