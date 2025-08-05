from Connection.ConnectionString import ConnectionString
from Connection.DBSocket.DBSocket import DBSocket
import socket


def _recv_all(sock: socket.socket):
    try:
        # https://stackoverflow.com/a/17697651
        data = b''
        while True:
            part = sock.recv(DBSocket.BUFF_SIZE)
            data += part
            if len(part) < DBSocket.BUFF_SIZE:
                # either 0 or end of data
                break
        return data
    except ConnectionAbortedError:
        print(
            sock.detach()
        )


class TCPSocket(DBSocket):
    ip: str
    port: int
    __socket: socket.socket
    __alive: bool = False

    def __init__(self, ip: str = "127.0.0.1", port: int = 3254):
        self.ip = ip
        self.port = port

        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @property
    def __alive__(self) -> bool:
        return self.__alive

    def connect(self):
        self.__socket.connect((self.ip, self.port))
        self.__alive = True

    def send(self, msg: str):
        self.__socket.send((msg + DBSocket.SEND_CHAR).encode(DBSocket.ENCODING))

    def recv(self) -> str:
        return _recv_all(self.__socket).decode(DBSocket.ENCODING)

    def close(self):
        self.__socket.close()
        self.__alive = False
