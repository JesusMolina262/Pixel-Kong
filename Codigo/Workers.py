import socket
from threading import Thread
from PySide6.QtCore import QObject, Signal


class Conexion_serv(QObject):
    cliente_conectado = Signal(str)
    error = Signal(str)
    mensaje = Signal(str) #para la comunicacion
    conexion_cerrada = Signal()

    def __init__(self, nombre):
        super().__init__()
        self.socket_servidor = socket.socket()
        self.conexion = None
        self.nombre = nombre
        self.buffer = "" #por si los mensajes se envian en partes o juntos
        self.conectado = True

    def iniciar_servidor(self):
        try:
            self.socket_servidor.settimeout(1)  # Timeout para accept
            self.socket_servidor.bind(("", 5050))
            self.socket_servidor.listen(1)

            while self.conectado:
                try:
                    self.conexion, addr = self.socket_servidor.accept()
                    self.conexion.settimeout(0.5)
                    break
                except socket.timeout:
                    continue
                except:
                    break

            if self.conexion: #si se conecto
                self.conexion.send(f"CONEXION\n".encode('utf-8'))
                self.cliente_conectado.emit("CONEXION, ya se puede iniciar la partida")
                Thread(target=self.escucha_servidor, daemon=True).start() #hilo demonio para no tener que "matarlo"
            else:
                self.error.emit("No se pudo establecer conexión")

        except Exception as e:
            if self.socket_servidor:
                self.socket_servidor.close() #cerrar la conexion
            self.error.emit(str(e))

    def mandar_servidor(self, msg):
        if not self.conectado or not self.conexion:
            return

        try:
            msg = msg + "\n" #salto de linea para que el buffer lo entienda como un mensaje
            self.conexion.send(msg.encode('utf-8'))
        except Exception as e:
            self.conectado = False
            if self.socket_servidor:
                self.socket_servidor.close()
            self.error.emit("ERROR_CLIENTE_CAIDO")

    def escucha_servidor(self):
        try:
            while self.conectado:
                try:
                    msg = self.conexion.recv(1024).decode('utf-8')
                    if not msg:
                        break

                    self.buffer += msg

                    # Procesar todos los mensajes completos en el buffer
                    while '\n' in self.buffer:
                        msg, self.buffer = self.buffer.split('\n', 1)
                        if msg:
                            if msg == "DESCONEXION":
                                self.conectado = False
                                break
                            self.mensaje.emit(msg)

                except socket.timeout:
                    continue  # timeout normal, continuar escuchando
                except:
                    break  # error real

        except:
            pass
        finally:
            #se cierra toda conexion
            self.cerrar()
            self.error.emit("Cliente desconectado")
            self.conexion_cerrada.emit()

    def cerrar(self):
        self.conectado = False
        if self.conexion:
            self.conexion.close()
        if self.socket_servidor:
            self.socket_servidor.close()


class Conexion_clien(QObject):
    cliente_conectado = Signal(str)
    error = Signal(str)
    mensaje = Signal(str) #para toda la comunicacion
    iniciar_juego = Signal()
    conexion_cerrada = Signal()

    def __init__(self, ip, nombre):
        super().__init__()
        self.socket_cliente = None
        self.nombre = nombre
        self.ip = ip
        self.buffer = "" #por si los mensajes se envian por partes o juntos
        self.conectado = True

    def iniciar_cliente_rec(self):
        try:
            self.socket_cliente = socket.socket()
            self.socket_cliente.settimeout(5)  # timeout para conexión
            self.socket_cliente.connect((self.ip, 5050))
            self.socket_cliente.settimeout(0.5)  # timeout más corto para recv

            msg = self.socket_cliente.recv(1024).decode('utf-8')
            self.buffer += msg

            if '\n' in self.buffer:
                msg, self.buffer = self.buffer.split('\n', 1)
                if msg[:8] == "CONEXION":
                    self.cliente_man(f"CONEXION:{self.nombre}")
                    self.cliente_conectado.emit(msg + " Esperando a iniciar la partida")
                    Thread(target=self.escucha_cliente, daemon=True).start() #hilo demonio para no tener que "matarlo"

        except socket.timeout:
            self.error.emit("Timeout de conexión")
        except ConnectionRefusedError:
            self.error.emit("No se pudo conectar al servidor")
        except Exception as e:
            if self.socket_cliente:
                self.socket_cliente.close()
            self.error.emit(str(e))

    def escucha_cliente(self):
        try:
            while self.conectado:
                try:
                    msg = self.socket_cliente.recv(1024).decode('utf-8')
                    if not msg:
                        break  # Conexión cerrada

                    self.buffer += msg

                    while '\n' in self.buffer:
                        msg, self.buffer = self.buffer.split('\n', 1)
                        if msg:
                            if msg == "DESCONEXION":
                                self.conectado = False
                                break
                            elif msg == "INICIO":
                                self.iniciar_juego.emit()
                            else:
                                self.mensaje.emit(msg)

                except socket.timeout:
                    continue  # Timeout normal
                except:
                    break  # Error real

        except:
            pass
        finally:
            self.conectado = False
            if self.socket_cliente:
                self.socket_cliente.close()
            self.error.emit("Servidor desconectado")
            self.conexion_cerrada.emit()

    def cliente_man(self, msg):
        if not self.conectado or not self.socket_cliente:
            return

        try:
            msg = msg + "\n"
            self.socket_cliente.send(msg.encode('utf-8'))
        except Exception as e:
            self.cerrar()
            self.error.emit("ERROR_SERVIDOR_CAIDO")

    def cerrar(self):
        self.conectado = False
        if self.socket_cliente:
            self.socket_cliente.close()