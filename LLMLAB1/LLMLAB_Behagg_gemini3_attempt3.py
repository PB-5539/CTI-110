import tkinter as tk
from tkinter import ttk
import math
import random
import time
import threading

# --- Constants & Configuration ---
WINDOW_WIDTH = 1000
WINDOW_HEIGHT = 700
GRID_SIZE = 40
INV_ROWS = 3
INV_COLS = 9
HOTBAR_COLS = 9

class DungeonGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python Roguelike")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        
        # State Management
        self.game_window = None
        self.settings_window = None
        self.upgrade_window_open = False
        
        # Settings
        self.theme = {
            "bg": "#2E1A47", # Medium dark purple
            "dungeon": "#2B2D42", # Dark blue-grey
            "text": "white"
        }
        self.use_emojis = tk.BooleanVar(value=True)
        self.konami_index = 0
        self.konami_code = ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]
        self.cheats_enabled = False

        # Player Data Structure
        self.player = {
            "stats": {"hp": 100, "max_hp": 100, "dmg": 10, "def": 5, "dodge": 5, "speed": 1, "xp": 0},
            "pos": [1, 1],
            "inventory": {}, # {item_name: (r, c)}
            "hotbar": {},
            "turn_count": 0,
            "floor": 1
        }
        
        self.loot_table = {
            1: ["Rusty Sword", "Iron Shield", "Health Potion"],
            2: ["Steel Blade", "Greatshield", "XP Tome"],
            3: ["Dragon Slayer", "Aegis", "Elixir"]
        }

        self.setup_main_menu()

    def setup_main_menu(self):
        self.main_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.main_frame.pack(fill="both", expand=True)

        tk.Label(self.main_frame, text="DUNGEON CRAWLER", font=("Courier", 40), 
                 fg="white", bg=self.theme["bg"]).pack(pady=50)

        btn_style = {"font": ("Courier", 15), "width": 20, "pady": 10}
        
        tk.Button(self.main_frame, text="PLAY", command=self.start_game, **btn_style).pack(pady=10)
        tk.Button(self.main_frame, text="SETTINGS", command=self.open_settings, **btn_style).pack(pady=10)
        tk.Button(self.main_frame, text="QUIT", command=self.root.destroy, **btn_style).pack(pady=10)

    # --- Windows Logic ---
    def open_settings(self):
        if self.settings_window is not None and tk.Toplevel.winfo_exists(self.settings_window):
            self.settings_window.lift()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Settings")
        self.settings_window.geometry("300x400")
        
        tk.Label(self.settings_window, text="Themes").pack(pady=5)
        tk.Button(self.settings_window, text="Purple (Default)", command=lambda: self.set_theme("#2E1A47", "#2B2D42")).pack()
        tk.Button(self.settings_window, text="Green", command=lambda: self.set_theme("#1A472E", "#1B241E")).pack()
        tk.Button(self.settings_window, text="Red", command=lambda: self.set_theme("#471A1A", "#241B1B")).pack()
        
        tk.Checkbutton(self.settings_window, text="Use Emojis", variable=self.use_emojis).pack(pady=20)

    def set_theme(self, bg, dungeon):
        self.theme["bg"] = bg
        self.theme["dungeon"] = dungeon
        self.main_frame.config(bg=bg)

    def start_game(self):
        self.root.withdraw()
        self.game_window = tk.Toplevel(self.root)
        self.game_window.title("In-Game")
        self.game_window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.game_window.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.game_window.bind("<Key>", self.handle_keypress)

        self.setup_game_ui()
        self.generate_level()
        
        # Start game logic thread
        self.game_running = True
        self.logic_thread = threading.Thread(target=self.game_loop, daemon=True)
        self.logic_thread.start()

    # --- UI & Rendering ---
    def setup_game_ui(self):
        # Left Panel (Stats & Inventory)
        self.left_panel = tk.Frame(self.game_window, width=350, bg="#1a1a1a")
        self.left_panel.pack(side="left", fill="y")

        self.stat_label = tk.Label(self.left_panel, text="", fg="white", bg="#1a1a1a", justify="left", font=("Courier", 10))
        self.stat_label.pack(pady=10, padx=10)

        self.inv_container = tk.Frame(self.left_panel, bg="grey")
        self.inv_container.pack(pady=5)
        self.render_inventory_grid()

        tk.Button(self.left_panel, text="UPGRADES", command=self.toggle_upgrades).pack(pady=10)

        # Right Panel (Game Canvas & Terminal)
        self.right_panel = tk.Frame(self.game_window, bg=self.theme["dungeon"])
        self.right_panel.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(self.right_panel, bg=self.theme["dungeon"], width=600, height=450, highlightthickness=0)
        self.canvas.pack(pady=10)

        self.terminal = tk.Text(self.right_panel, height=8, bg="black", fg="lime", state="disabled")
        self.terminal.pack(fill="x", padx=10, pady=5)
        
        self.cheat_entry = tk.Entry(self.right_panel, bg="#222", fg="yellow", insertbackground="white")
        self.cheat_entry.bind("<Return>", self.process_cheat)

    def render_inventory_grid(self):
        # Main Inventory 9x3
        for r in range(INV_ROWS):
            for c in range(INV_COLS):
                f = tk.Frame(self.inv_container, width=35, height=35, relief="sunken", borderwidth=1)
                f.grid(row=r, column=c, padx=1, pady=1)
        # Hotbar 9x1
        for c in range(HOTBAR_COLS):
            f = tk.Frame(self.inv_container, width=35, height=35, relief="ridge", borderwidth=2, bg="#444")
            f.grid(row=4, column=c, padx=1, pady=5)

    def log(self, message):
        self.terminal.config(state="normal")
        self.terminal.insert("end", f"> {message}\n")
        self.terminal.see("end")
        self.terminal.config(state="disabled")

    # --- Game Logic ---
    def generate_level(self):
        self.level_data = []
        self.enemies = []
        self.objects = {} # (x,y): type
        
        # Simple procedural-ish level
        for x in range(15):
            for y in range(11):
                if random.random() > 0.8 and (x,y) != (1,1):
                    self.level_data.append({'pos': (x,y), 'type': 'wall'})
                else:
                    self.level_data.append({'pos': (x,y), 'type': 'floor'})
        
        # Add staircase
        sx, sy = random.randint(10,14), random.randint(7,10)
        self.objects[(sx, sy)] = "stair"
        
        # Add chest
        self.objects[(random.randint(5,9), random.randint(2,5))] = "chest"

        # Add enemies
        for _ in range(2 + self.player["floor"]):
            ex, ey = random.randint(5, 14), random.randint(5, 10)
            self.enemies.append(Enemy("Skeleton", ex, ey))

        self.draw_game()

    def draw_game(self):
        if not self.game_window: return
        self.canvas.delete("all")
        
        # Draw Map
        for tile in self.level_data:
            x, y = tile['pos']
            color = "#111" if tile['type'] == 'wall' else "#333"
            self.canvas.create_rectangle(x*GRID_SIZE, y*GRID_SIZE, (x+1)*GRID_SIZE, (y+1)*GRID_SIZE, fill=color)

        # Draw Objects
        for (ox, oy), otype in self.objects.items():
            char = "▼" if otype == "stair" else "C"
            if self.use_emojis.get():
                char = "🪜" if otype == "stair" else "📦"
            self.canvas.create_text(ox*GRID_SIZE+20, oy*GRID_SIZE+20, text=char, fill="gold", font=("Arial", 20))

        # Draw Enemies
        for e in self.enemies:
            char = "S" if not self.use_emojis.get() else "💀"
            self.canvas.create_text(e.x*GRID_SIZE+20, e.y*GRID_SIZE+20, text=char, fill="red", font=("Arial", 20))

        # Draw Player
        p_char = "@" if not self.use_emojis.get() else "🧙"
        px, py = self.player["pos"]
        self.canvas.create_text(px*GRID_SIZE+20, py*GRID_SIZE+20, text=p_char, fill="cyan", font=("Arial", 20))

        # Update Stats
        s = self.player["stats"]
        self.stat_label.config(text=f"HP: {s['hp']}/{s['max_hp']}\nXP: {s['xp']}\nDMG: {s['dmg']} | DEF: {s['def']}\nFloor: {self.player['floor']} | Turn: {self.player['turn_count']}")

    def handle_keypress(self, event):
        # Konami Check
        key = event.keysym
        if self.konami_index < len(self.konami_code):
            target = self.konami_code[self.konami_index]
            if (target.lower() == key.lower()) or (target == "Up" and key == "Up"):
                self.konami_index += 1
            else:
                self.konami_index = 0
            
            if self.konami_index == len(self.konami_code):
                self.log("CHEATS ACTIVATED")
                self.cheat_entry.pack(fill="x", padx=10)
                self.cheats_enabled = True

        dx, dy = 0, 0
        if key in ["Up", "w"]: dy = -1
        elif key in ["Down", "s"]: dy = 1
        elif key in ["Left", "a"]: dx = -1
        elif key in ["Right", "d"]: dx = 1
        elif key == "space":
            self.interact()
            return

        if dx != 0 or dy != 0:
            self.move_player(dx, dy)

    def move_player(self, dx, dy):
        new_x = self.player["pos"][0] + dx
        new_y = self.player["pos"][1] + dy
        
        # Check Collision / Attack
        for e in self.enemies:
            if e.x == new_x and e.y == new_y:
                self.attack_enemy(e)
                self.end_turn()
                return

        # Check Walls
        for tile in self.level_data:
            if tile['pos'] == (new_x, new_y) and tile['type'] == 'wall':
                return

        self.player["pos"] = [new_x, new_y]
        self.end_turn()

    def attack_enemy(self, enemy):
        dmg = self.player["stats"]["dmg"]
        enemy.hp -= dmg
        self.log(f"You hit {enemy.name} for {dmg}!")
        if enemy.hp <= 0:
            self.log(f"{enemy.name} died! +10 XP")
            self.player["stats"]["xp"] += 10
            self.enemies.remove(enemy)

    def interact(self):
        pos = tuple(self.player["pos"])
        if pos in self.objects:
            obj = self.objects[pos]
            if obj == "stair":
                self.player["floor"] += 1
                self.log(f"Descended to Floor {self.player['floor']}")
                self.generate_level()
            elif obj == "chest":
                loot = random.choice(self.loot_table.get(self.player["floor"], ["Rusty Spoon"]))
                self.log(f"Found {loot}!")
                del self.objects[pos]
                self.draw_game()

    def end_turn(self):
        self.player["turn_count"] += 1
        # Enemy Turns
        for e in self.enemies:
            e.act(self.player, self.level_data, self.enemies)
            if e.hp <= 0: continue
            # If adjacent after move, attack
            dist = math.dist(self.player["pos"], [e.x, e.y])
            if dist < 1.5:
                dmg = max(1, 5 - self.player["stats"]["def"] // 2)
                self.player["stats"]["hp"] -= dmg
                self.log(f"{e.name} dealt {dmg} damage!")

        if self.player["stats"]["hp"] <= 0:
            self.game_over()
        
        self.draw_game()

    def game_over(self):
        self.game_running = False
        death_win = tk.Toplevel(self.game_window)
        death_win.geometry("300x200")
        tk.Label(death_win, text="YOU DIED", font=("Courier", 30), fg="red").pack(pady=20)
        tk.Button(death_win, text="QUIT", command=self.root.destroy).pack()

    def game_loop(self):
        # Placeholder for real-time logic if needed (e.g. animations)
        while self.game_running:
            time.sleep(0.1)

    # --- Upgrades & Cheats ---
    def toggle_upgrades(self):
        if self.upgrade_window_open:
            self.upgrade_frame.destroy()
            self.upgrade_window_open = False
        else:
            self.upgrade_frame = tk.Frame(self.left_panel, bg="#333")
            self.upgrade_frame.place(x=0, y=150, width=350, height=300)
            tk.Label(self.upgrade_frame, text="UPGRADES (Cost: 20 XP)", bg="#333", fg="white").pack()
            
            for stat in ["dmg", "max_hp", "def"]:
                tk.Button(self.upgrade_frame, text=f"+ {stat.upper()}", 
                          command=lambda s=stat: self.apply_upgrade(s)).pack(pady=5)
            self.upgrade_window_open = True

    def apply_upgrade(self, stat):
        if self.player["stats"]["xp"] >= 20:
            self.player["stats"]["xp"] -= 20
            self.player["stats"][stat] += 5
            if stat == "max_hp": self.player["stats"]["hp"] = self.player["stats"]["max_hp"]
            self.log(f"Upgraded {stat}!")
            self.draw_game()

    def process_cheat(self, event):
        cmd = self.cheat_entry.get()
        if cmd == "+hp": self.player["stats"]["hp"] = 999
        elif cmd == "+def": self.player["stats"]["def"] += 50
        elif cmd == "+dmg": self.player["stats"]["dmg"] += 50
        self.cheat_entry.delete(0, 'end')
        self.draw_game()

class Enemy:
    def __init__(self, name, x, y):
        self.name = name
        self.x = x
        self.y = y
        self.hp = 30

    def act(self, player, walls, enemies):
        px, py = player["pos"]
        dist = math.dist([self.x, self.y], [px, py])
        
        if dist < 1.5: # Already adjacent
            return 
        
        # Simple AI: Move towards player if healthy, away if low
        dx = 1 if px > self.x else -1 if px < self.x else 0
        dy = 1 if py > self.y else -1 if py < self.y else 0
        
        if self.hp < 10: # Flee
            dx *= -1
            dy *= -1

        new_x, new_y = self.x + dx, self.y + dy
        
        # Collision check
        is_blocked = False
        if [new_x, new_y] == player["pos"]: is_blocked = True
        for w in walls:
            if w['pos'] == (new_x, new_y) and w['type'] == 'wall': is_blocked = True
        
        if not is_blocked:
            self.x, self.y = new_x, new_y

if __name__ == "__main__":
    game = DungeonGame()
    game.root.mainloop()