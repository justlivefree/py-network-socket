import datetime
import os
import pickle
import socket
import threading
from socket import SocketType

from core.config import LEAVE_CHAT, PORT, FILE_MSG, TEXT_MSG, MSG_SIZE, FILE_CHUNK_SIZE


class Core:

    def __init__(self, address_family=socket.AF_INET,
                 server_type=socket.SOCK_STREAM,
                 host=None,
                 **socket_options):
        # by default, it works on TCP and IPv4
        self.address = (socket.gethostbyname(socket.gethostname()), PORT) if host is None else (host, PORT)
        self.server = socket.socket(address_family, server_type)
        if socket_options == {}:
            self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        else:
            self.server.setsockopt(**socket_options)

    def start(self):
        pass


class Server(Core):

    def __init__(self, *args, **kwargs):
        self.clients = {}
        super().__init__(*args, **kwargs)

    @staticmethod
    def _parse_file_header(header: bytes):
        data = pickle.loads(header)
        return data['file_name'], data['size']

    def file_handler(self, client: SocketType):
        count = int(client.recv(32).strip())
        for _ in range(count):
            header = client.recv(512).strip()
            file_name, size = self._parse_file_header(header)
            if os.path.exists(file_name):
                name, ext = file_name.rsplit('.')
                file_name = f'{name}_{datetime.datetime.now()}.{ext}'
            with open(file_name, 'wb') as file:
                while size > 0:
                    file_msg = client.recv(min(FILE_CHUNK_SIZE, size))
                    size -= len(file_msg)
                    file.write(file_msg)
        client.close()

    def message_handler(self, client: SocketType, addr):
        header = pickle.loads(client.recv(512).strip())
        host, port = addr
        client_id, client_username = header.values()
        header.update({'socket': client})
        self.clients[client_id] = header
        check = True
        while check:
            text_msg = client.recv(1024)
            if text_msg in (LEAVE_CHAT, b''):
                text_msg = pickle.dumps({
                    'left_user': client_username
                })
                text_msg += b' ' * (MSG_SIZE - len(text_msg))
                check = False
                del self.clients[client_id]
            for key, val in self.clients.items():
                val['socket'].send(text_msg)
        client.close()
        print(f'[DISCONNECT] {host}:{port}')

    def start(self):
        self.server.bind(self.address)
        self.server.listen()
        print(f'[SERVER] {self.address[0]}:{PORT}')
        while True:
            conn, addr = self.server.accept()
            print(f'[NEW CONNECTION] {addr[0]}')
            type_msg = int(conn.recv(2))
            if type_msg == FILE_MSG:
                thread = threading.Thread(target=self.file_handler, args=(conn,))
            elif type_msg == TEXT_MSG:
                thread = threading.Thread(target=self.message_handler, args=(conn, addr))
            else:
                continue
            thread.start()
