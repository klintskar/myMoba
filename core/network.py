import socket
import threading
import json

PORT = 65432
BUFFER = 1024


class GameServer:
    def __init__(self, on_player_join, on_player_leave, on_data_received):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('', PORT))
        self.server.listen(10)
        self.clients = {}  # conn -> username
        self.on_player_join = on_player_join
        self.on_player_leave = on_player_leave
        self.on_data_received = on_data_received
        self.running = True

    def start(self):
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def accept_loop(self):
        while self.running:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self, conn):
        try:
            username = conn.recv(BUFFER).decode().strip()
            username = self._resolve_duplicate_name(username)
            self.clients[conn] = username
            self.on_player_join(username)

            while self.running:
                data = conn.recv(BUFFER)
                if not data:
                    break
                self.on_data_received(username, data.decode())
                self.broadcast(data.decode(), exclude=username)

        except Exception as e:
            print(f"Client error: {e}")

        finally:
            self._remove_client(conn)

    def _remove_client(self, conn):
        username = self.clients.pop(conn, None)
        if username:
            self.on_player_leave(username)
        try:
            conn.close()
        except:
            pass

    def broadcast(self, data_dict):
        msg = json.dumps(data_dict).encode()
        for conn in list(self.clients):
            try:
                conn.sendall(msg)
                print(f"Broadcasted data to {self.clients[conn]}: {data_dict}")  # Debugging line
            except:
                self._remove_client(conn)

    def _resolve_duplicate_name(self, name):
        existing = list(self.clients.values())
        if name not in existing:
            return name
        i = 1
        while f"{name} ({i})" in existing:
            i += 1
        return f"{name} ({i})"


class ClientConnection:
    def __init__(self, host, port, username):
        self.host = host
        self.port = port
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.recv_thread = None
        self.on_receive = None
        self.running = False

    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            self.socket.sendall(self.username.encode())
            self.running = True
            self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
            self.recv_thread.start()
            print(f"Connected to server at {self.host}:{self.port} as {self.username}")
        except Exception as e:
            print(f"Connection failed: {e}")
            self.running = False

    def _recv_loop(self):
        while self.running:
            try:
                data = self.socket.recv(BUFFER)
                if not data:
                    break
                if self.on_receive:
                    self.on_receive(data.decode())
                print(f"Received data: {data.decode()}")  # Debugging line
            except Exception as e:
                print(f"Receive error: {e}")
                self.running = False
                break  # Exit the loop on error

    def send(self, data_dict):
        try:
            msg = json.dumps(data_dict).encode()
            self.socket.sendall(msg)
            #print(f"Sent data: {data_dict}")
        except Exception as e:
            print(f"Send error: {e}")
            self.running = False
            self.close()  # Ensure the connection is closed properly

    def close(self):
        self.running = False
        try:
            self.socket.close()
            print("Connection closed")  # Debugging line
        except:
            pass