import arcade
from core.network import HostConnection
from core.game import GameView

class LobbyView(arcade.View):
    def __init__(self, connection: HostConnection, host_username: str):
        super().__init__()
        self.connection = connection
        self.host_username = host_username
        self.player_list = [host_username]
        self.start_button = None
        self.ui_initialized = False

    def on_show(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.connection.start_listening(self.on_player_joined)

        # Create start button
        self.start_button = arcade.SpriteSolidColor(150, 40, arcade.color.GREEN)
        self.start_button.center_x = self.window.width // 2
        self.start_button.center_y = 50
        self.ui_initialized = True

    def on_player_joined(self, username):
        if username not in self.player_list:
            self.player_list.append(username)
        print(f"{username} joined!")

    def on_draw(self):
        self.clear()

        if self.ui_initialized:
            self.start_button.draw()
            arcade.draw_text("Start Game", self.start_button.center_x, self.start_button.center_y,
                              arcade.color.BLACK, font_size=16, anchor_x="center", anchor_y="center")

        # Draw all connected players
        arcade.draw_text("Connected Players:", 100, self.window.height - 100, arcade.color.WHITE, 20)
        for i, name in enumerate(self.player_list):
            arcade.draw_text(name, 100, self.window.height - 140 - i * 30, arcade.color.WHITE, 16)

    def on_mouse_press(self, x, y, button, modifiers):
        if self.start_button and self.start_button.collides_with_point((x, y)):
            self.start_game()

    def start_game(self):
        print("Starting game from lobby...")
        game = GameView(is_host=True, connection=self.connection)
        self.window.show_view(game)
