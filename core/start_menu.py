import arcade
import arcade.gui
from core.network import GameServer, ClientConnection
from core.lobby import LobbyView
from core.game import GameView

class StartMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ui_manager = arcade.gui.UIManager()
        self.ui_box = arcade.gui.UIBoxLayout()

        self.username_input = arcade.gui.UIInputText(width=200, text="Player")
        self.ip_input_box = None
        self.popup_widgets = []

    def on_show(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.ui_manager.enable()

        title = arcade.gui.UILabel(text="MyMOBA", font_size=36, align="center")
        self.ui_box.add(title.with_space_around(bottom=20))

        self.ui_box.add(arcade.gui.UILabel(text="Username:", font_size=16))
        self.ui_box.add(self.username_input.with_space_around(bottom=20))

        singleplayer_button = arcade.gui.UIFlatButton(text="Singleplayer", width=200)
        join_button = arcade.gui.UIFlatButton(text="Join", width=200)
        host_button = arcade.gui.UIFlatButton(text="Host", width=200)

        singleplayer_button.on_click = lambda *_: self.start_singleplayer()
        join_button.on_click = lambda *_: self.show_ip_input()
        host_button.on_click = lambda *_: self.host_game()

        self.ui_box.add(singleplayer_button.with_space_around(bottom=10))
        self.ui_box.add(join_button.with_space_around(bottom=10))
        self.ui_box.add(host_button.with_space_around(bottom=10))

        self.ui_manager.add(arcade.gui.UIAnchorWidget(anchor_x="center", anchor_y="center", child=self.ui_box))

    def on_hide_view(self):
        self.ui_manager.disable()

    def on_draw(self):
        self.clear()
        self.ui_manager.draw()

    def start_singleplayer(self):
        username = self.username_input.text.strip() or "Player"
        game_view = GameView(is_host=False, connection=None, username=username, all_usernames=[username])
        self.window.show_view(game_view)

    def show_ip_input(self):
        if self.popup_widgets:
            return

        self.ip_input_box = arcade.gui.UIInputText(width=200)
        connect_button = arcade.gui.UIFlatButton(text="Connect", width=200)
        connect_button.on_click = lambda *_: self.join_game()

        cancel_button = arcade.gui.UIFlatButton(text="Cancel", width=200)
        cancel_button.on_click = lambda *_: self.close_ip_input()

        input_box = arcade.gui.UIBoxLayout(vertical=True)
        input_box.add(arcade.gui.UILabel(text="Enter IP to Join", font_size=16).with_space_around(bottom=10))
        input_box.add(self.ip_input_box.with_space_around(bottom=10))
        input_box.add(connect_button.with_space_around(bottom=5))
        input_box.add(cancel_button)

        popup = arcade.gui.UIAnchorWidget(anchor_x="left", anchor_y="center", align_x=50, child=input_box)
        self.popup_widgets.append(popup)
        self.ui_manager.add(popup)

    def close_ip_input(self):
        for widget in self.popup_widgets:
            self.ui_manager.remove(widget)
        self.popup_widgets.clear()
        self.ip_input_box = None

    def join_game(self):
        if not self.ip_input_box:
            print("No IP input field found")
            return

        username = self.username_input.text.strip() or "Player"
        ip_text = self.ip_input_box.text.strip()

        if ":" in ip_text:
            try:
                host, port_str = ip_text.split(":")
                port = int(port_str)
            except ValueError:
                print("Invalid format. Use IP or IP:PORT.")
                return
        else:
            host = ip_text
            port = 65432

        print(f"Connecting to {host}:{port} as {username}...")

        try:
            conn = ClientConnection(host, port, username)
            conn.connect()
            lobby_view = LobbyView(server=None, host_username="", is_host=False, client_connection=conn, local_username=username)
            self.window.show_view(lobby_view)
        except Exception as e:
            print(f"Connection failed: {e}")

    def host_game(self):
        username = self.username_input.text.strip() or "Host"

        from core.lobby import LobbyView

        def on_player_join(username):
            print(f"[SERVER] Player joined: {username}")

        def on_player_leave(username):
            print(f"[SERVER] Player left: {username}")

        def on_data_received(user, data):
            print(f"[SERVER] Data from {user}: {data}")

        server = GameServer(
            on_player_join=on_player_join,
            on_player_leave=on_player_leave,
            on_data_received=on_data_received
        )
        server.start()

        lobby = LobbyView(server=server, host_username=username, is_host=True, client_connection=None, local_username=username)
        self.window.show_view(lobby)
    
    def start_game(self):
        print("Starting game from lobby...")
        if self.is_host:
            self.server.broadcast({"type": "start_game"})
        game_view = GameView(
            is_host=self.is_host,
            connection=self.server if self.is_host else self.client_connection,
            username=self.username,
            all_usernames=self.players
        )
        self.window.show_view(game_view)
        print("Transitioned to GameView")  # Debugging line
