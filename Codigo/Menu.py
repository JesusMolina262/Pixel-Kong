from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QDialog, QListWidget, QHBoxLayout
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from Funciones import cargar_imagen, cargar_records, ASSETS, WINDOW_W, WINDOW_H

class MenuWidget(QWidget):
    jugador = Signal(str)
    def __init__(self, app_window):
        super().__init__()
        self.app_window = app_window
        self.init_ui()
        self.init_audio()
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
        btn_servidor.clicked.connect(lambda: self.jugador.emit("SERVIDOR"))
        btn_servidor.clicked.connect(dlg.accept)

        btn_cliente = QPushButton("Cliente")
        btn_cliente.clicked.connect(lambda: self.jugador.emit("CLIENTE"))
        btn_cliente.clicked.connect(dlg.accept)

        cbv.addWidget(txt_pregunta)
        cbh.addWidget(btn_servidor)
        cbh.addWidget(btn_cliente)
        cbv.addLayout(cbh)
        dlg.exec()

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

