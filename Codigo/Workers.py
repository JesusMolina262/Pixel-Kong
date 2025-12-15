import socket
from threading import Thread
from PySide6.QtCore import QObject, Signal

class Conexion_serv(QObject):
    cliente_conectado = Signal(str)
    error = Signal(str)
    mensaje = Signal(str)

    def __init__(self, nombre):
        super().__init__()
        self.socket_servidor = socket.socket()
        self.conexion = None
        self.nombre = nombre
        self.buffer = ""

    def iniciar_servidor(self):
        try:
            self.socket_servidor.bind(("", 5050))
            self.socket_servidor.listen(1)

            self.conexion, addr = self.socket_servidor.accept()
            self.conexion.send(f"CONEXION:{self.nombre}\n".encode('utf-8'))
            self.cliente_conectado.emit("CONEXION, ya se puede iniciar la partida")
            Thread(target=self.escucha_servidor, daemon=True).start()
        except Exception as e:
            print(e)
            self.socket_servidor.close()
            self.error.emit(e)

    def mandar_servidor(self, msg):
        try:
            msg = msg + "\n"
            self.conexion.send(msg.encode('utf-8'))
        except Exception as e:
            print(e)
            self.socket_servidor.close()
            self.error.emit(e)

    def escucha_servidor(self):
        try:
            while True:
                msg = self.conexion.recv(1024).decode('utf-8')
                if not msg:
                    break
                self.buffer += msg

                # Procesar todos los mensajes completos en el buffer
                while '\n' in self.buffer:
                    # Separar el primer mensaje completo
                    msg, self.buffer = self.buffer.split('\n', 1)
                    if msg:  # Ignorar líneas vacías
                        self.mensaje.emit(msg)

        except Exception as e:
            print(e)
            self.socket_servidor.close()
            self.error.emit(e)

class Conexion_clien(QObject):
    cliente_conectado = Signal(str)
    error = Signal(str)
    mensaje = Signal(str)
    iniciar_juego = Signal()

    def __init__(self, ip, nombre):
        super().__init__()
        self.socket_cliente = None
        self.nombre = nombre
        self.ip = ip
        self.buffer = ""

    def iniciar_cliente_rec(self):
        try:
            self.socket_cliente = socket.socket()
            self.socket_cliente.connect((self.ip, 5050))
            msg = self.socket_cliente.recv(1024).decode('utf-8')
            self.buffer += msg

            # Procesar mensaje de conexión
            if '\n' in self.buffer:
                msg, self.buffer = self.buffer.split('\n', 1)
                if msg[:8] == "CONEXION":
                    self.cliente_man(f"CONEXION:{self.nombre}")
                    self.cliente_conectado.emit(msg + " Esperando a iniciar la partida")
                    Thread(target=self.escucha_cliente, daemon=True).start()

        except Exception as e:
            print(e)
            self.socket_cliente.close()
            self.error.emit(e)

    def escucha_cliente(self):
        try:
            while True:
                msg = self.socket_cliente.recv(1024).decode('utf-8')
                if not msg:
                    break  # Conexión cerrada

                self.buffer += msg

                # Procesar todos los mensajes completos en el buffer
                while '\n' in self.buffer:
                    # Separar el primer mensaje completo
                    msg, self.buffer = self.buffer.split('\n', 1)
                    if msg:  # Ignorar líneas vacías
                        if msg == "INICIO":
                            self.iniciar_juego.emit()
                        else:
                            self.mensaje.emit(msg)
        except Exception as e:
            print(e)
            self.socket_cliente.close()
            self.error.emit(e)

    def cliente_man(self, msg):
        try:
            msg = msg + "\n"
            self.socket_cliente.send(msg.encode('utf-8'))
        except Exception as e:
            print(e)
            self.socket_cliente.close()
            self.error.emit(e)