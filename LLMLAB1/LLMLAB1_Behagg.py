import math
import random
import time
import tkinter as tk
import threading


# ------------------------
# GAME LOGIC (PLACEHOLDER)
# ------------------------
def game_loop():
    print("Game loop started (placeholder)")
    while True:
        print("Game logic running...")
        time.sleep(2)


# ------------------------
# MAIN GAME WINDOW
# ------------------------
def open_game_window(root):
    print("Opening game window...")

    game_window = tk.Toplevel(root)
    game_window.title("Game Window")
    game_window.geometry("400x300")

    def on_close():
        print("Game window closed, destroying root...")
        root.destroy()

    game_window.protocol("WM_DELETE_WINDOW", on_close)

    label = tk.Label(game_window, text="Game Screen (Placeholder)")
    label.pack(pady=20)

    # Start game loop in a thread
    game_thread = threading.Thread(target=game_loop, daemon=True)
    game_thread.start()


# ------------------------
# SETTINGS WINDOW
# ------------------------
def open_settings_window(root):
    print("Opening settings window...")

    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("300x200")

    label = tk.Label(settings_window, text="Settings (Placeholder)")
    label.pack(pady=20)

    button = tk.Button(settings_window, text="Change Setting",
                       command=lambda: print("Changing a setting (placeholder)"))
    button.pack(pady=10)


# ------------------------
# MAIN MENU
# ------------------------
def create_main_menu():
    root = tk.Tk()
    root.title("Main Menu")
    root.geometry("300x250")

    title = tk.Label(root, text="Main Menu", font=("Arial", 16))
    title.pack(pady=20)

    play_button = tk.Button(root, text="Play",
                            command=lambda: open_game_window(root))
    play_button.pack(pady=10)

    settings_button = tk.Button(root, text="Settings",
                                command=lambda: open_settings_window(root))
    settings_button.pack(pady=10)

    quit_button = tk.Button(root, text="Quit",
                            command=lambda: root.destroy())
    quit_button.pack(pady=10)

    root.mainloop()


# ------------------------
# ENTRY POINT
# ------------------------
if __name__ == "__main__":
    create_main_menu()