import arcade
from PIL import Image, ImageOps
from entities.player import Player

class Hood(Player):
    def __init__(self):
        super().__init__()
        self.scale = 2
        self.load_textures()
        self.texture = self.textures_idle[0]

    def load_textures(self):
        sprite_sheet_path = "assets/images/hood/hood.png"  # place the sheet here
        frame_width = 32
        frame_height = 32

        sprite_sheet = Image.open(sprite_sheet_path).convert("RGBA")

        def load_row(row_index, frame_count, name_prefix):
            frames = []
            flipped_frames = []
            for i in range(frame_count):
                x = i * frame_width
                y = row_index * frame_height
                box = (x, y, x + frame_width, y + frame_height)
                frame_image = sprite_sheet.crop(box)

                tex = arcade.Texture(f"{name_prefix}_{i}", image=frame_image)
                flipped_tex = arcade.Texture(f"{name_prefix}_flipped_{i}", image=ImageOps.mirror(frame_image))

                frames.append(tex)
                flipped_frames.append(flipped_tex)
            return frames, flipped_frames

        # Load animations (you can rename these once you know which row is what)
        self.textures_idle, self.textures_idle_flipped = load_row(2, 4, "idle")
        self.textures_run, self.textures_run_flipped = load_row(3, 8, "run")
        self.textures_attack, self.textures_attack_flipped = load_row(8, 8, "attack")  # guessing attack row