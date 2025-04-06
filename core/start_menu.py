import arcade
import arcade.gui
from core.network import HostConnection, ClientConnection
from core.game import GameView
from core.lobby import LobbyView

class StartMenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.ui_manager = arcade.gui.UIManager()
        self.ui_box = arcade.gui.UIBoxLayout()
        self.ip_input_box = None
        self.popup_widgets = []
        self.username_input = arcade.gui.UIInputText(width=200, text="Player")

    def on_show(self):
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)
        self.ui_manager.enable()

        title = arcade.gui.UILabel(text="MyMOBA", font_size=36, align="center")
        self.ui_box.add(title.with_space_around(bottom=20))

        self.ui_box.add(arcade.gui.UILabel(text="Username:", font_size=16))
        self.ui_box.add(self.username_input.with_space_around(bottom=20))

        # Buttons
        singleplayer_button = arcade.gui.UIFlatButton(text="Singleplayer", width=200)
        join_button = arcade.gui.UIFlatButton(text="Join", width=200)
        host_button = arcade.gui.UIFlatButton(text="Host", width=200)

        singleplayer_button.on_click = self.start_singleplayer
        join_button.on_click = self.show_ip_input
        host_button.on_click = self.host_placeholder

        self.ui_box.add(singleplayer_button.with_space_around(bottom=10))
        self.ui_box.add(join_button.with_space_around(bottom=10))
        self.ui_box.add(host_button.with_space_around(bottom=10))

        self.ui_manager.add(arcade.gui.UIAnchorWidget(anchor_x="center", anchor_y="center", child=self.ui_box))

    def on_draw(self):
        self.clear()
        self.ui_manager.draw()

    def on_hide_view(self):
        self.ui_manager.disable()

    def start_singleplayer(self, event):
        self.window.show_view(GameView())

    def show_ip_input(self, event):
        if self.popup_widgets:
            return  # prevent duplicates

        self.ip_input_box = arcade.gui.UIInputText(width=200)
        connect_button = arcade.gui.UIFlatButton(text="Connect", width=200)
        connect_button.on_click = self.join_placeholder

        cancel_button = arcade.gui.UIFlatButton(text="Cancel", width=200)
        cancel_button.on_click = self.close_ip_input

        input_box = arcade.gui.UIBoxLayout(vertical=True)
        input_box.add(arcade.gui.UILabel(text="Enter IP to Join", font_size=16).with_space_around(bottom=10))
        input_box.add(self.ip_input_box.with_space_around(bottom=10))
        input_box.add(connect_button.with_space_around(bottom=5))
        input_box.add(cancel_button)

        popup = arcade.gui.UIAnchorWidget(anchor_x="left", anchor_y="center", align_x=50, child=input_box)
        self.popup_widgets.append(popup)
        self.ui_manager.add(popup)

    def close_ip_input(self, event=None):
        for widget in self.popup_widgets:
            self.ui_manager.remove(widget)
        self.popup_widgets.clear()
        self.ip_input_box = None

    def join_placeholder(self, event):
        if not self.ip_input_box:
            print("No IP input found.")
            return

        ip_text = self.ip_input_box.text.strip()
        username = self.username_input.text.strip() or "Player"

        # Parse host and port
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
            self.window.show_view(GameView(is_host=False, connection=conn))
        except Exception as e:
            print(f"Connection failed: {e}")
            self.close_ip_input()

    def host_placeholder(self, event):
        username = self.username_input.text.strip() or "Host"
        try:
            conn = HostConnection()
            self.window.show_view(LobbyView(conn, username))
        except OSError as e:
            print(f"Failed to bind port: {e}")
