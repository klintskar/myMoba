import arcade
from entities.samurai import Samurai
from entities.hood import Hood
import json

class GameView(arcade.View):
    def __init__(self, is_host=False, connection=None):
        super().__init__()
        print("GameView initialized")
        self.is_host = is_host
        self.connection = connection
        self.setup_complete = False
        self.players = arcade.SpriteList()
        self.physics_engines = []
        self.projectiles = arcade.SpriteList()
        self.remote_players = {}  # username -> sprite
        self.setup()

    def setup(self):
        # Local player setup
        if self.is_host:
            self.player = Hood()
        else:
            self.player = Samurai()

        self.player.center_x = 100
        self.player.center_y = 100
        self.players.append(self.player)

        # Setup physics (collisions between all players)
        self.update_physics_engines()

        self.setup_complete = True

    def update_physics_engines(self):
        self.physics_engines.clear()
        for character in self.players:
            blocking_sprites = arcade.SpriteList()
            for other in self.players:
                if other != character:
                    blocking_sprites.append(other)
            engine = arcade.PhysicsEngineSimple(character, blocking_sprites)
            self.physics_engines.append(engine)

    def on_draw(self):
        self.clear()
        arcade.start_render()
        self.players.draw()
        self.projectiles.draw()

    def on_update(self, delta_time):
        if not self.setup_complete:
            return

        for engine in self.physics_engines:
            engine.update()

        self.player.update()
        self.player.update_animation(delta_time)

        # Send local player position
        if self.connection:
            try:
                pos_data = json.dumps({
                    "x": self.player.center_x,
                    "y": self.player.center_y
                })
                self.connection.send(pos_data)
            except Exception as e:
                print("Send error:", e)

            # Receive remote player updates
            try:
                data = self.connection.receive()
                if data:
                    remote_pos = json.loads(data)
                    if "x" in remote_pos and "y" in remote_pos:
                        if not self.remote_players:
                            self.remote_players["remote"] = Hood() if self.is_host else Samurai()
                            self.players.append(self.remote_players["remote"])
                            self.update_physics_engines()

                        remote_sprite = self.remote_players["remote"]
                        remote_sprite.center_x = remote_pos["x"]
                        remote_sprite.center_y = remote_pos["y"]
                        remote_sprite.update_animation(delta_time)
            except Exception as e:
                print("Receive error:", e)

        self.projectiles.update()

    def on_key_press(self, key, modifiers):
        self.player.handle_key_press(key)

    def on_key_release(self, key, modifiers):
        self.player.handle_key_release(key)

    def on_show(self):
        if not self.setup_complete:
            self.setup()
