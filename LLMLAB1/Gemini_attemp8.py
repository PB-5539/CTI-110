import tkinter as tk
from tkinter import messagebox, ttk
import random
import math
import time
import threading

# --- CONFIGURATION & CONSTANTS ---
TILE_SIZE = 40
GRID_WIDTH = 15
GRID_HEIGHT = 15
COLORS = {
    "default": {"bg": "#4B0082", "wall": "#2F4F4F", "floor": "#1A1A1A", "text": "white"},
    "green": {"bg": "#006400", "wall": "#2E8B57", "floor": "#002200", "text": "white"},
    "red": {"bg": "#8B0000", "wall": "#A52A2A", "floor": "#220000", "text": "white"}
}

RAW_MAPS = [
    [
        "111111111111111",
        "1P0000000000001",
        "100C00111000S01",
        "100000111000001",
        "111000000000111",
        "100011111110001",
        "10S000000000001",
        "100011111110001",
        "111000000000111",
        "100000111000001",
        "10000011100C001",
        "100G00000000001",
        "1000001X100S001",
        "100C00111000001",
        "111111111111111"
    ]
]

ITEM_STATS = {
    "Rusty Sword": {"type": "Weapon", "dmg": 5, "def": 0, "block": 0},
    "Iron Shield": {"type": "Shield", "dmg": 0, "def": 2, "block": 0.2},
    "Leather Armor": {"type": "Armor", "dmg": 0, "def": 5, "block": 0},
    "Magic Ring": {"type": "Accessory", "dmg": 2, "def": 1, "block": 0.05}
}

LOOT_TABLES = {
    1: ["Rusty Sword", "Iron Shield"],
    2: ["Iron Shield", "Leather Armor"],
    3: ["Magic Ring", "Leather Armor"]
}

class Entity:
    def __init__(self, x, y, hp, name, char, color):
        self.x = x
        self.y = y
        self.max_hp = hp
        self.hp = hp
        self.name = name
        self.char = char
        self.color = color

class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dungeon Crawler")
        self.current_theme = "default"
        self.use_emojis = tk.BooleanVar(value=True)
        self.konami_index = 0
        self.konami_code = ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]
        self.cheat_mode = False
        
        self.main_menu()

    def main_menu(self):
        self.menu_frame = tk.Frame(self.root, bg=COLORS[self.current_theme]["bg"], padx=50, pady=50)
        self.menu_frame.pack(fill="both", expand=True)

        tk.Label(self.menu_frame, text="PY-DUNGEON", font=("Courier", 30, "bold"), 
                 bg=COLORS[self.current_theme]["bg"], fg="white").pack(pady=20)

        btns = [("Play", self.start_game), ("Settings", self.open_settings), 
                ("Level Creator", self.open_editor), ("Quit", self.root.destroy)]
        
        for text, cmd in btns:
            tk.Button(self.menu_frame, text=text, command=cmd, width=20, height=2,
                      bg="#333", fg="white", font=("Arial", 12)).pack(pady=5)

    def open_settings(self):
        if hasattr(self, 'sett_win') and self.sett_win.winfo_exists():
            self.sett_win.lift()
            return
        
        self.sett_win = tk.Toplevel(self.root)
        self.sett_win.title("Settings")
        self.sett_win.geometry("300x300")
        
        tk.Label(self.sett_win, text="Theme Selection").pack(pady=5)
        for theme in COLORS.keys():
            tk.Button(self.sett_win, text=theme.capitalize(), 
                      command=lambda t=theme: self.set_theme(t)).pack(fill="x")
        
        tk.Checkbutton(self.sett_win, text="Use Emojis", variable=self.use_emojis).pack(pady=10)

    def set_theme(self, theme):
        self.current_theme = theme
        self.menu_frame.config(bg=COLORS[theme]["bg"])

    # --- GAME LOGIC ---
    def start_game(self):
        self.game_win = tk.Toplevel(self.root)
        self.game_win.protocol("WM_DELETE_WINDOW", self.exit_game)
        self.root.withdraw()

        # Player Data
        self.player = {
            "stats": {"hp": 100, "max_hp": 100, "dmg": 10, "def": 0, "block": 0, "speed": 1, "xp": 0},
            "pos": [1, 1],
            "inventory": {}, # {item_name: (x, y)}
            "equipped": {},  # {type: item_name}
            "hotbar": {}
        }
        
        self.floor = 1
        self.turns = 0
        self.running = True
        self.entities = []
        self.map_data = []

        self.setup_game_ui()
        self.load_level()
        self.game_win.bind("<Key>", self.handle_input)
        
        # Game Loop Thread
        self.loop_thread = threading.Thread(target=self.game_loop, daemon=True)
        self.loop_thread.start()

    def setup_game_ui(self):
        self.ui_left = tk.Frame(self.game_win, width=300, bg="#222")
        self.ui_left.pack(side="left", fill="y")
        
        self.stats_label = tk.Label(self.ui_left, text="", fg="white", bg="#222", justify="left", font=("Courier", 10))
        self.stats_label.pack(pady=10, padx=5)

        self.inv_canvas = tk.Canvas(self.ui_left, width=280, height=200, bg="#333", highlightthickness=0)
        self.inv_canvas.pack(pady=10)
        self.inv_canvas.bind("<Button-1>", self.on_inventory_click)

        self.upgrade_btn = tk.Button(self.ui_left, text="Upgrades", command=self.toggle_upgrades)
        self.upgrade_btn.pack(pady=5)

        self.right_frame = tk.Frame(self.game_win)
        self.right_frame.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(self.right_frame, width=GRID_WIDTH*TILE_SIZE, height=GRID_HEIGHT*TILE_SIZE, bg="black")
        self.canvas.pack()

        self.terminal = tk.Entry(self.right_frame, bg="black", fg="lime", font=("Courier", 10))
        self.terminal.pack(fill="x")
        self.terminal.bind("<Return>", self.process_command)
        self.terminal.config(state="disabled")

        self.log = tk.Text(self.right_frame, height=6, bg="#111", fg="white", state="disabled")
        self.log.pack(fill="x")

    def log_msg(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", f"> {msg}\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def load_level(self):
        raw = random.choice(RAW_MAPS)
        self.map_data = []
        self.entities = []
        for r, line in enumerate(raw):
            row = []
            for c, char in enumerate(line):
                row.append(char)
                if char == 'P': self.player["pos"] = [c, r]
                elif char == 'S': self.entities.append(Entity(c, r, 30, "Skeleton", "S", "white"))
                elif char == 'G': self.entities.append(Entity(c, r, 20, "Goblin", "G", "green"))
            self.map_data.append(row)
        self.render()

    def render(self):
        self.canvas.delete("all")
        theme = COLORS[self.current_theme]
        
        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                tile = self.map_data[r][c]
                x1, y1 = c * TILE_SIZE, r * TILE_SIZE
                color = theme["wall"] if tile == "1" else theme["floor"]
                self.canvas.create_rectangle(x1, y1, x1+TILE_SIZE, y1+TILE_SIZE, fill=color, outline="#444")
                
                if tile == "X":
                    self.draw_sprite(c, r, "▼", "blue", True)
                elif tile == "C":
                    self.draw_sprite(c, r, "C", "gold", True)

        # Draw Entities
        for en in self.entities:
            self.draw_sprite(en.x, en.y, en.char, en.color)
            # HP Bar
            bar_w = (en.hp / en.max_hp) * TILE_SIZE
            self.canvas.create_rectangle(en.x*TILE_SIZE, en.y*TILE_SIZE-5, 
                                         en.x*TILE_SIZE+bar_w, en.y*TILE_SIZE-2, fill="red")

        # Draw Player
        px, py = self.player["pos"]
        self.draw_sprite(px, py, "@", "cyan")
        
        self.update_stats_ui()
        self.draw_inventory()

    def draw_sprite(self, x, y, char, color, square=False):
        x1, y1 = x * TILE_SIZE, y * TILE_SIZE
        if self.use_emojis.get():
            emo = {"@": "🧙", "S": "💀", "G": "👺", "C": "📦", "▼": "🏁"}.get(char, char)
            self.canvas.create_text(x1+TILE_SIZE/2, y1+TILE_SIZE/2, text=emo, font=("Arial", 20))
        else:
            if square:
                self.canvas.create_rectangle(x1+5, y1+5, x1+TILE_SIZE-5, y1+TILE_SIZE-5, fill=color)
            else:
                self.canvas.create_oval(x1+5, y1+5, x1+TILE_SIZE-5, y1+TILE_SIZE-5, fill=color)
            self.canvas.create_text(x1+TILE_SIZE/2, y1+TILE_SIZE/2, text=char, fill="black" if color in ["white", "cyan", "gold"] else "white")

    def update_stats_ui(self):
        p = self.player["stats"]
        txt = f"FLOOR: {self.floor} | TURN: {self.turns}\nHP: {p['hp']}/{p['max_hp']}\nXP: {p['xp']}\nDMG: {p['dmg']} | DEF: {p['def']}"
        self.stats_label.config(text=txt)

    def draw_inventory(self):
        self.inv_canvas.delete("all")
        # 9x3 Grid
        for r in range(3):
            for c in range(9):
                x, y = c*30 + 5, r*30 + 5
                self.inv_canvas.create_rectangle(x, y, x+25, y+25, outline="gray", fill="#444")
        # 9x1 Hotbar
        for c in range(9):
            x, y = c*30 + 5, 120
            self.inv_canvas.create_rectangle(x, y, x+25, y+25, outline="white", fill="#444")

    # --- INPUT & AI ---
    def handle_input(self, event):
        if not self.running: return
        
        # Konami Check
        if event.keysym == self.konami_code[self.konami_index]:
            self.konami_index += 1
            if self.konami_index == len(self.konami_code):
                self.cheat_mode = True
                self.terminal.config(state="normal")
                self.log_msg("Cheats Enabled.")
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
            self.move_player(dx, dy)

    def move_player(self, dx, dy):
        new_x = self.player["pos"][0] + dx
        new_y = self.player["pos"][1] + dy
        
        # Collision
        if self.map_data[new_y][new_x] == "1": return
        
        # Combat Check
        target = next((en for en in self.entities if en.x == new_x and en.y == new_y), None)
        if target:
            dmg = max(1, self.player["stats"]["dmg"])
            target.hp -= dmg
            self.log_msg(f"You hit {target.name} for {dmg}!")
            if target.hp <= 0:
                self.entities.remove(target)
                self.player["stats"]["xp"] += 10
            self.end_turn()
        else:
            self.player["pos"] = [new_x, new_y]
            self.end_turn()

    def interact(self):
        px, py = self.player["pos"]
        tile = self.map_data[py][px]
        if tile == "X":
            self.floor += 1
            self.load_level()
            self.log_msg(f"Descended to Floor {self.floor}")
        elif tile == "C":
            item = random.choice(LOOT_TABLES.get(min(self.floor, 3)))
            self.log_msg(f"Found {item}!")
            self.map_data[py][px] = "0"
            self.render()

    def end_turn(self):
        self.turns += 1
        # Enemy AI
        px, py = self.player["pos"]
        for en in self.entities:
            dist = math.sqrt((en.x - px)**2 + (en.y - py)**2)
            if dist < 5:
                # Basic move towards player
                mdx = 1 if px > en.x else -1 if px < en.x else 0
                mdy = 1 if py > en.y else -1 if py < en.y else 0
                
                # Prioritize one axis (no diagonal)
                if mdx != 0 and abs(px-en.x) >= abs(py-en.y):
                    nx, ny = en.x + mdx, en.y
                else:
                    nx, ny = en.x, en.y + mdy
                
                if dist <= 1.1: # Attack
                    dmg = max(0, 5 - self.player["stats"]["def"])
                    self.player["stats"]["hp"] -= dmg
                    self.log_msg(f"{en.name} bit you for {dmg}!")
                elif self.map_data[ny][nx] == "0" and not (nx == px and ny == py):
                    en.x, en.y = nx, ny

        if self.player["stats"]["hp"] <= 0:
            self.game_over()
        self.render()

    def game_loop(self):
        while self.running:
            time.sleep(0.1)

    def game_over(self):
        self.running = False
        messagebox.showinfo("Game Over", f"You died on floor {self.floor}")
        self.exit_game()

    def exit_game(self):
        self.running = False
        self.game_win.destroy()
        self.root.deiconify()

    # --- LEVEL EDITOR ---
    def open_editor(self):
        self.ed_win = tk.Toplevel(self.root)
        self.ed_win.title("Level Creator")
        self.brush = "1"
        
        canvas = tk.Canvas(self.ed_win, width=GRID_WIDTH*20, height=GRID_HEIGHT*20, bg="black")
        canvas.pack(side="left")
        
        cells = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        
        def paint(event):
            c, r = event.x // 20, event.y // 20
            if 0 <= c < GRID_WIDTH and 0 <= r < GRID_HEIGHT:
                char = self.brush
                color = {"1": "gray", "0": "black", "X": "blue", "C": "gold", "P": "white", "S": "red", "G": "green"}[char]
                canvas.itemconfig(cells[r][c], fill=color)
                temp_map[r][c] = char

        temp_map = [["0" for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        for r in range(GRID_HEIGHT):
            for c in range(GRID_WIDTH):
                cells[r][c] = canvas.create_rectangle(c*20, r*20, c*20+20, r*20+20, outline="#222")
        
        canvas.bind("<B1-Motion>", paint)
        canvas.bind("<Button-1>", paint)

        panel = tk.Frame(self.ed_win)
        panel.pack(side="right", fill="y")
        
        for k, v in [("Wall", "1"), ("Floor", "0"), ("Stairs", "X"), ("Chest", "C"), ("Player", "P"), ("Skeleton", "S")]:
            tk.Button(panel, text=k, command=lambda val=v: setattr(self, 'brush', val)).pack(fill="x")
            
        tk.Button(panel, text="SAVE", bg="lime", command=lambda: self.save_map(temp_map)).pack(pady=20)

    def save_map(self, m):
        new_raw = ["".join(row) for row in m]
        RAW_MAPS.append(new_raw)
        self.ed_win.destroy()
        messagebox.showinfo("Success", "Map added to rotations!")

    # --- MISC SYSTEMS ---
    def process_command(self, event):
        cmd = self.terminal.get().strip()
        if cmd == "+hp": self.player["stats"]["max_hp"] += 50; self.player["stats"]["hp"] += 50
        elif cmd == "+dmg": self.player["stats"]["dmg"] += 10
        self.terminal.delete(0, "end")
        self.render()

    def toggle_upgrades(self):
        messagebox.showinfo("Upgrades", "XP: " + str(self.player["stats"]["xp"]) + "\nClick tree nodes to upgrade (WIP)")

    def on_inventory_click(self, event):
        # Implementation for clicking grid coords to equip
        pass

if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()