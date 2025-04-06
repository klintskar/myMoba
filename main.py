import arcade
from core.start_menu import StartMenuView


SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "myMoba"

def main():
    # Set up the game window
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=True)
    
    # Create and show the main game view
    start_menu = StartMenuView()
    window.show_view(start_menu)

    # Start the arcade run loop
    print("Running game...")
    arcade.run()

if __name__ == "__main__":
    main()
