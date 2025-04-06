import arcade
from abc import ABC, abstractmethod

class Player(arcade.Sprite, ABC):
    def __init__(self):
        super().__init__()
        self.change_x = 0
        self.change_y = 0
        self.facing_right = True
        self.speed = 4
        self.held_keys = set()
        self.current_animation = "idle"
        self.current_texture_index = 0
        self.animation_timer = 0
        self.animation_speed = 0.1
        self.is_attacking = False

    @abstractmethod
    def load_textures(self):
        pass

    def update_animation(self, delta_time: float = 1/60):
        self.animation_timer += delta_time

        if self.current_animation == "attack":
            frames = self.textures_attack
            frames_flipped = self.textures_attack_flipped
        elif self.current_animation == "run":
            frames = self.textures_run
            frames_flipped = self.textures_run_flipped
        else:
            frames = self.textures_idle
            frames_flipped = self.textures_idle_flipped

        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0
            self.current_texture_index += 1

            if self.current_texture_index >= len(frames):
                self.current_texture_index = 0
                if self.current_animation == "attack":
                    self.is_attacking = False
                    self.change_x = 0
                    self.change_y = 0
                    self.current_animation = "run" if self.held_keys else "idle"

        facing = self.locked_facing if self.is_attacking else self.facing_right
        self.texture = (
            frames[self.current_texture_index] if facing
            else frames_flipped[self.current_texture_index]
        )

    def handle_key_press(self, key):
        if key in (arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D):
            self.held_keys.add(key)

        elif key == arcade.key.SPACE and not self.is_attacking:
            self.is_attacking = True
            self.current_animation = "attack"
            self.current_texture_index = 0
            self.animation_timer = 0
            self.locked_facing = self.facing_right

    def handle_key_release(self, key):
        if key in self.held_keys:
            self.held_keys.remove(key)

    def update(self):
        # Only update direction and set velocities
        dx = 0
        dy = 0

        if arcade.key.W in self.held_keys:
            dy += self.speed
        if arcade.key.S in self.held_keys:
            dy -= self.speed
        if arcade.key.A in self.held_keys:
            dx -= self.speed
            self.facing_right = False
        if arcade.key.D in self.held_keys:
            dx += self.speed
            self.facing_right = True

        if not self.is_attacking:
            self.change_x = dx
            self.change_y = dy

            new_state = "run" if self.change_x or self.change_y else "idle"
            if new_state != self.current_animation:
                self.current_animation = new_state
                self.current_texture_index = 0
        else:
            self.change_x = 0
            self.change_y = 0
