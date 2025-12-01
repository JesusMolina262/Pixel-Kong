import socket
from threading import Thread
from PySide6.QtCore import QObject, Signal


class Conexion_serv(QObject):
    cliente_conectado = Signal(str)
    error = Signal(str)
    movimiento = Signal(str)

    def __init__(self):
        super().__init__()
        self.socket_servidor = socket.socket()

        self.conn = None

    def iniciar_servidor(self):
        try:
            self.socket_servidor.bind(("", 5050))
            self.socket_servidor.listen(1)
            conn, addr = self.socket_servidor.accept()
            conn.send("CONEXION".encode('utf-8'))
            self.cliente_conectado.emit("cliente conectado")
            self.conexion = conn
            Thread(target=self.escucha_servidor, daemon=True).start()
        except Exception as e:
            self.socket_servidor.close()
            self.error.emit(e)

    def mandar_servidor(self, msg):
        try:
            self.conn.send(msg.encode())
        except Exception as e:
            self.socket_servidor.close()
            self.error.emit(e)

    def escucha_servidor(self):
        try:
            while True:
                msg = self.conexion.recv(1024).decode('utf-8')
                self.movimiento.emit(msg)
        except Exception as e:
            self.socket_servidor.close()
            self.error.emit(e)

class Conexion_clien(QObject):
    cliente_conectado = Signal(str)
    error = Signal(str)
    pantalla = Signal(str)

    def __init__(self, ip, nombre):
        super().__init__()
        self.socket_cliente = None
        self.nombre = nombre
        self.ip = ip

    def iniciar_cliente_rec(self):
        try:
            self.socket_cliente = socket.socket()
            self.socket_cliente.connect((self.ip, 5050))
            msg = self.socket_cliente.recv(1024).decode('utf-8')
            if msg == "CONEXION":
                self.cliente_man(self.nombre)
                self.cliente_conectado.emit(msg)
                Thread(target=self.escucha_cliente, daemon=True)
        except Exception as e:
            self.socket_cliente.close()
            self.error.emit(e)

    def escucha_cliente(self):
        try:
            while True:
                msg = self.socket_cliente.recv(1024).decode()
                self.pantalla.emit(msg)
        except Exception as e:
            self.socket_cliente.close()
            self.error.emit(e)

    def cliente_man(self, msg):
        try:
            self.socket_cliente.send(msg.encode())
        except Exception as e:
            self.socket_cliente.close()
            self.error.emit(e)
