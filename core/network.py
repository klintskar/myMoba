import socket
import threading
import json
import queue

PORT = 65432
BUFFER = 4096  # instead of 1024

class GameServer:
    def __init__(self, on_player_join, on_player_leave, on_data_received):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(('', PORT))
        self.server.listen(10)

        self.clients = {}  # conn -> username
        self.client_queues = {}  # conn -> queue.Queue()
        self.on_player_join = on_player_join
        self.on_player_leave = on_player_leave
        self.on_data_received = on_data_received
        self.running = True
        self.message_queue = queue.Queue()

    def start(self):
        threading.Thread(target=self.accept_loop, daemon=True).start()

    def accept_loop(self):
        while self.running:
            conn, addr = self.server.accept()
            threading.Thread(target=self.handle_client, args=(conn,), daemon=True).start()

    def handle_client(self, conn):
        try:
            name_data = conn.recv(BUFFER)
            requested_name = name_data.decode().strip()
            print(f"🔵 New connection requested name: {requested_name}")

            username = self._resolve_duplicate_name(requested_name)
            print(f"✅ Final assigned username: {username}")

            self.clients[conn] = username
            self.client_queues[conn] = queue.Queue()
            self.on_player_join(username)

            # Inform the client of their resolved username
            self.client_queues[conn].put(json.dumps({
                "type": "set_username",
                "username": username
            }).encode())

            # Send updated lobby list
            self.broadcast({
                "type": "lobby_update",
                "players": list(self.clients.values())
            })

            # Start sender thread
            threading.Thread(target=self.client_sender, args=(conn,), daemon=True).start()

            while True:
                data = conn.recv(BUFFER)
                if not data:
                    break

                decoded = data.decode()
                self.on_data_received(username, decoded)
                self.message_queue.put((username, decoded))

                # Re-broadcast the message to others
                self.broadcast(decoded, exclude=username)

        except Exception as e:
            print("Client error:", e)
        finally:
            self._remove_client(conn)

    def client_sender(self, conn):
        queue_ = self.client_queues[conn]
        while self.running:
            try:
                msg = queue_.get(timeout=0.1)
                conn.sendall(msg)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Client sender failed: {e}")
                self._remove_client(conn)
                break

    def broadcast(self, data_dict, exclude=None):
        if isinstance(data_dict, str):
            try:
                data_dict = json.loads(data_dict)
            except json.JSONDecodeError:
                print(f"❌ Can't broadcast invalid JSON: {data_dict}")
                return

        msg = json.dumps(data_dict).encode()

        for conn in list(self.clients):
            username = self.clients[conn]
            if exclude is not None and username == exclude:
                continue
            if conn in self.client_queues:
                try:
                    self.client_queues[conn].put(msg)
                except Exception as e:
                    print(f"❌ Failed to queue message for {username}: {e}")
                    self._remove_client(conn)

    def _remove_client(self, conn):
        username = self.clients.pop(conn, None)
        self.client_queues.pop(conn, None)
        if username:
            self.on_player_leave(username)
        try:
            conn.close()
        except:
            pass

    def _resolve_duplicate_name(self, name):
        existing_names = set(self.clients.values())
        if name not in existing_names:
            return name
        i = 1
        while f"{name} ({i})" in existing_names:
            i += 1
        return f"{name} ({i})"

    def send(self, data_dict):
        self.broadcast(data_dict)
        self.message_queue.put(("HOST_SELF", json.dumps(data_dict)))

    def receive(self):
        try:
            return self.message_queue.get(timeout=0.1)
        except queue.Empty:
            return None

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
        try:
            while self.running:
                data = self.socket.recv(BUFFER)
                if not data:
                    break

                text = data.decode()

                # Try parsing as JSON
                try:
                    parsed = json.loads(text)

                    # 🎉 Handle special message: set_username
                    if parsed.get("type") == "set_username":
                        self.username = parsed["username"]
                        print(f"🎉 Server assigned final username: {self.username}")
                        continue

                except json.JSONDecodeError:
                    # Not JSON or not parseable — log and continue
                    print("❌ Invalid JSON received from server")

                # 💡 Still pass ALL messages (JSON or raw) to the client handler
                if self.on_receive:
                    self.on_receive(text)

        except Exception as e:
            print("Receive error:", e)
        finally:
            self.socket.close()
            self.running = False
            print("Connection closed")

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

    def receive(self):
        try:
            data = self.socket.recv(BUFFER)
            if not data:
                return None
            return data.decode()
        except Exception as e:
            print("Client receive error:", e)
            return None