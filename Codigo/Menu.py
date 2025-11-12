from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QDialog, \
    QFormLayout, QLineEdit, QMessageBox, QListWidget
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from Funciones import cargar_imagen, cargar_records, ASSETS, WINDOW_W, WINDOW_H, RECORDS_FILE

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
        dlg.setStyleSheet("color: white;")
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
