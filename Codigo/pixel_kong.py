import sys, random
from PySide6.QtCore import Qt, QTimer, QRect, Signal
from PySide6.QtGui import QPainter, QColor, QFont
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget,QMessageBox
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from Menu import MenuWidget
from Funciones import cargar_imagen, ASSETS, WINDOW_W, WINDOW_H

# ---------- JUEGO COMPLETO ----------
class JuegoWidget_servidor(QWidget):
    mensaje = Signal(str)
    def __init__(self, app_window, nombre, rival):
        super().__init__()
        self.app_window = app_window
        self.nombre = nombre
        self.rival = rival

        # --- recursos ---
        self.pm_fondo = cargar_imagen("fondo.png", WINDOW_W, WINDOW_H)
        self.pm_mario = cargar_imagen("mario.png", 30, 30)
        self.pm_rival = cargar_imagen("mario2.png", 30, 30)
        self.estrella = cargar_imagen("estrella.png", 20, 20)
        self.pm_barril = cargar_imagen("barril.png", 25, 25)
        self.pm_cascara = cargar_imagen("cascara.png", 25, 25)
        self.pm_bomba = cargar_imagen("bomba.png", 25, 25)
        self.pm_power_inmune = cargar_imagen("power_inmune.png", 28, 28)
        self.pm_power_lento = cargar_imagen("power_lento.png", 28, 28)
        self.pm_power_salto = cargar_imagen("power_salto.png", 28, 28)
        self.pm_vida = cargar_imagen("vida.png", 24, 24)

        # --- estado jugador ---
        self.j_w, self.j_h = 25, 30
        self.jx, self.jy = 80.0, 520.0
        self.jvx, self.jvy = 0.0, 0.0
        self.salto_vel = -10.0
        self.gravedad = 0.7

        self.key_left = self.key_right = False
        self.key_up = self.key_down = False
        self.key_up = False

        self.puntos = 0
        self.nivel = 1
        self.vidas = 3
        self.inmune = False

        # --- estado jugador 2 ---
        self.j2_w, self.j2_h = 25, 30
        self.j2x, self.j2y = 80.0, 520.0
        self.salto_vel_j2 = -10.0

        self.puntos_j2 = 0
        self.vidas_j2 = 3

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
        self.plataformas = [
            QRect(0, 600, 960, 20), #abajo
            QRect(0, 450, 760, 20), #enmedio abajo
            QRect(100, 300, 960, 20), #enmedio arriba
            QRect(0, 150, 760, 20), #arriba
        ]
        self.escaleras = [
            QRect(700, 450, 40, 150), #abajo
            QRect(150, 300, 40, 150), #enmedio
            QRect(700, 150, 40, 150)  #arriba
            ]

    def generar_obstaculo(self):
        # Barriles, cáscaras o bombas
        tipo = random.choice(["barril", "cascara", "bomba"])
        x = 0
        y = 120  # nivel superior
        vx = 2
        self.obstaculos.append({"tipo": tipo, "x": x, "y": y, "vx": vx})
        self.mensaje.emit(f"obs%{tipo}")

    def generar_powerup(self):
        tipo = random.choice(["inmune", "lento", "salto"])
        x = random.randint(50, 900)
        y = random.randint(50, 430)
        self.powerups.append({"tipo": tipo, "x": x, "y": y})
        self.mensaje.emit(f"pow%{tipo}%{x}%{y}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pm_fondo)

        painter.drawPixmap(int(self.jx), int(self.jy), self.pm_mario)
        painter.drawPixmap(int(self.j2x), int(self.j2y), self.pm_rival)

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

            #Dibujar estrella
        painter.drawPixmap(120,50, self.estrella)

            # HUD: puntos y vidas
        painter.setFont(QFont("Arial", 18))
        painter.setPen(Qt.white)
        painter.drawText(10, 30, f"Jugador 1:{self.nombre}  Puntos: {self.puntos}  Nivel: {self.nivel}")
        for i in range(self.vidas):
            painter.drawPixmap(10 + i * 30, 40, self.pm_vida)
        painter.drawText(500, 30, f"Jugador 1:{self.rival}  Puntos: {self.puntos_j2}")
        for i in range(self.vidas_j2):
            painter.drawPixmap(500 + i * 30, 40, self.pm_vida)

    def obstaculo_en_plataforma(self, obs):
        for plat in self.plataformas:
            distancia_y = plat.top() - (obs["y"] + 28)
            # Si el obstaculo esta encima de esa plataforma
            if -5 <= distancia_y <= 5:
                # Si el obstaculo esta horizontalmente en la plataforma
                if (obs["x"] + 28 > plat.left() and obs["x"] < plat.right()):
                    return True
        # Si esta cayendo, cambia de direccion
        if obs["y"] == 252:
            obs["vx"] *= -1
        elif obs["y"] == 400:
            obs["vx"] *= -1
        elif obs["y"] == 548:
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

            # Colisión con escaleras
        for escalera in self.escaleras:
            if pj_rect.intersects(escalera) and (self.key_up or self.key_up):
                self.jvy = -4

        #salto
        if self.key_up and on_platform:
            self.jvy = self.salto_vel

            # Limitar dentro de la pantalla
        self.jx = max(0, min(self.jx, WINDOW_W - self.j_w))
        self.jy = min(self.jy, WINDOW_H - self.j_h)

        self.update()

        self.mensaje.emit(f"pos{self.jx}%{self.jy}%{self.puntos}%{self.vidas}")

        # Mover obstáculos
        for obs in self.obstaculos:
            # Aplicar gravedad si no está en plataforma
            if not self.obstaculo_en_plataforma(obs):
                obs["y"] += 4  # Velocidad de caída
            else:
                # Si está en plataforma, mover horizontalmente según su dirección
                obs["x"] += obs["vx"]

            # Quitar los que salieron de la pantalla por los costados o abajo
            if (obs["x"] < -50 or obs["x"] > WINDOW_W + 50 or obs["y"] > WINDOW_H + 50):
                if obs in self.obstaculos:
                    self.obstaculos.remove(obs)

            # Colisiones y caida de obstáculos
        for obs in self.obstaculos[:]:
            obs_rect = QRect(int(obs["x"]), int(obs["y"]), 28, 28)
            if pj_rect.intersects(obs_rect) and not self.inmune:
                self.perder_vida(self.nombre)
                self.obstaculos.remove(obs)
                break

            # Colisiones con power-ups
        for p in self.powerups[:]:
            p_rect = QRect(p["x"], p["y"], 28, 28)
            if pj_rect.intersects(p_rect):
                self.aplicar_powerup(p["tipo"])
                self.powerups.remove(p)

            # Subir de nivel
        e_rect = QRect(120, 50, 20, 20)
        if pj_rect.intersects(e_rect):
            self.mensaje.emit("ganador")
            self.subir_nivel(self.nombre)

    def perder_vida(self, jugador):
        if jugador == self.nombre:
            self.vidas -= 1
            if self.vidas <= 0:
                QMessageBox.information(self, "Game Over", f"{self.nombre} perdió todas las vidas!")
                self.app_window.volver_menu()
            else:
                self.jx, self.jy = 80, 550
        else:
            QMessageBox.information(self, "Game Over", f"{self.rival} perdió todas las vidas!")
            self.app_window.volver_menu()

    def aplicar_powerup(self, tipo):
        self.puntos += 500
        if tipo == "inmune":
            self.inmune = True
            QTimer.singleShot(5000, lambda: setattr(self, 'inmune', False))

        elif tipo == "lento":
            # Reducir velocidad de obstáculos
            for o in self.obstaculos:
                o["vx"] /= 2

            # Programar restauración con temporizador propio
            self.timer_power_aux.start(5000)

        elif tipo == "salto":
            self.salto_vel = -12
            QTimer.singleShot(5000, lambda: setattr(self, 'salto_vel', -8))

    def restaurar_velocidades(self):
        for o in self.obstaculos:
            if o["vx"]>0:
                o["vx"] = 2
            else:
                o["vx"] = -2
        self.mensaje.emit("normal")

    def subir_nivel(self, jugador):
        self.nivel += 1
        self.jx, self.jy = 80, 550
        self.jx, self.jy = 80, 550
        self.obstaculos.clear()
        self.powerups.clear()
        QMessageBox.information(self, f"{jugador} completo el nivel", f"¡Nivel {self.nivel}!")

    def keyPressEvent(self, event):
        if event.key() == (Qt.Key_Left): self.key_left = True
        if event.key() == (Qt.Key_Right): self.key_right = True
        if event.key() == (Qt.Key_Up): self.key_up = True
        if event.key() == (Qt.Key_Down): self.key_down = True

    def keyReleaseEvent(self, event):
        if event.key() == (Qt.Key_Left): self.key_left = False
        if event.key() == (Qt.Key_Right): self.key_right = False
        if event.key() == (Qt.Key_Up): self.key_up = False
        if event.key() == (Qt.Key_Down): self.key_down = False

    def posicion_j2(self, posicion):
        #pos%{self.jx}%{self.jy}%{self.puntos}%{self.vidas}
        partes = posicion.split("%")
        self.j2x = float(partes[1])
        self.j2y = float(partes[2])
        self.puntos_j2 = int(partes[3])
        self.vidas_j2 = int(partes[4])
        if self.vidas_j2 == 0:
            self.perder_vida(self.rival)

    def recibir(self, msg):
        partes = msg.split("%")
        if partes[0] == "pos":
            self.posicion_j2(msg)
        elif partes[0] == "lento":
            self.aplicar_powerup(partes[0])
        elif partes[0] == "normal":
            self.restaurar_velocidades()
        elif partes[0] == "ganador":
            self.subir_nivel(self.rival)

class JuegoWidget_cliente(QWidget):
    mensaje = Signal(str)

    def __init__(self, app_window, nombre, rival):
        super().__init__()
        self.app_window = app_window
        self.nombre = nombre
        self.rival = rival

        # --- recursos ---
        self.pm_fondo = cargar_imagen("fondo.png", WINDOW_W, WINDOW_H)
        self.pm_mario = cargar_imagen("mario.png", 30, 30)
        self.pm_rival = cargar_imagen("mario2.png", 30, 30)
        self.estrella = cargar_imagen("estrella.png", 20, 20)
        self.pm_barril = cargar_imagen("barril.png", 25, 25)
        self.pm_cascara = cargar_imagen("cascara.png", 25, 25)
        self.pm_bomba = cargar_imagen("bomba.png", 25, 25)
        self.pm_power_inmune = cargar_imagen("power_inmune.png", 28, 28)
        self.pm_power_lento = cargar_imagen("power_lento.png", 28, 28)
        self.pm_power_salto = cargar_imagen("power_salto.png", 28, 28)
        self.pm_vida = cargar_imagen("vida.png", 24, 24)

        # --- estado jugador ---
        self.j_w, self.j_h = 25, 30
        self.jx, self.jy = 80.0, 520.0
        self.jvx, self.jvy = 0.0, 0.0
        self.salto_vel = -10.0
        self.gravedad = 0.7

        self.key_left = self.key_right = False
        self.key_up = self.key_down = False

        self.puntos = 0
        self.nivel = 1
        self.vidas = 3
        self.inmune = False

        # --- estado jugador 2 ---
        self.j2_w, self.j2_h = 25, 30
        self.j2x, self.j2y = 80.0, 520.0
        self.salto_vel_j2 = -10.0

        self.puntos_j2 = 0
        self.vidas_j2 = 3

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

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.timer.timeout.connect(lambda: self.setFocus())

        # --- audio de choque ---
        self.audio_player = QMediaPlayer(self)
        self.aout = QAudioOutput(self)
        self.audio_player.setAudioOutput(self.aout)
        ruta_choque = ASSETS / "choque.mp3"
        self.ruta_choque = ruta_choque if ruta_choque.exists() else None

    def construir_nivel(self):
        self.plataformas = [
            QRect(0, 600, 960, 20),  # abajo
            QRect(0, 450, 760, 20),  # enmedio abajo
            QRect(100, 300, 960, 20),  # enmedio arriba
            QRect(0, 150, 760, 20),  # arriba
        ]
        self.escaleras = [
            QRect(700, 450, 40, 150),  # abajo
            QRect(150, 300, 40, 150),  # enmedio
            QRect(700, 150, 40, 150)  # arriba
        ]

    def generar_obstaculo(self, tipo):
        # Barriles, cáscaras o bombas
        x = 0
        y = 120  # nivel superior
        vx = 2
        self.obstaculos.append({"tipo": tipo, "x": x, "y": y, "vx": vx})

    def generar_powerup(self, pow):
        partes = pow.split("%")
        tipo = partes[1]
        x = partes[2]
        y = partes[3]
        self.powerups.append({"tipo": tipo, "x": x, "y": y})

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.pm_fondo)

        painter.drawPixmap(int(self.jx), int(self.jy), self.pm_mario)
        painter.drawPixmap(int(self.j2x), int(self.j2y), self.pm_rival)

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
            pm = self.pm_barril if obs["tipo"] == "barril" else self.pm_cascara if obs[
                                                                                       "tipo"] == "cascara" else self.pm_bomba
            painter.drawPixmap(int(obs["x"]), int(obs["y"]), pm)

            # Dibujar power-ups
        for p in self.powerups:
            pm = self.pm_power_inmune if p["tipo"] == "inmune" else self.pm_power_lento if p[
                                                                                               "tipo"] == "lento" else self.pm_power_salto
            painter.drawPixmap(int(p["x"]), int(p["y"]), pm)

            # Dibujar estrella
        painter.drawPixmap(100, 30, self.estrella)

            # HUD: puntos y vidas
        painter.setFont(QFont("Arial", 18))
        painter.setPen(Qt.white)
        painter.drawText(10, 30, f"Jugador 1:{self.nombre}  Puntos: {self.puntos}  Nivel: {self.nivel}")
        for i in range(self.vidas):
            painter.drawPixmap(10 + i * 30, 40, self.pm_vida)
        painter.drawText(500, 30, f"Jugador 1:{self.rival}  Puntos: {self.puntos_j2}")
        for i in range(self.vidas_j2):
            painter.drawPixmap(500 + i * 30, 40, self.pm_vida)

    def obstaculo_en_plataforma(self, obs):
        for plat in self.plataformas:
            distancia_y = plat.top() - (obs["y"] + 28)
            # Si el obstaculo esta encima de esa plataforma
            if -5 <= distancia_y <= 5:
                # Si el obstaculo esta horizontalmente en la plataforma
                if (obs["x"] + 28 > plat.left() and obs["x"] < plat.right()):
                    return True
        # Si esta cayendo, cambia de direccion
        if obs["y"] == 252:
            obs["vx"] *= -1
        elif obs["y"] == 400:
            obs["vx"] *= -1
        elif obs["y"] == 548:
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

            # Colisión con escaleras
        for escalera in self.escaleras:
            if pj_rect.intersects(escalera) and (self.key_up or self.key_up):
                self.jvy = -4

        #salto
        if self.key_up and on_platform:
            self.jvy = self.salto_vel

            # Limitar dentro de la pantalla
        self.jx = max(0, min(self.jx, WINDOW_W - self.j_w))
        self.jy = min(self.jy, WINDOW_H - self.j_h)

        self.update()

        self.mensaje.emit(f"pos{self.jx}%{self.jy}%{self.puntos}%{self.vidas}")

        # Mover obstáculos
        for obs in self.obstaculos:
            # Aplicar gravedad si no está en plataforma
            if not self.obstaculo_en_plataforma(obs):
                obs["y"] += 4  # Velocidad de caída
            else:
                # Si está en plataforma, mover horizontalmente según su dirección
                obs["x"] += obs["vx"]

            # Quitar los que salieron de la pantalla por los costados o abajo
            if (obs["x"] < -50 or obs["x"] > WINDOW_W + 50 or obs["y"] > WINDOW_H + 50):
                if obs in self.obstaculos:
                    self.obstaculos.remove(obs)

            # Colisiones y caida de obstáculos
        for obs in self.obstaculos[:]:
            obs_rect = QRect(int(obs["x"]), int(obs["y"]), 28, 28)
            if pj_rect.intersects(obs_rect) and not self.inmune:
                self.perder_vida(self.nombre)
                self.obstaculos.remove(obs)
                break

            # Colisiones con power-ups
        for p in self.powerups[:]:
            p_rect = QRect(p["x"], p["y"], 28, 28)
            if pj_rect.intersects(p_rect):
                self.aplicar_powerup(p["tipo"])
                self.powerups.remove(p)

            # Subir de nivel
        e_rect = QRect(120, 50, 20, 20)
        if pj_rect.intersects(e_rect):
            self.mensaje.emit("ganador")
            self.subir_nivel(self.nombre)

    def perder_vida(self, jugador):
        if jugador == self.nombre:
            self.vidas -= 1
            if self.vidas <= 0:
                QMessageBox.information(self, "Game Over", f"{self.nombre} perdió todas las vidas!")
                self.app_window.volver_menu()
            else:
                self.jx, self.jy = 80, 550
        else:
            QMessageBox.information(self, "Game Over", f"{self.rival} perdió todas las vidas!")
            self.app_window.volver_menu()

    def aplicar_powerup(self, tipo):
        self.puntos += 500
        if tipo == "inmune":
            self.inmune = True
            QTimer.singleShot(5000, lambda: setattr(self, 'inmune', False))

        elif tipo == "lento":
            # Reducir velocidad de obstáculos
            for o in self.obstaculos:
                o["vx"] /= 2

            # Programar restauración con temporizador propio
            self.timer_power_aux.start(5000)

        elif tipo == "salto":
            self.salto_vel = -12
            QTimer.singleShot(5000, lambda: setattr(self, 'salto_vel', -8))

    def restaurar_velocidades(self):
        for o in self.obstaculos:
            if o["vx"] > 0:
                o["vx"] = 2
            else:
                o["vx"] = -2
        self.mensaje.emit("normal")

    def subir_nivel(self, jugador):
        self.nivel += 1
        self.jx, self.jy = 80, 550
        self.obstaculos.clear()
        self.powerups.clear()
        QMessageBox.information(self, f"{jugador} completo el nivel", f"¡Nivel {self.nivel}!")

    def keyPressEvent(self, event):
        if event.key() == (Qt.Key_Left): self.key_left = True
        if event.key() == (Qt.Key_Right): self.key_right = True
        if event.key() == (Qt.Key_Up): self.key_up = True
        if event.key() == (Qt.Key_Down): self.key_down = True

    def keyReleaseEvent(self, event):
        if event.key() == (Qt.Key_Left): self.key_left = False
        if event.key() == (Qt.Key_Right): self.key_right = False
        if event.key() == (Qt.Key_Up): self.key_up = False
        if event.key() == (Qt.Key_Down): self.key_down = False

    def posicion_j2(self, posicion):
        # pos%{self.jx}%{self.jy}%{self.puntos}%{self.vidas}
        partes = posicion.split("%")
        self.j2x = float(partes[1])
        self.j2y = float(partes[2])
        self.puntos_j2 = int(partes[3])
        self.vidas_j2 = int(partes[4])
        if self.vidas_j2 == 0:
            self.perder_vida(self.rival)

    def recibir(self, msg):
        partes = msg.split("%")
        if partes[0] == "pos":
            self.posicion_j2(msg)
        elif partes[0] == "obs":
            self.generar_obstaculo(partes[1])
        elif partes[0] == "pow":
            self.generar_powerup(msg)
        elif partes[0] == "lento":
            self.aplicar_powerup(partes[0])
        elif partes[0] == "normal":
            self.restaurar_velocidades()
        elif partes[0] == "ganador":
            self.subir_nivel(self.rival)


# ---------- VENTANA PRINCIPAL ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PIXEL KONG")
        self.setFixedSize(WINDOW_W, WINDOW_H)
        self.menu = MenuWidget(self)
        self.setCentralWidget(self.menu)
        self.menu.pantalla.connect(self.recibir_mensaje_cliente)
        self.menu.posicion.connect(self.recibir_mensaje_servidor)

    def iniciar_juego(self, nombre, rival, rol):
        if rol == "SERVIDOR":
            self.juego = JuegoWidget_servidor(self, nombre, rival)
            self.juego.mensaje.connect(lambda msg: self.menu.mand_msg_serv(msg))
        else:
            self.juego = JuegoWidget_cliente(self, nombre, rival)
            self.juego.mensaje.connect(lambda msg: self.menu.mand_msg_clien(msg))
        self.setCentralWidget(self.juego)
        self.juego.setFocus()

    def recibir_mensaje_servidor(self, msg):
        self.juego.recibir(msg)

    def recibir_mensaje_cliente(self, msg):
        self.juego.recibir(msg)

    def volver_menu(self):
        self.menu = MenuWidget(self)
        self.setCentralWidget(self.menu)
        self.menu.pantalla.connect(self.recibir_mensaje_cliente)
        self.menu.posicion.connect(self.recibir_mensaje_servidor)


app = QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec())