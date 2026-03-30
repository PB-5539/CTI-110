import tkinter as tk
from tkinter import messagebox
import math
import random
import time
import threading

# --- Constants & Configuration ---
TILE_SIZE = 40
GRID_WIDTH = 12
GRID_HEIGHT = 10
THEMES = {
    "Purple": {"bg": "#2e1a47", "wall": "#3b3b58", "floor": "#1a1a2e", "text": "white"},
    "Green": {"bg": "#1a472a", "wall": "#2d583b", "floor": "#0f1f14", "text": "white"},
    "Red": {"bg": "#471a1a", "wall": "#582d2d", "floor": "#1f0f0f", "text": "white"}
}

class GameEngine:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python Roguelike")
        self.root.geometry("900x700")
        
        # State Management
        self.current_theme = "Purple"
        self.use_emojis = True
        self.game_running = False
        self.cheat_enabled = False
        self.konami_progress = []
        self.konami_code = ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]
        
        self.player_data = {
            "stats": {"hp": 100, "max_hp": 100, "dmg": 10, "def": 5, "speed": 1, "xp": 0, "level": 1},
            "pos": [1, 1],
            "inventory": {}, # {item_name: (grid_x, grid_y)}
            "hotbar": {},
            "equipped": []
        }
        
        self.item_stats = {
            "Rusty Sword": {"dmg": 5, "def": 0},
            "Leather Shield": {"dmg": 0, "def": 3},
            "Magic Ring": {"dmg": 2, "def": 2}
        }
        
        self.loot_tables = {
            1: ["Rusty Sword", "Leather Shield"],
            2: ["Rusty Sword", "Leather Shield", "Magic Ring"],
            3: ["Magic Ring"]
        }
        
        self.floor = 1
        self.turns = 0
        self.entities = [] # Monsters, Chests, Stairs
        self.map_data = []
        
        self.windows = {} # Track sub-windows
        self.setup_main_menu()

    def setup_main_menu(self):
        self.main_frame = tk.Frame(self.root, bg=THEMES[self.current_theme]["bg"])
        self.main_frame.pack(fill="both", expand=True)
        
        tk.Label(self.main_frame, text="DUNGEON CRAWLER", font=("Courier", 30, "bold"), 
                 bg=THEMES[self.current_theme]["bg"], fg="white").pady=20
        tk.Label(self.main_frame, text="ROGUE-LITE", font=("Courier", 15), 
                 bg=THEMES[self.current_theme]["bg"], fg="white").pack()
        
        btn_style = {"font": ("Courier", 14), "width": 20, "pady": 10}
        
        tk.Button(self.main_frame, text="PLAY", command=self.start_game, **btn_style).pack(pady=10)
        tk.Button(self.main_frame, text="SETTINGS", command=self.open_settings, **btn_style).pack(pady=10)
        tk.Button(self.main_frame, text="QUIT", command=self.root.destroy, **btn_style).pack(pady=10)

    def open_settings(self):
        if self.check_window("settings"): return
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("300x300")
        self.windows["settings"] = win
        
        tk.Label(win, text="Select Theme:").pack()
        for theme in THEMES.keys():
            tk.Button(win, text=theme, command=lambda t=theme: self.set_theme(t)).pack(fill="x")
            
        tk.Label(win, text="Visual Style:").pack(pady=10)
        tk.Button(win, text="Toggle Text/Emoji Icons", command=self.toggle_icons).pack()

    def set_theme(self, name):
        self.current_theme = name
        self.main_frame.config(bg=THEMES[name]["bg"])
        
    def toggle_icons(self):
        self.use_emojis = not self.use_emojis
        messagebox.showinfo("Setting Changed", f"Icons set to {'Emoji' if self.use_emojis else 'Text'}")

    def check_window(self, name):
        if name in self.windows and self.windows[name].winfo_exists():
            self.windows[name].lift()
            return True
        return False

    # --- Game Logic ---
    def start_game(self):
        self.game_win = tk.Toplevel(self.root)
        self.game_win.title("Dungeon")
        self.game_win.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.game_win.bind("<Key>", self.handle_input)
        
        self.game_running = True
        self.setup_game_ui()
        self.generate_level()
        
        # Start game loop thread
        self.loop_thread = threading.Thread(target=self.game_loop, daemon=True)
        self.loop_thread.start()

    def setup_game_ui(self):
        theme = THEMES[self.current_theme]
        self.game_win.config(bg=theme["bg"])
        
        # Left Panel (Stats & Inventory)
        self.left_panel = tk.Frame(self.game_win, bg=theme["bg"], width=300)
        self.left_panel.pack(side="left", fill="y", padx=10)
        
        self.stat_label = tk.Label(self.left_panel, text="", font=("Courier", 12), justify="left", bg=theme["bg"], fg="white")
        self.stat_label.pack(pady=10)
        
        tk.Button(self.left_panel, text="UPGRADES", command=self.toggle_upgrades).pack(fill="x")
        
        self.inv_canvas = tk.Canvas(self.left_panel, width=280, height=200, bg="#333333")
        self.inv_canvas.pack(pady=5)
        
        # Right Panel (Game Area)
        self.right_panel = tk.Frame(self.game_win, bg=theme["bg"])
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.right_panel, width=GRID_WIDTH*TILE_SIZE, height=GRID_HEIGHT*TILE_SIZE, bg=theme["floor"])
        self.canvas.pack(pady=10)
        
        self.terminal = tk.Entry(self.right_panel, bg="black", fg="green", font=("Courier", 10))
        self.terminal.pack(fill="x", side="bottom")
        self.terminal.bind("<Return>", self.process_command)
        
        self.log = tk.Text(self.right_panel, height=6, bg="black", fg="white", font=("Courier", 10))
        self.log.pack(fill="x", side="bottom")
        
        self.update_stats_ui()
        self.draw_inventory()

    def generate_level(self):
        self.canvas.delete("all")
        self.entities = []
        # Simple procedural-ish map: 0=floor, 1=wall
        self.map_data = [[1 if x==0 or x==GRID_WIDTH-1 or y==0 or y==GRID_HEIGHT-1 else 0 
                         for x in range(GRID_WIDTH)] for y in range(GRID_HEIGHT)]
        
        # Add random walls
        for _ in range(15):
            self.map_data[random.randint(1, GRID_HEIGHT-2)][random.randint(1, GRID_WIDTH-2)] = 1
            
        # Clear start and end
        self.map_data[1][1] = 0 
        self.player_data["pos"] = [1, 1]
        
        # Spawn Exit
        self.spawn_entity("stairs", "▼" if not self.use_emojis else "🪜")
        # Spawn Chest
        self.spawn_entity("chest", "C" if not self.use_emojis else "🎁")
        # Spawn Enemies
        for _ in range(2 + self.floor):
            self.spawn_entity("enemy", "S" if not self.use_emojis else "💀")

        self.draw_map()

    def spawn_entity(self, etype, char):
        while True:
            rx, ry = random.randint(1, GRID_WIDTH-2), random.randint(1, GRID_HEIGHT-2)
            if self.map_data[ry][rx] == 0 and [rx, ry] != self.player_data["pos"]:
                self.entities.append({
                    "type": etype, "pos": [rx, ry], "char": char, 
                    "hp": 20 + (self.floor * 5), "max_hp": 20 + (self.floor * 5)
                })
                break

    def draw_map(self):
        self.canvas.delete("all")
        theme = THEMES[self.current_theme]
        for y, row in enumerate(self.map_data):
            for x, tile in enumerate(row):
                color = theme["wall"] if tile == 1 else theme["floor"]
                self.canvas.create_rectangle(x*TILE_SIZE, y*TILE_SIZE, (x+1)*TILE_SIZE, (y+1)*TILE_SIZE, fill=color, outline="#444")
        
        # Draw Entities
        for e in self.entities:
            self.draw_sprite(e["pos"][0], e["pos"][1], e["char"], "red" if e["type"]=="enemy" else "yellow")
            if e["type"] == "enemy":
                # Mini health bar
                px, py = e["pos"][0]*TILE_SIZE, e["pos"][1]*TILE_SIZE
                self.canvas.create_rectangle(px, py-5, px+TILE_SIZE, py-2, fill="red")
                self.canvas.create_rectangle(px, py-5, px+(TILE_SIZE*(e["hp"]/e["max_hp"])), py-2, fill="green")

        # Draw Player
        p_icon = "@" if not self.use_emojis else "🧙"
        self.draw_sprite(self.player_data["pos"][0], self.player_data["pos"][1], p_icon, "cyan")

    def draw_sprite(self, x, y, char, color):
        # Fallback to text shapes as requested
        cx, cy = x*TILE_SIZE + TILE_SIZE//2, y*TILE_SIZE + TILE_SIZE//2
        if char in ["▼", "🪜", "C", "🎁"]: # Squares for objects
            self.canvas.create_rectangle(x*TILE_SIZE+5, y*TILE_SIZE+5, (x+1)*TILE_SIZE-5, (y+1)*TILE_SIZE-5, fill=color)
        else: # Circles for creatures
            self.canvas.create_oval(x*TILE_SIZE+5, y*TILE_SIZE+5, (x+1)*TILE_SIZE-5, (y+1)*TILE_SIZE-5, fill=color)
        
        self.canvas.create_text(cx, cy, text=char, fill="white", font=("Arial", 14, "bold"))

    # --- Interaction ---
    def handle_input(self, event):
        if not self.game_running: return
        
        dx, dy = 0, 0
        key = event.keysym
        
        if key in ["Up", "w", "W"]: dy = -1
        elif key in ["Down", "s", "S"]: dy = 1
        elif key in ["Left", "a", "A"]: dx = -1
        elif key in ["Right", "d", "D"]: dx = 1
        elif key == "space": self.interact(); return
        
        # Konami check
        self.konami_progress.append(key)
        if self.konami_progress == self.konami_code[:len(self.konami_progress)]:
            if len(self.konami_progress) == len(self.konami_code):
                self.log_msg("CHEATS ENABLED")
                self.cheat_enabled = True
        else: self.konami_progress = []

        if dx != 0 or dy != 0:
            self.move_player(dx, dy)

    def move_player(self, dx, dy):
        new_x = self.player_data["pos"][0] + dx
        new_y = self.player_data["pos"][1] + dy
        
        # Wall Collision
        if self.map_data[new_y][new_x] == 1: return
        
        # Enemy Collision (Attack)
        for e in self.entities:
            if e["pos"] == [new_x, new_y] and e["type"] == "enemy":
                self.attack_enemy(e)
                self.end_turn()
                return
        
        self.player_data["pos"] = [new_x, new_y]
        self.end_turn()

    def attack_enemy(self, enemy):
        dmg = self.player_data["stats"]["dmg"]
        enemy["hp"] -= dmg
        self.log_msg(f"You hit enemy for {dmg}!")
        if enemy["hp"] <= 0:
            self.entities.remove(enemy)
            self.player_data["stats"]["xp"] += 10
            self.log_msg("Enemy defeated!")

    def interact(self):
        px, py = self.player_data["pos"]
        for e in self.entities:
            if e["pos"] == [px, py]:
                if e["type"] == "stairs":
                    self.floor += 1
                    self.log_msg(f"Descending to floor {self.floor}...")
                    self.generate_level()
                elif e["type"] == "chest":
                    item = random.choice(self.loot_tables.get(self.floor, ["Rusty Sword"]))
                    self.add_to_inventory(item)
                    self.entities.remove(e)
                    self.log_msg(f"Found {item}!")
                    self.draw_map()
                return

    def end_turn(self):
        self.turns += 1
        # Enemy AI
        for e in self.entities:
            if e["type"] == "enemy":
                self.enemy_ai(e)
        
        self.update_stats_ui()
        self.draw_map()
        
        if self.player_data["stats"]["hp"] <= 0:
            self.game_over()

    def enemy_ai(self, e):
        px, py = self.player_data["pos"]
        ex, ey = e["pos"]
        dist = math.sqrt((px-ex)**2 + (py-ey)**2)
        
        if dist < 1.5: # Adjacent
            dmg = max(0, 5 + self.floor - self.player_data["stats"]["def"])
            self.player_data["stats"]["hp"] -= dmg
            self.log_msg(f"Enemy dealt {dmg} damage!")
        elif dist < 5: # Chase
            dx = 1 if px > ex else -1 if px < ex else 0
            dy = 1 if py > ey else -1 if py < ey else 0
            
            # Check for simple obstruction
            nx, ny = ex + dx, ey + dy
            if self.map_data[ny][nx] == 0 and not any(ent["pos"] == [nx, ny] for ent in self.entities):
                e["pos"] = [nx, ny]

    def log_msg(self, text):
        self.log.insert("1.0", f"Turn {self.turns}: {text}\n")

    def update_stats_ui(self):
        s = self.player_data["stats"]
        txt = f"HP: {s['hp']}/{s['max_hp']}\nDMG: {s['dmg']} | DEF: {s['def']}\nXP: {s['xp']} | Floor: {self.floor}\nTurn: {self.turns}"
        self.stat_label.config(text=txt)

    # --- Inventory & Upgrades ---
    def add_to_inventory(self, item):
        # Find first empty slot in 9x3 grid
        for y in range(3):
            for x in range(9):
                if (x, y) not in self.player_data["inventory"].values():
                    self.player_data["inventory"][item] = (x, y)
                    self.draw_inventory()
                    return

    def draw_inventory(self):
        self.inv_canvas.delete("all")
        # Draw 9x3 grid
        for y in range(3):
            for x in range(9):
                self.inv_canvas.create_rectangle(x*30+5, y*30+5, (x+1)*30+5, (y+1)*30+5, outline="gray")
        
        # Items
        for name, pos in self.player_data["inventory"].items():
            ix, iy = pos
            self.inv_canvas.create_rectangle(ix*30+7, iy*30+7, (ix+1)*30+3, (iy+1)*30+3, fill="gold")

    def toggle_upgrades(self):
        if self.check_window("upgrades"): return
        win = tk.Toplevel(self.root)
        win.title("Upgrades")
        self.windows["upgrades"] = win
        
        s = self.player_data["stats"]
        tk.Label(win, text=f"XP Available: {s['xp']}").pack()
        
        def buy(stat):
            if s['xp'] >= 20 or self.cheat_enabled:
                if not self.cheat_enabled: s['xp'] -= 20
                if stat == 'hp': s['max_hp'] += 20; s['hp'] += 20
                else: s[stat] += 2
                self.update_stats_ui()
                messagebox.showinfo("Upgraded", f"{stat} increased!")
        
        tk.Button(win, text="Build Health (20 XP)", command=lambda: buy('hp')).pack(fill="x")
        tk.Button(win, text="Sharpen Blade (20 XP)", command=lambda: buy('dmg')).pack(fill="x")
        tk.Button(win, text="Toughen Skin (20 XP)", command=lambda: buy('def')).pack(fill="x")

    def process_command(self, event):
        if not self.cheat_enabled: return
        cmd = self.terminal.get()
        self.terminal.delete(0, tk.END)
        
        if cmd == "+hp": self.player_data["stats"]["hp"] += 100
        elif cmd == "+def": self.player_data["stats"]["def"] += 10
        elif cmd == "+dmg": self.player_data["stats"]["dmg"] += 10
        self.update_stats_ui()

    def game_loop(self):
        while self.game_running:
            # Main logic is turn-based, so this thread just keeps 
            # the process alive or handles animations if needed.
            time.sleep(0.1)

    def game_over(self):
        self.game_running = False
        messagebox.showinfo("Game Over", f"You died on Floor {self.floor} after {self.turns} turns.")
        self.game_win.destroy()
        self.setup_main_menu()

if __name__ == "__main__":
    game = GameEngine()
    game.root.mainloop()