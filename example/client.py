from core.client import Client


class CustomClient(Client):

    def show_message(self, sender_id, message):
        print(f'{sender_id} -> {message.strip()}', flush=True)


client = CustomClient('127.0.1.1', 'john doe')

# client.send_file('file_path')

client.start_chat()
while True:
    msg = input('>>> ')
    if msg == '/quit':
        client.close_chat()
        break
    client.send_msg(msg)
