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
        self.username = username
        self.all_usernames = all_usernames if all_usernames else []

        self.players = arcade.SpriteList()
        self.projectiles = arcade.SpriteList()
        self.physics_engines = []
        self.remote_players = {}  # username -> sprite
        self.incoming_data = queue.Queue()

        self.player = None
        self.setup_complete = False
        self.setup_called = False

        self._first_draw_complete = False


    def on_show(self):
        if not self.setup_called:
            self.setup()
            self.setup_called = True

        self.window.push_handlers(self)

        if self.connection and hasattr(self.connection, 'receive'):
            threading.Thread(target=self.listen_loop, daemon=True).start()

    def setup(self):
        for username in self.all_usernames:
            if username == self.username:
                sprite = Hood() if self.is_host else Samurai()
                self.player = sprite
                self.remote_players[username] = sprite
            else:
                self.remote_players[username] = None  # mark as pending creation

        for username, sprite in self.remote_players.items():
            if sprite is not None:
                sprite.center_x = 100
                sprite.center_y = 100
                self.players.append(sprite)

        if not self.player:
            print("⚠️ self.player was not set, using fallback")
            self.player = self.players[0]

    def delayed_setup(self, delta_time):
        print("✅ Running delayed setup")
        self.update_physics_engines()
        self.setup_complete = True

        if self.connection and hasattr(self.connection, 'receive'):
            threading.Thread(target=self.listen_loop, daemon=True).start()

    def update_physics_engines(self):
        self.physics_engines.clear()
        for character in self.players:
            blocking = arcade.SpriteList()
            for other in self.players:
                if other != character:
                    blocking.append(other)
            engine = arcade.PhysicsEngineSimple(character, blocking)
            self.physics_engines.append(engine)

    def on_draw(self):
        self.clear()
        arcade.start_render()

        if not self._first_draw_complete:
            self._first_draw_complete = True
            self.setup()
            self.update_physics_engines()  # make sure physics are ready
            self.setup_complete = True  # ✅ enable on_update logic

            if self.connection and hasattr(self.connection, 'receive'):
                threading.Thread(target=self.listen_loop, daemon=True).start()

        self.players.draw()
        self.projectiles.draw()

    def on_update(self, delta_time):
        if not self.setup_complete:
            return

        while not self.incoming_data.empty():
            data_dict = self.incoming_data.get_nowait()
            print(f"🟡 Handling update for: {data_dict.get('username')}")  # 👀 Add this
            self.update_remote_positions(data_dict)

        def listen_loop(self):
            while True:
                try:
                    data = self.connection.receive()
                    if not data:
                        continue
                    print(f"🔵 Raw data received: {data}")  # 👀 Add this line
                    try:
                        data_dict = json.loads(data)
                        print(f"🟢 Parsed: {data_dict}")  # 👀 Add this too
                        self.incoming_data.put(data_dict)
                    except json.JSONDecodeError:
                        print("❌ Invalid JSON received:", data)
                except Exception as e:
                    print("Listen loop error:", e)
                    break

    def update_remote_positions(self, data_dict):
        username = data_dict.get("username")
        print(f"🔶 update_remote_positions called for {username}")  # 👀 Debug
        if username == self.username:
            return

        if self.remote_players.get(username) is None:
            sprite = Hood() if self.is_host else Samurai()
            self.remote_players[username] = sprite
            sprite.center_x = data_dict.get("x", 100)
            sprite.center_y = data_dict.get("y", 100)
            self.players.append(sprite)
            self.update_physics_engines()
            print(f"✅ Created remote player: {username}")
        else:
            sprite = self.remote_players[username]
            sprite.center_x = data_dict.get("x", sprite.center_x)
            sprite.center_y = data_dict.get("y", sprite.center_y)
            sprite.update_animation(1 / 60)
            print(f"Updated position: {username} ({sprite.center_x}, {sprite.center_y})")

    def on_key_press(self, key, modifiers):
        if self.player:
            self.player.handle_key_press(key)

    def on_key_release(self, key, modifiers):
        if self.player:
            self.player.handle_key_release(key)
