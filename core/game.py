import arcade
import threading
import json
import queue
from entities.samurai import Samurai
from entities.hood import Hood


class GameView(arcade.View):
    def __init__(self, is_host=False, connection=None, username="Player", all_usernames=None):
        super().__init__()
        print("GameView initialized")
        self.is_host = is_host
        self.connection = connection
        self.username = username.strip()  # ✅ normalize
        self.all_usernames = [u.strip() for u in all_usernames] if all_usernames else []  # ✅ normalize

        self.players = arcade.SpriteList()
        self.projectiles = arcade.SpriteList()
        self.physics_engines = []
        self.remote_players = {}  # username -> sprite
        self.incoming_data = queue.Queue()

        self.player = None
        self.setup_complete = False
        self.setup_called = False
        self.listen_thread_started = False

        self._first_draw_complete = False  # keep this for your flow

    def on_show(self):
        print("GameView on_show called")  # Debug
        if not self.setup_called:
            self.setup()
            self.setup_called = True

    def setup(self):
        print(f"Setting up GameView for: {self.username}")
        for username in self.all_usernames:
            print(f"[setup] Comparing username={username!r} to self.username={self.username!r}")
            if username == self.username:
                sprite = Hood() if self.is_host else Samurai()
                self.player = sprite
                sprite.center_x = 100
                sprite.center_y = 100
                self.players.append(sprite)
                print(f"✅ Player sprite created for {username}")
            else:
                self.remote_players[username] = None  # mark as pending creation

        if not self.player and len(self.players) > 0:
            print("⚠️ self.player was not set, using fallback")
            self.player = self.players[0]
        elif not self.player:
            raise RuntimeError("❌ No player sprite could be assigned — check all_usernames and username!")

        if self.player:
            print(f"✅ self.player initialized: {self.player}")
        print(f"[setup] Created {len(self.players)} sprites for players: {[p for p in self.players]}")
        print(f"[setup] self.username = {self.username}")
        print(f"[setup] all_usernames = {self.all_usernames}")

    def update_physics_engines(self):
        self.physics_engines.clear()
        for character in self.players:
            blocking = arcade.SpriteList()
            for other in self.players:
                if other != character:
                    blocking.append(other)
            engine = arcade.PhysicsEngineSimple(character, blocking)
            self.physics_engines.append(engine)
            print(f"✅ Physics engine created for {character}")

    def on_draw(self):
        self.clear()
        arcade.start_render()

        if not self._first_draw_complete:
            self._first_draw_complete = True

            self.update_physics_engines()  # make sure physics are ready
            self.setup_complete = True  # ✅ enable on_update logic

            if self.connection and hasattr(self.connection, 'receive') and not self.listen_thread_started:
                threading.Thread(target=self.listen_loop, daemon=True).start()
                self.listen_thread_started = True

        #print(f"[draw] Currently drawing {len(self.players)} player sprites")
        self.players.draw()
        #self.projectiles.draw()

    def on_update(self, delta_time):
        #print(f"on_update called with delta_time: {delta_time}")  # Debug
        if not self.setup_complete:
            return

        if self.player:
            self.player.update()
            self.player.update_animation(delta_time)

        # Send position to others
        if self.connection:
            self.connection.send({
                "username": self.username,
                "x": self.player.center_x,
                "y": self.player.center_y
            })

        for engine in self.physics_engines:
            engine.update()

        while not self.incoming_data.empty():
            data_dict = self.incoming_data.get_nowait()
            #print(f"🟡 Handling update for: {data_dict.get('username')}")
            self.update_remote_positions(data_dict)

    def listen_loop(self):
        while True:
            try:
                data = self.connection.receive()
                if not data:
                    continue

                # 🧠 GameServer returns (username, data), while ClientConnection returns str
                if isinstance(data, tuple):
                    sender, data = data  # unpack tuple
                else:
                    sender = "client"

                #print(f"🔵 Raw data received from {sender}: {data}")
                try:
                    data_dict = json.loads(data)
                    #print(f"🟢 Parsed from {sender}: {data_dict}")
                    self.incoming_data.put(data_dict)
                except json.JSONDecodeError:
                    print("❌ Invalid JSON received:", data)

            except Exception as e:
                print("Listen loop error:", e)
                break

    def update_remote_positions(self, data_dict):
        if not isinstance(data_dict, dict):
            print(f"❌ Skipping non-dict update: {data_dict}")
            return

        username = data_dict.get("username", "").strip()

        #print(f"🔶 update_remote_positions called for {username} (self = {self.username})")

        if username == self.username:
            #print("🔁 Skipping update: it’s me")
            return

        sprite = self.remote_players.get(username)

        if sprite is None:
            sprite = Hood() if self.is_host else Samurai()
            sprite.center_x = data_dict.get("x", 100)
            sprite.center_y = data_dict.get("y", 100)
            self.remote_players[username] = sprite
            self.players.append(sprite)
            self.update_physics_engines()
            print(f"✅ Created remote player: {username}")
        else:
            sprite.center_x = data_dict.get("x", sprite.center_x)
            sprite.center_y = data_dict.get("y", sprite.center_y)
            sprite.update_animation(1 / 60)
            #print(f"📦 Updated position: {username} ({sprite.center_x}, {sprite.center_y})")
        #print(f"[remote] Total players on screen: {len(self.players)} | Remote: {list(self.remote_players.keys())}")

    def on_key_press(self, key, modifiers):
        if self.player:
            self.player.handle_key_press(key)

    def on_key_release(self, key, modifiers):
        if self.player:
            self.player.handle_key_release(key)
