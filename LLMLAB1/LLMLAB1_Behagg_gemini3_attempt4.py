import tkinter as tk
from tkinter import ttk, messagebox
import math
import random
import time
import threading

# --- Configuration & Constants ---
CANVAS_WIDTH = 600
CANVAS_HEIGHT = 400
TILE_SIZE = 40
GRID_W = CANVAS_WIDTH // TILE_SIZE
GRID_H = CANVAS_HEIGHT // TILE_SIZE

class RogueGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dungeon Crawler OS")
        self.root.geometry("300x400")
        
        # Windows management
        self.game_window = None
        self.settings_window = None
        self.upgrade_window = None
        
        # Settings
        self.settings = {
            "theme": "Purple",
            "display_mode": "Text", # Options: Text, Emoji, Images
            "bg_color": "#2E1A47",
            "wall_color": "#3D3D4D"
        }
        
        # Konami Code state
        self.konami_sequence = []
        self.target_konami = ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]
        self.cheats_enabled = False

        self.setup_main_menu()
        
    def setup_main_menu(self):
        self.frame = tk.Frame(self.root, bg=self.settings["bg_color"])
        self.frame.pack(fill="both", expand=True)
        
        tk.Label(self.frame, text="PY-DUNGEON", font=("Courier", 24, "bold"), 
                 fg="white", bg=self.settings["bg_color"]).pady = 20
        tk.Label(self.frame, text="A Roguelike Adventure", fg="#A0A0A0", 
                 bg=self.settings["bg_color"]).pack()
        
        btn_style = {"width": 15, "pady": 5, "bg": "#4B0082", "fg": "white", "font": ("Arial", 12)}
        
        tk.Button(self.frame, text="Play", command=self.open_game, **btn_style).pack(pady=10)
        tk.Button(self.frame, text="Settings", command=self.open_settings, **btn_style).pack(pady=10)
        tk.Button(self.frame, text="Quit", command=self.root.destroy, **btn_style).pack(pady=10)

    # --- Window Management ---
    def open_settings(self):
        if self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift()
            return
            
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        
        tk.Label(self.settings_window, text="Select Theme:").pack()
        theme_var = tk.StringVar(value=self.settings["theme"])
        themes = {"Purple": ("#2E1A47", "#3D3D4D"), "Green": ("#1A4721", "#3D4D3E"), "Red": ("#471A1A", "#4D3D3D")}
        
        def update_theme():
            self.settings["theme"] = theme_var.get()
            self.settings["bg_color"], self.settings["wall_color"] = themes[self.settings["theme"]]
            
        for t in themes:
            tk.Radiobutton(self.settings_window, text=t, variable=theme_var, value=t, command=update_theme).pack()

        tk.Label(self.settings_window, text="Display Mode:").pack()
        disp_var = tk.StringVar(value=self.settings["display_mode"])
        for m in ["Text", "Emoji", "Images"]:
            tk.Radiobutton(self.settings_window, text=m, variable=disp_var, value=m, 
                           command=lambda: self.settings.update({"display_mode": disp_var.get()})).pack()

    def open_game(self):
        self.root.withdraw()
        self.game_window = tk.Toplevel(self.root)
        self.game_window.title("Dungeon Crawler")
        self.game_window.protocol("WM_DELETE_WINDOW", self.on_close_game)
        
        self.init_game_state()
        self.setup_game_ui()
        
        # Start game logic thread
        self.game_running = True
        self.logic_thread = threading.Thread(target=self.game_loop, daemon=True)
        self.logic_thread.start()
        
        self.game_window.bind("<Key>", self.handle_input)

    def on_close_game(self):
        self.game_running = False
        self.root.destroy()

    # --- Game Logic ---
    def init_game_state(self):
        self.player = {
            "stats": {"hp": 100, "max_hp": 100, "dmg": 10, "def": 2, "speed": 1, "xp": 0},
            "pos": [1, 1],
            "inventory": {}, # {item_name: (x, y)}
            "hotbar": {},
            "equipped": []
        }
        self.turn_count = 0
        self.floor_count = 1
        self.entities = [] # Monsters
        self.map_data = [] # List of (x, y, type)
        self.loot_tables = {
            1: ["Rusty Sword", "Leather Cap", "Health Potion"],
            2: ["Steel Blade", "Iron Plate", "Large Potion"],
            3: ["Demon Slayer", "Dragon Scale", "Elixir"]
        }
        self.item_stats = {
            "Rusty Sword": {"dmg": 5}, "Steel Blade": {"dmg": 12}, "Demon Slayer": {"dmg": 25},
            "Leather Cap": {"def": 1}, "Iron Plate": {"def": 5}, "Dragon Scale": {"def": 10},
            "Health Potion": {"hp": 20}, "Large Potion": {"hp": 50}, "Elixir": {"hp": 100}
        }
        self.generate_floor()

    def generate_floor(self):
        self.map_data = []
        self.entities = []
        # Basic layout: Border walls
        for x in range(GRID_W):
            for y in range(GRID_H):
                if x == 0 or x == GRID_W-1 or y == 0 or y == GRID_H-1:
                    self.map_data.append({"pos": (x, y), "type": "wall"})
        
        # Random internal walls
        for _ in range(15):
            wx, wy = random.randint(2, GRID_W-2), random.randint(2, GRID_H-2)
            if (wx, wy) != (1, 1):
                self.map_data.append({"pos": (wx, wy), "type": "wall"})

        # Staircase
        self.stair_pos = (GRID_W-2, GRID_H-2)
        self.map_data.append({"pos": self.stair_pos, "type": "staircase"})

        # Chest
        self.chest_pos = (random.randint(2, GRID_W-2), random.randint(2, GRID_H-2))
        self.map_data.append({"pos": self.chest_pos, "type": "chest"})

        # Enemies
        for _ in range(2 + self.floor_count):
            ex, ey = random.randint(3, GRID_W-2), random.randint(3, GRID_H-2)
            self.entities.append(Enemy("Goblin", 30, 5, [ex, ey]))

    def setup_game_ui(self):
        self.main_container = tk.Frame(self.game_window, bg="black")
        self.main_container.pack()

        # Left Panel: Stats and Inventory
        self.left_panel = tk.Frame(self.main_container, width=250, bg="#222")
        self.left_panel.pack(side="left", fill="y")
        
        self.stat_label = tk.Label(self.left_panel, text="", fg="white", bg="#222", justify="left")
        self.stat_label.pack(pady=10)
        
        self.inv_canvas = tk.Canvas(self.left_panel, width=200, height=300, bg="#333")
        self.inv_canvas.pack()
        
        tk.Button(self.left_panel, text="Upgrades", command=self.toggle_upgrades).pack(pady=5)

        # Right Panel: Game and Log
        self.right_panel = tk.Frame(self.main_container)
        self.right_panel.pack(side="right")
        
        self.canvas = tk.Canvas(self.right_panel, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=self.settings["bg_color"])
        self.canvas.pack()
        
        self.log_text = tk.Text(self.right_panel, height=6, width=70, bg="black", fg="lime")
        self.log_text.pack()
        
        self.cheat_entry = tk.Entry(self.right_panel, bg="#111", fg="yellow", insertbackground="white")
        self.cheat_entry.bind("<Return>", self.process_cheat)

    def log(self, msg):
        self.log_text.insert("end", f"> {msg}\n")
        self.log_text.see("end")

    def handle_input(self, event):
        # Konami Tracking
        self.konami_sequence.append(event.keysym)
        if self.konami_sequence == self.target_konami[:len(self.konami_sequence)]:
            if len(self.konami_sequence) == len(self.target_konami):
                self.cheats_enabled = True
                self.log("CHEATS ENABLED. Input terminal active.")
                self.cheat_entry.pack(fill="x")
                self.konami_sequence = []
        else:
            self.konami_sequence = []

        # Movement
        dx, dy = 0, 0
        if event.keysym in ["Up", "w", "W"]: dy = -1
        elif event.keysym in ["Down", "s", "S"]: dy = 1
        elif event.keysym in ["Left", "a", "A"]: dx = -1
        elif event.keysym in ["Right", "d", "D"]: dx = 1
        elif event.keysym == "space":
            self.interact()
            return

        if dx != 0 or dy != 0:
            self.move_player(dx, dy)

    def move_player(self, dx, dy):
        new_x = self.player["pos"][0] + dx
        new_y = self.player["pos"][1] + dy
        
        # Wall Collision
        if any(m["pos"] == (new_x, new_y) and m["type"] == "wall" for m in self.map_data):
            return
            
        # Enemy Collision (Attack)
        for e in self.entities:
            if e.pos == [new_x, new_y]:
                dmg = self.player["stats"]["dmg"]
                e.hp -= dmg
                self.log(f"You hit {e.name} for {dmg}!")
                if e.hp <= 0:
                    self.entities.remove(e)
                    self.player["stats"]["xp"] += 20
                    self.log(f"{e.name} died! +20 XP")
                self.end_turn()
                return

        self.player["pos"] = [new_x, new_y]
        self.end_turn()

    def interact(self):
        pos = tuple(self.player["pos"])
        if pos == self.stair_pos:
            self.floor_count += 1
            self.log(f"Descended to floor {self.floor_count}")
            self.generate_floor()
        elif pos == self.chest_pos:
            table = self.loot_tables.get(self.floor_count, self.loot_tables[3])
            item = random.choice(table)
            self.log(f"Found {item}!")
            self.add_to_inventory(item)
            # Remove chest
            self.map_data = [m for m in self.map_data if m["pos"] != pos]
        self.end_turn()

    def add_to_inventory(self, item):
        # Simplified grid logic: find first free slot
        for y in range(3):
            for x in range(9):
                slot = (x, y)
                if slot not in self.player["inventory"].values():
                    self.player["inventory"][item + f"_{random.random()}"] = slot
                    return

    def end_turn(self):
        self.turn_count += 1
        # Enemy Turn
        for e in self.entities:
            e.act(self.player, self.map_data)
        
        if self.player["stats"]["hp"] <= 0:
            self.game_running = False
            messagebox.showinfo("Game Over", f"You died on floor {self.floor_count}")
            self.on_close_game()

    def game_loop(self):
        while self.game_running:
            self.update_ui()
            time.sleep(0.1)

    def update_ui(self):
        self.canvas.delete("all")
        # Draw Map
        for m in self.map_data:
            color = self.settings["wall_color"] if m["type"] == "wall" else "brown"
            char = "#" if m["type"] == "wall" else "C" if m["type"] == "chest" else "▼"
            self.draw_tile(m["pos"][0], m["pos"][1], color, char)
            
        # Draw Player
        self.draw_tile(self.player["pos"][0], self.player["pos"][1], "blue", "@")
        
        # Draw Enemies
        for e in self.entities:
            self.draw_tile(e.pos[0], e.pos[1], "red", e.name[0])

        # Update Stats
        s = self.player["stats"]
        self.stat_label.config(text=f"HP: {s['hp']}/{s['max_hp']}\nXP: {s['xp']}\nFloor: {self.floor_count}\nTurns: {self.turn_count}")

    def draw_tile(self, x, y, color, char):
        x1, y1 = x * TILE_SIZE, y * TILE_SIZE
        mode = self.settings["display_mode"]
        
        if mode == "Images":
            # Image logic would go here, fallback to text if fail
            self.canvas.create_rectangle(x1, y1, x1+TILE_SIZE, y1+TILE_SIZE, fill=color, outline="gray")
        
        self.canvas.create_text(x1+20, y1+20, text=char, fill="white", font=("Arial", 18))

    def toggle_upgrades(self):
        if self.upgrade_window and self.upgrade_window.winfo_exists():
            self.upgrade_window.destroy()
            return
            
        self.upgrade_window = tk.Toplevel(self.game_window)
        self.upgrade_window.geometry("200x300")
        tk.Label(self.upgrade_window, text="Upgrades (Cost 50 XP)").pack()
        
        def buy(stat):
            if self.player["stats"]["xp"] >= 50:
                self.player["stats"]["xp"] -= 50
                if stat == "hp": self.player["stats"]["max_hp"] += 20
                else: self.player["stats"][stat] += 2
                self.log(f"Upgraded {stat}!")

        tk.Button(self.upgrade_window, text="+Max HP", command=lambda: buy("hp")).pack(pady=5)
        tk.Button(self.upgrade_window, text="+DMG", command=lambda: buy("dmg")).pack(pady=5)
        tk.Button(self.upgrade_window, text="+DEF", command=lambda: buy("def")).pack(pady=5)

    def process_cheat(self, event):
        cmd = self.cheat_entry.get()
        if cmd == "+hp": self.player["stats"]["hp"] = 999
        elif cmd == "+def": self.player["stats"]["def"] += 50
        elif cmd == "+dmg": self.player["stats"]["dmg"] += 50
        self.cheat_entry.delete(0, "end")
        self.log("Cheat Applied!")

class Enemy:
    def __init__(self, name, hp, dmg, pos):
        self.name = name
        self.hp = hp
        self.dmg = dmg
        self.pos = pos

    def act(self, player, map_data):
        px, py = player["pos"]
        ex, ey = self.pos
        dist = math.sqrt((px-ex)**2 + (py-ey)**2)
        
        if dist < 1.5: # Adjacent
            actual_dmg = max(0, self.dmg - player["stats"]["def"])
            player["stats"]["hp"] -= actual_dmg
        elif dist < 5: # Chase
            dx = 1 if px > ex else -1 if px < ex else 0
            dy = 1 if py > ey else -1 if py < ey else 0
            
            new_pos = [ex + dx, ey + dy]
            # Simple collision check
            if not any(m["pos"] == tuple(new_pos) for m in map_data):
                if new_pos != player["pos"]:
                    self.pos = new_pos

if __name__ == "__main__":
    game = RogueGame()
    game.root.mainloop()