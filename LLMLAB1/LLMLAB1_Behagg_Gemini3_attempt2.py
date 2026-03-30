import tkinter as tk
from tkinter import ttk
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

# --- Game Logic Class ---
class RoguelikeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Dungeon Crawler")
        self.root.geometry("1000x700")
        
        # Settings Variables
        self.theme = tk.StringVar(value="Purple")
        self.visual_style = tk.StringVar(value="Emoji") # Options: Emoji, Text
        self.themes = {
            "Purple": {"bg": "#2E1A47", "dungeon": "#3B3B4D", "text": "white"},
            "Green": {"bg": "#1A301A", "dungeon": "#2D3D2D", "text": "#00FF00"},
            "Red": {"bg": "#301A1A", "dungeon": "#4D2D2D", "text": "#FF4444"}
        }

        # Player Data Structure
        self.player = {
            "stats": {"hp": 100, "max_hp": 100, "dmg": 10, "def": 2, "dodge": 5, "speed": 1, "xp": 0, "level": 1},
            "pos": [1, 1],
            "inventory": {}, # {item_name: (x, y)}
            "hotbar": {},
            "equipment": {"weapon": None, "armor": None}
        }
        
        self.item_stats = {
            "Rusty Sword": {"dmg_mult": 1.2},
            "Iron Shield": {"def_bonus": 5},
            "Leather Tunic": {"dodge_mult": 1.1}
        }
        
        self.loot_table = {
            1: ["Rusty Sword", "Leather Tunic"],
            2: ["Iron Shield", "Steel Blade"],
            3: ["Great Axe", "Plate Armor"]
        }

        self.turn_count = 0
        self.floor_count = 1
        self.enemies = []
        self.map_data = []
        self.chests = []
        self.staircase = None
        self.konami_index = 0
        self.konami_code = ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]
        
        self.setup_main_menu()

    # --- UI Setup ---
    def setup_main_menu(self):
        self.main_menu = tk.Frame(self.root, bg="#2E1A47")
        self.main_menu.pack(fill="both", expand=True)
        
        tk.Label(self.main_menu, text="PY-DUNGEON", font=("Courier", 40, "bold"), bg="#2E1A47", fg="white").pady=50
        tk.Label(self.main_menu, text="A Python Roguelike", font=("Courier", 15), bg="#2E1A47", fg="gray").pack()
        
        btn_frame = tk.Frame(self.main_menu, bg="#2E1A47")
        btn_frame.pack(expand=True)

        tk.Button(btn_frame, text="PLAY", width=20, command=self.start_game).pack(pady=10)
        tk.Button(btn_frame, text="SETTINGS", width=20, command=self.open_settings).pack(pady=10)
        tk.Button(btn_frame, text="QUIT", width=20, command=self.root.destroy).pack(pady=10)

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("300x300")
        
        tk.Label(win, text="Theme:").pack()
        tk.OptionMenu(win, self.theme, *self.themes.keys()).pack()
        
        tk.Label(win, text="Fallback Visuals:").pack()
        tk.OptionMenu(win, self.visual_style, "Emoji", "Text").pack()
        
        tk.Button(win, text="Close", command=win.destroy).pack(pady=20)

    def start_game(self):
        self.game_window = tk.Toplevel(self.root)
        self.game_window.title("Dungeon")
        self.game_window.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.main_menu.pack_forget()
        
        current_theme = self.themes[self.theme.get()]
        self.game_window.configure(bg=current_theme["bg"])

        # Layout Frames
        self.left_panel = tk.Frame(self.game_window, bg=current_theme["bg"], width=300)
        self.left_panel.pack(side="left", fill="y", padx=10)
        
        self.right_panel = tk.Frame(self.game_window, bg=current_theme["bg"])
        self.right_panel.pack(side="right", fill="both", expand=True)

        # UI Stats
        self.hp_label = tk.Label(self.left_panel, text="HP: 100/100", fg="white", bg=current_theme["bg"])
        self.hp_label.pack()
        self.stats_label = tk.Label(self.left_panel, text="Floor: 1 | Turn: 0", fg="white", bg=current_theme["bg"])
        self.stats_label.pack()

        # Inventory Canvas
        self.inv_canvas = tk.Canvas(self.left_panel, width=280, height=400, bg="#111111")
        self.inv_canvas.pack(pady=10)
        
        self.upgrade_btn = tk.Button(self.left_panel, text="Upgrades", command=self.toggle_upgrade_menu)
        self.upgrade_btn.pack()

        # Game Canvas
        self.canvas = tk.Canvas(self.right_panel, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg=current_theme["dungeon"])
        self.canvas.pack(pady=10)

        # Terminal
        self.terminal = tk.Entry(self.right_panel, bg="black", fg="lime", insertbackground="white")
        self.terminal.pack(fill="x", side="bottom")
        self.terminal.bind("<Return>", self.process_command)
        
        self.log = tk.Text(self.right_panel, height=8, bg="black", fg="white", state="disabled")
        self.log.pack(fill="x", side="bottom")

        self.game_window.bind("<Key>", self.handle_input)
        
        self.generate_level()
        self.draw_game()
        self.draw_inventory()

    # --- Level Generation ---
    def generate_level(self):
        self.map_data = []
        # Simple floor grid
        for y in range(GRID_H):
            for x in range(GRID_W):
                if random.random() > 0.1: self.map_data.append((x, y))
        
        self.player["pos"] = list(random.choice(self.map_data))
        self.staircase = random.choice(self.map_data)
        
        # Spawn Enemies
        self.enemies = []
        for _ in range(3 + self.floor_count):
            pos = list(random.choice(self.map_data))
            self.enemies.append(Enemy("Skeleton", pos))
            
        # Spawn Chests
        self.chests = [random.choice(self.map_data) for _ in range(2)]

    # --- Drawing Logic ---
    def draw_game(self):
        self.canvas.delete("all")
        style = self.visual_style.get()
        
        # Draw Map
        for tile in self.map_data:
            x1, y1 = tile[0]*TILE_SIZE, tile[1]*TILE_SIZE
            self.canvas.create_rectangle(x1, y1, x1+TILE_SIZE, y1+TILE_SIZE, outline="#222222")

        # Draw Stairs
        sx, sy = self.staircase[0]*TILE_SIZE, self.staircase[1]*TILE_SIZE
        char = "▼" if style == "Emoji" else "S"
        self.canvas.create_text(sx+20, sy+20, text=char, fill="cyan", font=("Arial", 20))

        # Draw Chests
        for cx, cy in self.chests:
            char = "🎁" if style == "Emoji" else "C"
            self.canvas.create_text(cx*TILE_SIZE+20, cy*TILE_SIZE+20, text=char, fill="gold", font=("Arial", 20))

        # Draw Enemies
        for en in self.enemies:
            char = "💀" if style == "Emoji" else "E"
            self.canvas.create_text(en.pos[0]*TILE_SIZE+20, en.pos[1]*TILE_SIZE+20, text=char, fill="red", font=("Arial", 20))

        # Draw Player
        px, py = self.player["pos"][0]*TILE_SIZE, self.player["pos"][1]*TILE_SIZE
        char = "🧙" if style == "Emoji" else "@"
        self.canvas.create_text(px+20, py+20, text=char, fill="white", font=("Arial", 20))

    def draw_inventory(self):
        self.inv_canvas.delete("all")
        # 9x3 grid
        for r in range(3):
            for c in range(9):
                x, y = c*30 + 5, r*30 + 5
                self.inv_canvas.create_rectangle(x, y, x+28, y+28, outline="gray")
        # Hotbar 9x1
        for c in range(9):
            x, y = c*30 + 5, 350
            self.inv_canvas.create_rectangle(x, y, x+28, y+28, outline="white")

    # --- Game Logic ---
    def handle_input(self, event):
        # Konami check
        if event.keysym == self.konami_code[self.konami_index]:
            self.konami_index += 1
            if self.konami_index == len(self.konami_code):
                self.log_msg("CHEATS ENABLED. Use terminal.")
                self.konami_index = 0
        else:
            self.konami_index = 0

        dx, dy = 0, 0
        if event.keysym in ["Up", "w"]: dy = -1
        elif event.keysym in ["Down", "s"]: dy = 1
        elif event.keysym in ["Left", "a"]: dx = -1
        elif event.keysym in ["Right", "d"]: dx = 1
        elif event.keysym == "space":
            self.interact()
            return

        if dx != 0 or dy != 0:
            new_pos = [self.player["pos"][0] + dx, self.player["pos"][1] + dy]
            
            # Attack check
            target = None
            for en in self.enemies:
                if en.pos == new_pos:
                    target = en
                    break
            
            if target:
                self.attack_enemy(target)
                self.end_turn()
            elif tuple(new_pos) in self.map_data:
                self.player["pos"] = new_pos
                self.end_turn()
        
        self.draw_game()

    def attack_enemy(self, enemy):
        dmg = self.player["stats"]["dmg"]
        enemy.hp -= dmg
        self.log_msg(f"You hit {enemy.name} for {dmg} damage!")
        if enemy.hp <= 0:
            self.log_msg(f"{enemy.name} died! +10 XP")
            self.player["stats"]["xp"] += 10
            self.enemies.remove(enemy)

    def interact(self):
        pos = tuple(self.player["pos"])
        if pos == self.staircase:
            self.floor_count += 1
            self.log_msg(f"Descending to floor {self.floor_count}...")
            self.generate_level()
        elif pos in self.chests:
            loot = random.choice(self.loot_table.get(self.floor_count, ["Rusty Sword"]))
            self.log_msg(f"Found a {loot}!")
            self.player["inventory"][loot] = (0,0) # Simplified
            self.chests.remove(pos)
        self.draw_game()

    def end_turn(self):
        self.turn_count += 1
        # Enemy Logic
        for en in self.enemies:
            en.take_turn(self.player, self.map_data)
            if en.pos == self.player["pos"]: # Should not happen based on prompt logic
                pass 
        
        self.update_ui()
        if self.player["stats"]["hp"] <= 0:
            self.death_screen()

    def update_ui(self):
        p = self.player["stats"]
        self.hp_label.config(text=f"HP: {p['hp']}/{p['max_hp']}")
        self.stats_label.config(text=f"Floor: {self.floor_count} | Turn: {self.turn_count} | XP: {p['xp']}")

    def log_msg(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def toggle_upgrade_menu(self):
        up_win = tk.Toplevel(self.game_window)
        up_win.title("Upgrades")
        up_win.geometry("200x250")
        
        p = self.player["stats"]
        tk.Label(up_win, text=f"XP: {p['xp']}").pack()
        
        def upgrade(stat):
            if p["xp"] >= 20:
                p["xp"] -= 20
                if stat == "hp": p["max_hp"] += 20; p["hp"] += 20
                if stat == "dmg": p["dmg"] += 5
                if stat == "spd": p["speed"] += 1
                self.update_ui()
                up_win.destroy()

        tk.Button(up_win, text="+HP (20 XP)", command=lambda: upgrade("hp")).pack(pady=5)
        tk.Button(up_win, text="+DMG (20 XP)", command=lambda: upgrade("dmg")).pack(pady=5)
        tk.Button(up_win, text="+SPD (50 XP)", command=lambda: upgrade("spd")).pack(pady=5)

    def process_command(self, event):
        cmd = self.terminal.get()
        if cmd == "+hp": self.player["stats"]["hp"] += 100
        if cmd == "+def": self.player["stats"]["def"] += 10
        self.terminal.delete(0, "end")
        self.update_ui()

    def death_screen(self):
        ds = tk.Toplevel(self.root)
        ds.geometry("400x200")
        tk.Label(ds, text="YOU DIED", font=("Arial", 30), fg="red").pack(expand=True)
        tk.Button(ds, text="Main Menu", command=self.root.destroy).pack()

# --- Enemy Class ---
class Enemy:
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos
        self.hp = 30
        self.dmg = 5

    def take_turn(self, player, map_tiles):
        px, py = player["pos"]
        ex, ey = self.pos
        
        dist = math.sqrt((px-ex)**2 + (py-ey)**2)
        
        if dist < 1.5: # Adjacent
            player["stats"]["hp"] -= self.dmg
            # No movement
        elif dist < 5: # Chase
            dx = 1 if px > ex else -1 if px < ex else 0
            dy = 1 if py > ey else -1 if py < ey else 0
            
            new_pos = [ex + dx, ey + dy]
            # Simple collision check: move only if not onto player
            if new_pos != player["pos"] and tuple(new_pos) in map_tiles:
                self.pos = new_pos

# --- Main Run ---
if __name__ == "__main__":
    root = tk.Tk()
    game = RoguelikeGame(root)
    root.mainloop()