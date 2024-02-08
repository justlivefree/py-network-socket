import os
import pickle
import socket
import threading
import uuid

from core.config import LEAVE_CHAT, CLIENT_ID_SIZE, FILE_MSG, TEXT_MSG, PORT, MSG_SIZE, FILE_CHUNK_SIZE


class Client:

    def __init__(self, host, username):
        self.id = uuid.uuid4().hex.encode()[:CLIENT_ID_SIZE]
        self.username = username
        self.keep_handle = True
        self.chat_server = None
        self.address = (host, PORT)

    def send_file(self, *file_paths):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.connect(self.address)
        server.send(str(FILE_MSG).encode())
        count_files = f'{len(file_paths)}'.encode()
        server.send(count_files + b' ' * (32 - len(count_files)))
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            size = os.path.getsize(file_path)
            header = pickle.dumps(dict(file_name=file_name, size=size))
            server.sendall(header + b' ' * (512 - len(header)))
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(FILE_CHUNK_SIZE), b''):
                    server.send(chunk)
        server.close()

    def start_chat(self):
        self.chat_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.chat_server.connect(self.address)
        self.chat_server.send(str(TEXT_MSG).encode())
        header = pickle.dumps({
            'id': self.id,
            'username': self.username
        })
        self.chat_server.send(header + b' ' * (512 - len(header)))
        threading.Thread(target=self.msg_handler).start()

    def send_msg(self, text):
        data = {
            'sender': self.username,
            'message': text
        }
        send_data = pickle.dumps(data)
        send_data = send_data + b' ' * (MSG_SIZE - len(send_data))
        self.chat_server.send(send_data)

    def close_chat(self):
        self.chat_server.send(LEAVE_CHAT)

    def msg_handler(self):
        try:
            while True:
                tmp = self.chat_server.recv(MSG_SIZE).strip()
                msg_data = pickle.loads(tmp)
                if clt := msg_data.get('left_user'):
                    self.left_chat(clt)
                else:
                    sender, data = msg_data.values()
                    self.show_message(sender, data)
        except EOFError:
            pass

    def show_message(self, sender, message):
        # Overwrite this function for your case
        pass

    def left_chat(self, username):
        # Overwrite this function for your case
        pass
