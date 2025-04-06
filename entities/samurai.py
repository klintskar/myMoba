import arcade
from PIL import ImageOps
from entities.player import Player

class Samurai(Player):
    def __init__(self):
        super().__init__()
        self.scale = 2.2
        self.load_textures()
        self.texture = self.textures_idle[0]

    def load_textures(self):
        base_path = "assets/images/samurai/"

        self.textures_idle = arcade.load_spritesheet(base_path + "IDLE.png", 96, 96, 10, 10)
        self.textures_idle_flipped = [
            arcade.Texture(f"idle_flipped_{i}", image=ImageOps.mirror(tex.image))
            for i, tex in enumerate(self.textures_idle)
        ]

        self.textures_run = arcade.load_spritesheet(base_path + "RUN.png", 96, 96, 16, 16)
        self.textures_run_flipped = [
            arcade.Texture(f"run_flipped_{i}", image=ImageOps.mirror(tex.image))
            for i, tex in enumerate(self.textures_run)
        ]

        self.textures_attack = arcade.load_spritesheet(base_path + "ATTACK 1.png", 96, 96, 7, 7)
        self.textures_attack_flipped = [
            arcade.Texture(f"attack_flipped_{i}", image=ImageOps.mirror(tex.image))
            for i, tex in enumerate(self.textures_attack)
        ]
