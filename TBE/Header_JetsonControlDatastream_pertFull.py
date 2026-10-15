#June 9 2025 Viconside
import socket
import threading
import time  
class StreamJetson:

    def __init__(self, server_ip, port_number):
        self.server_ip = server_ip
        self.port_number = port_number
        self.connection = False
        self.client_socket = None
        self.client_address = None
        self.data_to_send = None  # Shared variable for data from the main script

    def send_data(self, data):
        """Update the data to be sent to the Jetson."""
        self.data_to_send = data + '\n'  # Ensure data ends with a newline for proper parsing
        # print(f"[DEBUG] Data to send updated: {self.data_to_send}")  # Debugging

    def send_trigger_now(self,pertnum):
        """Send perturbation trigger immediately without affecting data streaming."""
        if self.connection and self.client_socket:
            try:
                trigger_msg = f"{pertnum}\n"
                self.client_socket.sendall(trigger_msg.encode('utf-8'))
                print(f"[TRIGGER SENT] Perturbation trigger at {time.time()}")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to send trigger: {e}")
                return False
        else:
            print("[WARNING] No active connection for trigger")
            return False

    def handle_client(self, client_socket, client_address):
        print(f"[NEW CONNECTION] Jetson connected from {client_address}.")
        self.connection = True
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm for low latency
        try:
            while self.connection:
                if self.data_to_send:  # Check if there's data to send
                    client_socket.sendall(self.data_to_send.encode('utf-8'))
                    # print(f"[DATA SENT] {self.data_to_send}")
                    self.data_to_send = None  # Clear the data after sending
                time.sleep(0.001)  # Small delay to prevent busy-waiting
        except ConnectionResetError:
            print(f"[ERROR] Connection with {client_address} lost.")
            self.connection = False
        finally:
            client_socket.close()
            print(f"[DISCONNECTED] Jetson disconnected.")

    def start_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            # Try binding to the specified IP and port
            server.bind((self.server_ip, self.port_number))
            print(f"[LISTENING] Server is listening on {self.server_ip}:{self.port_number}")
        except PermissionError:
            print(f"[ERROR] Permission denied for {self.server_ip}:{self.port_number}")
            # Try binding to localhost instead
            try:
                server.bind(('localhost', self.port_number))
                self.server_ip = 'localhost'
                print(f"[LISTENING] Server is listening on localhost:{self.port_number}")
            except:
                # If that fails, let the system assign a port
                server.bind(('localhost', 0))
                self.server_ip, self.port_number = server.getsockname()
                print(f"[LISTENING] Server is listening on {self.server_ip}:{self.port_number}")
        except OSError as e:
            print(f"[ERROR] Socket error: {e}")
            # Try with system-assigned port
            try:
                server.bind(('localhost', 0))
                self.server_ip, self.port_number = server.getsockname()
                print(f"[LISTENING] Server is listening on {self.server_ip}:{self.port_number}")
            except Exception as e:
                print(f"[FATAL ERROR] Cannot start server: {e}")
                return
        
        server.listen()

        while True:
            try:
                self.client_socket, self.client_address = server.accept()
                # Handle each client connection in a new thread
                client_thread = threading.Thread(target=self.handle_client, args=(self.client_socket, self.client_address))
                client_thread.start()
                print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
            except Exception as e:
                print(f"[ERROR] Error accepting connection: {e}")
                break