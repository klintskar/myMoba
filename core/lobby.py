import arcade
from core.game import GameView

class LobbyView(arcade.View):
    def __init__(self, server, host_username, is_host, client_connection, local_username):
        super().__init__()
        self.server = server
        self.client_connection = client_connection
        self.local_username = local_username
        self.is_host = is_host
        self.players = [host_username] if is_host else []

        if self.is_host and self.server:
            self.server.on_player_join = self.on_player_joined
            self.server.on_player_leave = self.on_player_left
            self.server.on_data_received = self.on_data_received_host
        elif self.client_connection:
            self.client_connection.on_receive = self.on_data_received_client

        if self.is_host:
            self.start_button = arcade.SpriteSolidColor(200, 50, arcade.color.AIR_SUPERIORITY_BLUE)
            self.start_button.center_x = 400
            self.start_button.center_y = 100


    def on_show(self):
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

    def on_draw(self):
        self.clear()

        if self.is_host and self.start_button:
            self.start_button.draw()
            arcade.draw_text("Start Game", self.start_button.center_x, self.start_button.center_y,
                            arcade.color.BLACK, 16, anchor_x="center", anchor_y="center")


        for i, name in enumerate(self.players):
            arcade.draw_text(name, 100, 500 - i * 30, arcade.color.WHITE, 18)

        if not self.is_host:
            arcade.draw_text("Waiting for host to start...", 400, 60, arcade.color.WHITE, 18, anchor_x="center")

    def on_mouse_press(self, x, y, button, modifiers):
        if self.is_host and self.start_button and self.start_button.collides_with_point((x, y)):
          self.start_game()


    def on_player_joined(self, username):
        if username not in self.players:
            self.players.append(username)
            print(f"{username} joined lobby.")
            if self.server:
                self.server.broadcast({"type": "lobby_update", "players": self.players})

    def on_player_left(self, username):
        if username in self.players:
            self.players.remove(username)
            print(f"{username} left the lobby.")
            if self.server:
                self.server.broadcast({"type": "lobby_update", "players": self.players})

    def on_data_received_host(self, username, message):
        self._handle_message(message)

    def on_data_received_client(self, message):
        self._handle_message(message)

    def _handle_message(self, raw):
        import json
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                print("Invalid JSON in lobby")
                return
        else:
            data = raw

        if data.get("type") == "lobby_update":
            self.players = data.get("players", [])
            print("Updated player list:", self.players)

        elif data.get("type") == "start_game":
            print("Client received start_game!")
            game_view = GameView(
                is_host=False,
                connection=self.client_connection,
                username=self.local_username,
                all_usernames=self.players
            )
            self.window.show_view(game_view)

    def start_game(self):
        print("Starting game from lobby...")
        if self.is_host and self.server:
            self.server.broadcast({"type": "start_game"})
        game_view = GameView(
            is_host=True,
            connection=self.server,
            username=self.local_username,
            all_usernames=self.players
        )
        self.window.show_view(game_view)
