import tkinter as tk
from tkinter import ttk
import math
import random
import time
import threading

# --- Constants & Configuration ---
GRID_SIZE = 40
MAP_WIDTH = 12
MAP_HEIGHT = 10
INVENTORY_COLS = 9
INVENTORY_ROWS = 3

class RoguelikeGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dungeon Crawler")
        self.root.geometry("400x300")
        self.root.configure(bg="#4B0082")

        # Windows tracking
        self.game_window = None
        self.settings_window = None
        self.upgrade_frame = None
        
        # Settings
        self.theme = {"bg": "#4B0082", "wall": "#2F4F4F", "floor": "#1A1A1A"}
        self.use_emojis = tk.BooleanVar(value=True)
        self.konami_unlocked = False
        self.konami_buffer = []
        self.konami_code = ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]

        # Game State
        self.running = False
        self.turn_count = 0
        self.floor_count = 1
        
        # Player Data Structure (Nested Dictionaries)
        self.player = {
            "stats": {"hp": 100, "max_hp": 100, "dmg": 10, "def": 2, "dodge": 5, "speed": 1, "xp": 0},
            "pos": {"x": 1, "y": 1},
            "inventory": {}, # {item_name: (x, y)}
            "hotbar": {},    # {item_name: (x, y)}
            "equipment": []
        }
        
        self.item_stats = {
            "Rusty Sword": {"dmg_mult": 1.2, "type": "weapon"},
            "Leather Armor": {"def_mult": 1.5, "type": "armor"},
            "Lucky Charm": {"dodge_mult": 2.0, "type": "acc"}
        }

        self.loot_table = {
            1: ["Rusty Sword", "Leather Armor", "Small Potion"],
            2: ["Iron Sword", "Chainmail", "Lucky Charm"],
            3: ["Greatsword", "Plate Mail", "Hero Ring"]
        }

        self.setup_main_menu()

    def setup_main_menu(self):
        self.main_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.main_frame.pack(expand=True, fill="both")

        tk.Label(self.main_frame, text="DUNGEON CRAWLER", font=("Courier", 24, "bold"), 
                 fg="white", bg=self.theme["bg"]).pady = 20
        tk.Label(self.main_frame, text="", bg=self.theme["bg"]).pack() # Spacer

        btn_style = {"font": ("Courier", 12), "width": 20, "pady": 5}
        
        tk.Button(self.main_frame, text="PLAY", command=self.open_game, **btn_style).pack(pady=5)
        tk.Button(self.main_frame, text="SETTINGS", command=self.open_settings, **btn_style).pack(pady=5)
        tk.Button(self.main_frame, text="QUIT", command=self.root.destroy, **btn_style).pack(pady=5)

    # --- Windows Logic ---
    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
        
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        
        tk.Label(self.settings_window, text="Themes:").pack()
        tk.Button(self.settings_window, text="Purple/Dark (Default)", command=lambda: self.set_theme("purple")).pack()
        tk.Button(self.settings_window, text="Forest/Green", command=lambda: self.set_theme("green")).pack()
        tk.Button(self.settings_window, text="Hell/Red", command=lambda: self.set_theme("red")).pack()
        
        tk.Checkbutton(self.settings_window, text="Use Emojis instead of Text Symbols", 
                       variable=self.use_emojis).pack(pady=10)

    def set_theme(self, color):
        if color == "purple": self.theme = {"bg": "#4B0082", "wall": "#2F4F4F", "floor": "#1A1A1A"}
        elif color == "green": self.theme = {"bg": "#006400", "wall": "#556B2F", "floor": "#002000"}
        elif color == "red": self.theme = {"bg": "#8B0000", "wall": "#3B0000", "floor": "#1A0000"}

    def open_game(self):
        self.root.withdraw()
        self.game_window = tk.Toplevel(self.root)
        self.game_window.title("In-Game")
        self.game_window.protocol("WM_DELETE_WINDOW", self.on_game_close)
        self.game_window.configure(bg="black")
        
        # Setup UI layout
        # Left: UI Stats & Inventory
        self.left_panel = tk.Frame(self.game_window, bg="#333333", width=300)
        self.left_panel.pack(side="left", fill="both")
        
        self.stats_label = tk.Label(self.left_panel, text="", fg="white", bg="#333333", justify="left", font=("Courier", 10))
        self.stats_label.pack(pady=10, padx=10)
        
        self.inv_canvas = tk.Canvas(self.left_panel, width=360, height=160, bg="#222222")
        self.inv_canvas.pack(pady=5)
        
        tk.Button(self.left_panel, text="UPGRADES", command=self.toggle_upgrades).pack(pady=5)

        # Right: Game Canvas
        self.right_panel = tk.Frame(self.game_window, bg="black")
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.right_panel, width=MAP_WIDTH*GRID_SIZE, height=MAP_HEIGHT*GRID_SIZE, bg="black")
        self.canvas.pack(pady=5, padx=5)
        
        self.terminal = tk.Text(self.right_panel, height=6, width=50, bg="black", fg="#00FF00", font=("Courier", 9))
        self.terminal.pack(fill="x", padx=5, pady=5)
        self.terminal.bind("<Key>", self.handle_konami)

        self.running = True
        self.generate_level()
        self.update_ui()
        
        # Bind Movement
        self.game_window.bind("<Up>", lambda e: self.move_player(0, -1))
        self.game_window.bind("<Down>", lambda e: self.move_player(0, 1))
        self.game_window.bind("<Left>", lambda e: self.move_player(-1, 0))
        self.game_window.bind("<Right>", lambda e: self.move_player(1, 0))
        self.game_window.bind("<space>", lambda e: self.interact())
        
        # Start game thread
        self.game_thread = threading.Thread(target=self.game_loop, daemon=True)
        self.game_thread.start()

    # --- Game Logic ---
    def generate_level(self):
        self.map_data = []
        # Simple procedural: fill with walls, then dig a room
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                is_wall = (x == 0 or y == 0 or x == MAP_WIDTH-1 or y == MAP_HEIGHT-1)
                self.map_data.append({"x": x, "y": y, "wall": is_wall, "type": "floor"})

        # Place Stairs
        self.stairs_pos = {"x": MAP_WIDTH-2, "y": MAP_HEIGHT-2}
        
        # Place Chest
        self.chest_pos = {"x": random.randint(2, 5), "y": random.randint(2, 5)}
        
        # Spawn Monsters
        self.monsters = []
        for _ in range(2 + self.floor_count):
            mx, my = random.randint(2, 8), random.randint(2, 8)
            self.monsters.append(Monster("Skeleton", mx, my, 30 + (self.floor_count*10)))

        self.render_map()

    def render_map(self):
        self.canvas.delete("all")
        for tile in self.map_data:
            color = self.theme["wall"] if tile["wall"] else self.theme["floor"]
            self.canvas.create_rectangle(tile["x"]*GRID_SIZE, tile["y"]*GRID_SIZE, 
                                         (tile["x"]+1)*GRID_SIZE, (tile["y"]+1)*GRID_SIZE, fill=color, outline="#444")
        
        # Draw Stairs
        char = "▼" if not self.use_emojis.get() else "stairs.png"
        self.draw_sprite(self.stairs_pos["x"], self.stairs_pos["y"], "STAIRS", "blue", "🪜")
        
        # Draw Chest
        self.draw_sprite(self.chest_pos["x"], self.chest_pos["y"], "CHEST", "brown", "📦")

        # Draw Monsters
        for m in self.monsters:
            if m.hp > 0:
                self.draw_sprite(m.x, m.y, "M", "red", "💀")
                # Health bar above monster
                fill_w = (m.hp / m.max_hp) * GRID_SIZE
                self.canvas.create_rectangle(m.x*GRID_SIZE, m.y*GRID_SIZE-5, m.x*GRID_SIZE+GRID_SIZE, m.y*GRID_SIZE-2, fill="red")
                self.canvas.create_rectangle(m.x*GRID_SIZE, m.y*GRID_SIZE-5, m.x*GRID_SIZE+fill_w, m.y*GRID_SIZE-2, fill="green")

        # Draw Player
        self.draw_sprite(self.player["pos"]["x"], self.player["pos"]["y"], "@", "yellow", "🧙")

    def draw_sprite(self, x, y, text, color, emoji):
        # In a real scenario, we'd try loading an image here.
        # Logic: If image exists, draw it. Else draw the fallback (Emoji or Text).
        display_text = emoji if self.use_emojis.get() else text
        self.canvas.create_text(x*GRID_SIZE + 20, y*GRID_SIZE + 20, text=display_text, fill=color, font=("Arial", 18))

    def move_player(self, dx, dy):
        if not self.running: return
        nx, ny = self.player["pos"]["x"] + dx, self.player["pos"]["y"] + dy
        
        # Collision
        for tile in self.map_data:
            if tile["x"] == nx and tile["y"] == ny and tile["wall"]:
                return
        
        # Combat check
        for m in self.monsters:
            if m.x == nx and m.y == ny and m.hp > 0:
                dmg = self.player["stats"]["dmg"]
                m.hp -= dmg
                self.log(f"You hit {m.name} for {dmg} damage!")
                self.end_turn()
                return

        self.player["pos"]["x"] = nx
        self.player["pos"]["y"] = ny
        self.end_turn()

    def end_turn(self):
        self.turn_count += 1
        # Monster Logic
        for m in self.monsters:
            if m.hp > 0:
                m.act(self.player, self.map_data)
                if m.x == self.player["pos"]["x"] and m.y == self.player["pos"]["y"]:
                    # Simple push-back logic if monster moves onto player
                    dmg = max(1, 5 - self.player["stats"]["def"])
                    self.player["stats"]["hp"] -= dmg
                    self.log(f"{m.name} bites you for {dmg} damage!")
        
        if self.player["stats"]["hp"] <= 0:
            self.game_over()
        
        self.render_map()
        self.update_ui()

    def interact(self):
        px, py = self.player["pos"]["x"], self.player["pos"]["y"]
        if px == self.stairs_pos["x"] and py == self.stairs_pos["y"]:
            self.floor_count += 1
            self.log(f"Descending to Floor {self.floor_count}...")
            self.generate_level()
        elif px == self.chest_pos["x"] and py == self.chest_pos["y"]:
            item = random.choice(self.loot_table.get(min(self.floor_count, 3), ["Rusty Sword"]))
            self.log(f"Found a {item}!")
            self.add_to_inventory(item)
            self.chest_pos = {"x": -1, "y": -1} # Remove chest

    def add_to_inventory(self, item):
        # Basic auto-placement logic
        for r in range(INVENTORY_ROWS):
            for c in range(INVENTORY_COLS):
                if (c, r) not in self.player["inventory"].values():
                    self.player["inventory"][item] = (c, r)
                    self.update_ui()
                    return

    def update_ui(self):
        stats = self.player["stats"]
        txt = f"HP: {stats['hp']}/{stats['max_hp']}\nXP: {stats['xp']}\nDMG: {stats['dmg']} | DEF: {stats['def']}\nFloor: {self.floor_count} | Turn: {self.turn_count}"
        self.stats_label.config(text=txt)
        
        # Render Inventory Grid
        self.inv_canvas.delete("all")
        for r in range(INVENTORY_ROWS):
            for c in range(INVENTORY_COLS):
                x, y = c*40, r*40
                self.inv_canvas.create_rectangle(x, y, x+40, y+40, outline="gray")
        
        for item, pos in self.player["inventory"].items():
            ix, iy = pos
            self.inv_canvas.create_text(ix*40+20, iy*40+20, text=item[0], fill="white")

    def toggle_upgrades(self):
        if self.upgrade_frame:
            self.upgrade_frame.destroy()
            self.upgrade_frame = None
            return
        
        self.upgrade_frame = tk.Frame(self.left_panel, bg="#444444")
        self.upgrade_frame.place(x=0, y=100, width=360, height=200)
        tk.Label(self.upgrade_frame, text="UPGRADES (Cost: 10 XP)", bg="#444444", fg="gold").pack()
        
        def buy(stat):
            if self.player["stats"]["xp"] >= 10:
                self.player["stats"]["xp"] -= 10
                self.player["stats"][stat] += 2
                self.log(f"Upgraded {stat}!")
                self.update_ui()

        tk.Button(self.upgrade_frame, text="+Dmg", command=lambda: buy("dmg")).pack()
        tk.Button(self.upgrade_frame, text="+HP", command=lambda: buy("max_hp")).pack()
        tk.Button(self.upgrade_frame, text="Close", command=self.toggle_upgrades).pack()

    def handle_konami(self, event):
        key = event.keysym
        self.konami_buffer.append(key)
        if self.konami_buffer[-10:] == self.konami_code:
            self.log("CHEAT MODE ACTIVATED")
            self.konami_unlocked = True
            self.terminal.config(state="normal")
        
        if self.konami_unlocked and key == "Return":
            cmd = self.terminal.get("end-2l", "end-1c").strip()
            if "+hp" in cmd: self.player["stats"]["hp"] = 999
            if "+def" in cmd: self.player["stats"]["def"] = 99
            self.update_ui()

    def log(self, msg):
        self.terminal.insert("end", msg + "\n")
        self.terminal.see("end")

    def game_over(self):
        self.running = False
        tk.Label(self.right_panel, text="GAME OVER", fg="red", bg="black", font=("Arial", 30)).place(relx=0.5, rely=0.5, anchor="center")

    def game_loop(self):
        while self.running:
            time.sleep(0.1)

    def on_game_close(self):
        self.running = False
        self.root.deiconify()
        self.game_window.destroy()

class Monster:
    def __init__(self, name, x, y, hp):
        self.name = name
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp

    def act(self, player, map_data):
        px, py = player["pos"]["x"], player["pos"]["y"]
        dist = math.sqrt((px - self.x)**2 + (py - self.y)**2)
        
        if dist < 5:
            # Simple AI: move toward player if not adjacent
            if dist > 1.5:
                if px > self.x: self.x += 1
                elif px < self.x: self.x -= 1
                elif py > self.y: self.y += 1
                elif py < self.y: self.y -= 1

if __name__ == "__main__":
    game = RoguelikeGame()
    game.root.mainloop()