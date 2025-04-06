import socket
import threading

PORT = 65432
BUFFER = 1024

class HostConnection:
    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('', PORT))
        self.server.listen(5)
        self.clients = []  # (conn, address, username)
        self.on_player_join = None  # callback to UI
        self.lock = threading.Lock()

    def start_listening(self, on_player_join):
        self.on_player_join = on_player_join
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def _accept_loop(self):
        while True:
            try:
                conn, addr = self.server.accept()
                threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True).start()
            except OSError:
                break

    def _handle_client(self, conn, addr):
        try:
            raw_username = conn.recv(BUFFER).decode()
            username = self._resolve_duplicate_name(raw_username)

            with self.lock:
                self.clients.append((conn, addr, username))

            print(f"{username} joined from {addr}")

            if self.on_player_join:
                self.on_player_join(username)

            while True:
                try:
                    data = conn.recv(BUFFER)
                    if not data:
                        print(f"{username} disconnected.")
                        break
                    decoded = data.decode()
                    print(f"Received from {username}: {decoded}")
                except (ConnectionResetError, ConnectionAbortedError):
                    print(f"{username} connection lost.")
                    break

        except Exception as e:
            print(f"Error handling client {addr}: {e}")

        finally:
            with self.lock:
                self.clients = [(c, a, u) for (c, a, u) in self.clients if c != conn]

            try:
                conn.close()
            except:
                pass

            print(f"{username} has been removed from the client list.")

    def _resolve_duplicate_name(self, name):
        with self.lock:
            names = [u for _, _, u in self.clients]
            if name not in names:
                return name
            i = 1
            while f"{name} ({i})" in names:
                i += 1
            return f"{name} ({i})"

    def broadcast(self, message: str):
        with self.lock:
            for conn, _, _ in self.clients:
                try:
                    conn.sendall(message.encode())
                except:
                    pass  # optionally clean dead clients

class ClientConnection:
    def __init__(self, host, port=65432, username="Player"):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.username = username

    def connect(self):
        self.socket.connect((self.host, self.port))
        self.socket.sendall(self.username.encode())

    def send(self, data: str):
        try:
            self.socket.sendall(data.encode())
        except (BrokenPipeError, ConnectionResetError) as e:
            print(f"Disconnected from server: {e}")

    def receive(self) -> str:
        try:
            return self.socket.recv(BUFFER).decode()
        except:
            print("Receive error")
            return ""
