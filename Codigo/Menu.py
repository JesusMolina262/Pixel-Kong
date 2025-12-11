from PySide6.QtCore import Qt, QUrl, QThread
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QDialog, \
    QFormLayout, QLineEdit, QMessageBox, QListWidget, QHBoxLayout
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from Funciones import cargar_imagen, cargar_records, ASSETS, WINDOW_W, WINDOW_H, RECORDS_FILE
import socket
from Workers import Conexion_serv, Conexion_clien

class MenuWidget(QWidget):
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.init_ui()
        self.init_audio()
        self.hilo_servidor = None
        self.hilo_cliente = None
        self.lbl_cliente = None
        self.nombre_contrario = ""

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

        btn_jugar.clicked.connect(self.elegir_s_c)
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

    def elegir_s_c(self):
        dlg = QDialog(self)
        dlg.setStyleSheet("color: white;")
        dlg.setWindowTitle("Servidor o cliente")
        dlg.setFixedSize(360,180)
        cbv = QVBoxLayout(dlg)
        cbh = QHBoxLayout()
        txt_pregunta = QLabel("Vas a ser el Servidor o el cliente?")

        btn_servidor = QPushButton("Servidor")
        btn_servidor.clicked.connect(self.abrir_fachada_servidor)
        btn_servidor.clicked.connect(dlg.accept)

        btn_cliente = QPushButton("Cliente")
        btn_cliente.clicked.connect(self.abrir_fachada_cliente)
        btn_cliente.clicked.connect(dlg.accept)

        cbv.addWidget(txt_pregunta)
        cbh.addWidget(btn_servidor)
        cbh.addWidget(btn_cliente)
        cbv.addLayout(cbh)
        dlg.exec()

    def abrir_fachada_servidor(self):
        dlg = QDialog(self)
        dlg.setStyleSheet("color: white;")
        dlg.setWindowTitle("Crear sala")
        dlg.setFixedSize(360,220)

        form = QFormLayout(dlg)
        txt_nombre = QLineEdit(); txt_nombre.setPlaceholderText("Tu nombre")
        lbl_ip = QLabel()
        lbl_ip.setText(socket.gethostbyname(socket.gethostname()))
        self.lbl_cliente = QLabel("Esperando conexion...")
        btn = QPushButton("INICIAR")
        btn.clicked.connect(lambda: self.verificacion_serv(txt_nombre.text(), self.lbl_cliente.text(), "SERVIDOR"))
        self.iniciar_hilo_rec_servidor()
        form.addRow("Tu nombre:", txt_nombre)
        form.addRow("IP:", lbl_ip)
        form.addRow(self.lbl_cliente)
        form.addRow(btn)
        dlg.exec()

    def iniciar_hilo_rec_servidor(self):
        self.hilo_servidor_man = QThread()
        self.conexion_s = Conexion_serv()
        self.conexion_s.moveToThread(self.hilo_servidor_man)
        self.hilo_servidor_man.started.connect(self.conexion_s.iniciar_servidor)
        self.conexion_s.cliente_conectado.connect(self.cambiar_lbl)
        self.conexion_s.movimiento.connect(self.escucha_serv)
        self.conexion_s.error.connect(self.error)
        self.hilo_servidor_man.start()

    def verificacion_serv(self, jugador, texto, rol):
        if not jugador:
            QMessageBox.warning(self, "Falta algun campo", "Llena todos los campos para iniciar")
            return
        if texto != "CONEXION, ya se puede iniciar la partida":
            QMessageBox.warning(self, "Aun no se conecta el rival", "Espera a que tu contrincante se una a la partida para iniciar")
            return
        if hasattr(self, 'conexion_s') and self.conexion_s:
            try:
                self.conexion_s.mandar_servidor("INICIO")
            except:
                pass
        if self.player:
            self.player.stop()
        self.app_window.iniciar_juego(jugador, self.nombre_contrario , rol)


    def escucha_serv(self, msg):
        if msg[:8] == "CONEXION":
            self.nombre_contrario = msg[9:]
        print("servidor escucho:", msg)

    def escucha_cliente(self, msg):
        print("cliente escucho:", msg)

    def mand_pantalla(self, msg):
        self.conexion_s.mandar_servidor(msg)

    def cambiar_lbl(self, mensaje):
        self.lbl_cliente.setText(mensaje)

    def abrir_fachada_cliente(self):
        dlg = QDialog(self)
        dlg.setStyleSheet("color: white;")
        dlg.setWindowTitle("Crear/Unirse a sala")
        dlg.setFixedSize(360,220)
        form = QFormLayout(dlg)
        txt_nombre = QLineEdit(); txt_nombre.setPlaceholderText("Tu nombre")
        txt_ip = QLineEdit(); txt_ip.setPlaceholderText("IP (rival)")
        self.lbl_cliente = QLabel("Esperando conexion...")
        btn = QPushButton("INICIAR")
        btn.clicked.connect(lambda: self.verificacion_cliente(txt_nombre.text(), txt_ip.text()))
        form.addRow("Tu nombre:", txt_nombre)
        form.addRow("IP:", txt_ip)
        form.addRow(self.lbl_cliente)
        form.addRow(btn)
        dlg.exec()

    def iniciar_hilo_rec_cliente(self, nombre, ip):
        self.hilo_cliente = QThread()
        self.conexion_c = Conexion_clien(ip, nombre)
        self.conexion_c.moveToThread(self.hilo_cliente)
        self.hilo_cliente.started.connect(self.conexion_c.iniciar_cliente_rec)
        self.conexion_c.pantalla.connect(self.escucha_cliente)
        self.conexion_c.cliente_conectado.connect(self.cambiar_lbl)
        self.conexion_c.iniciar_juego.connect(lambda: self.iniciar_juego(nombre, "Servidor", "CLIENTE"))
        self.conexion_c.error.connect(self.error)
        self.hilo_cliente.start()

    def verificacion_cliente(self, nombre, ip):
        if not nombre or not ip:
            QMessageBox.warning(self, "Falta algun campo", "Llena todos los campos para iniciar.")
            return
        self.iniciar_hilo_rec_cliente(nombre, ip)

    def iniciar_juego(self, jugador, rival, rol):
        if self.player:
            self.player.stop()
        self.app_window.iniciar_juego(jugador, rival, rol)

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

    def error(self, error):
        print(f"ocurrio un error: {error}")

    def closeEvent(self, event):
        if not self.hilo_cliente:
            self.hilo_cliente.quit()
            self.hilo_cliente.wait()

        if not self.hilo_servidor:
            self.hilo_servidor.quit()
            self.hilo_servidor.wait()

        if not self.hilo_servidor:
            self.hilo_servidor.quit()
            self.hilo_servidor.wait()
