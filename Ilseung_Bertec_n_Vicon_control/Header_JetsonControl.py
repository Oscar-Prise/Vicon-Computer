import socket
import threading

class JetsonController:

    def __init__(self, server_ip, port_number):
        self.server_ip = server_ip
        self.port_number = port_number
        self.connection = False
        self.client_socket = " "
        self.client_address = " "
        
    def handle_client(self, client_socket, client_address):
        print(f"[NEW CONNECTION] Jetson connected.")
        # print('Client address: ', client_address)
        self.connection = True

    def send_message(self, message):
        try:
            # Send a message to the client
            trigger_message = message
            self.client_socket.sendall(trigger_message.encode('utf-8'))
            # print(f"[MESSAGE SENT] Sent to {self.client_address}: {trigger_message}")
            print('Jetson TRIGGERED')

        except ConnectionResetError:
            print(f"[ERROR] Connection with {self.client_address} lost.")
            self.client_socket.close()
            self.connection = False

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.server_ip, self.port_number))
        server.listen()
        print(f"[LISTENING] Listening for Jetson")
        # print(f'on {self.server_ip}:{self.port_number}')

        while not self.connection:
            self.client_socket, self.client_address = server.accept()
            # Handle each client connection in a new thread
            client_thread = threading.Thread(target=self.handle_client, args=(self.client_socket, self.client_address))
            client_thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")