import arcade
from core.network import HostConnection
from core.game import GameView

class WaitingForPlayerView(arcade.View):
    def __init__(self):
        super().__init__()
        self.connection = HostConnection()
        self.text = "Waiting for a player to join..."
        self.switched = False

    def on_show(self):
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self.connection.start_listening(self.on_player_joined)

    def on_draw(self):
        self.clear()
        arcade.draw_text(self.text, self.window.width // 2, self.window.height // 2,
                         arcade.color.WHITE, 24, anchor_x="center")

    def on_player_joined(self):
        if self.switched:
            return
        self.switched = True
        print("Switching to GameView")
        arcade.schedule(self.delayed_show, 0.01)

    def delayed_show(self, dt):
        arcade.unschedule(self.delayed_show)
        game_view = GameView(is_host=True, connection=self.connection)
        self.window.show_view(game_view)

