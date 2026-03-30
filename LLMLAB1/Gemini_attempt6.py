import math
import random
import time
import tkinter as tk
from tkinter import messagebox
import threading

class RogueGame:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dungeon Crawler")
        self.root.geometry("1000x700")
        
        # --- Settings & State ---
        self.theme = {"bg": "#2E1A47", "wall": "#3B3B4D", "floor": "#1A1A1A"} # Default Purple
        self.use_emojis = tk.BooleanVar(value=True)
        self.cheats_enabled = False
        self.konami_progress = []
        self.konami_code = ["Up", "Up", "Down", "Down", "Left", "Right", "Left", "Right", "b", "a"]
        
        self.game_running = False
        self.current_floor = 1
        self.turn_count = 0
        self.active_subwindows = {}

        # --- Player Data ---
        self.player = {
            "stats": {"hp": 100, "max_hp": 100, "dmg": 10, "def": 5, "dodge": 5, "speed": 1, "xp": 0},
            "pos": [1, 1],
            "inventory": {}, # {item_name: (x, y)}
            "hotbar": {},
            "equipped": None
        }
        
        self.item_stats = {
            "Rusty Sword": {"dmg": 5, "def": 0, "block": 2},
            "Iron Shield": {"dmg": 0, "def": 8, "block": 15},
            "Leather Armor": {"dmg": 0, "def": 10, "block": 5}
        }
        
        self.loot_table = {
            1: ["Rusty Sword", "Leather Armor"],
            2: ["Iron Shield", "Steel Blade"],
            3: ["Greatsword", "Platemail"]
        }

        self.enemies = []
        self.map_data = [] # List of dicts { (x,y): type }
        
        self.main_menu()

    # --- UI Windows ---
    def main_menu(self):
        self.menu_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.menu_frame.pack(fill="both", expand=True)
        
        tk.Label(self.menu_frame, text="VOID CRAWLER", font=("Courier", 40, "bold"), 
                 fg="white", bg=self.theme["bg"]).pack(pady=50)
        
        btns = [("PLAY", self.start_game), ("SETTINGS", self.open_settings), ("QUIT", self.root.destroy)]
        for txt, cmd in btns:
            tk.Button(self.menu_frame, text=txt, font=("Courier", 18), width=15, 
                      command=cmd, bg="#4B0082", fg="white").pack(pady=10)

    def open_settings(self):
        if "settings" in self.active_subwindows:
            self.active_subwindows["settings"].lift()
            return
        
        win = tk.Toplevel(self.root)
        win.title("Settings")
        self.active_subwindows["settings"] = win
        win.protocol("WM_DELETE_WINDOW", lambda: self.active_subwindows.pop("settings") or win.destroy())
        
        tk.Label(win, text="Select Theme:").pack()
        tk.Button(win, text="Purple (Default)", command=lambda: self.set_theme("purple")).pack()
        tk.Button(win, text="Toxic Green", command=lambda: self.set_theme("green")).pack()
        tk.Button(win, text="Blood Red", command=lambda: self.set_theme("red")).pack()
        
        tk.Checkbutton(win, text="Use Emojis instead of Text", variable=self.use_emojis).pack(pady=10)

    def set_theme(self, color):
        themes = {
            "purple": {"bg": "#2E1A47", "wall": "#3B3B4D", "floor": "#1A1A1A"},
            "green": {"bg": "#0A2410", "wall": "#1B3B1B", "floor": "#050F05"},
            "red": {"bg": "#240A0A", "wall": "#3B1B1B", "floor": "#0F0505"}
        }
        self.theme = themes[color]
        messagebox.showinfo("Theme", "Theme will apply to the next level/game.")

    # --- Game Engine ---
    def start_game(self):
        self.menu_frame.pack_forget()
        self.game_running = True
        
        # Main Layout
        self.game_container = tk.Frame(self.root, bg="black")
        self.game_container.pack(fill="both", expand=True)
        
        # Left Panel (Stats & Inventory)
        self.side_panel = tk.Frame(self.game_container, width=300, bg="#222")
        self.side_panel.pack(side="left", fill="y")
        
        self.stat_label = tk.Label(self.side_panel, text="", fg="white", bg="#222", justify="left", font=("Courier", 10))
        self.stat_label.pack(pady=10, padx=10)
        
        self.inv_canvas = tk.Canvas(self.side_panel, width=280, height=400, bg="#333")
        self.inv_canvas.pack(pady=5)
        
        tk.Button(self.side_panel, text="UPGRADES", command=self.toggle_upgrades).pack(pady=10)
        
        # Right Panel (Canvas & Terminal)
        self.right_panel = tk.Frame(self.game_container, bg="black")
        self.right_panel.pack(side="right", fill="both", expand=True)
        
        self.game_canvas = tk.Canvas(self.right_panel, bg=self.theme["floor"], width=600, height=450)
        self.game_canvas.pack(pady=5)
        
        self.terminal = tk.Text(self.right_panel, height=8, bg="black", fg="#00FF00", state="disabled")
        self.terminal.pack(fill="x", padx=10, pady=5)
        
        self.cmd_entry = tk.Entry(self.right_panel, bg="#111", fg="white", insertbackground="white")
        self.cmd_entry.bind("<Return>", self.handle_command)
        
        # Bind Controls
        self.root.bind("<Key>", self.handle_input)
        
        self.generate_level()
        self.draw_inventory()
        self.update_stats()
        
        # Start Game Logic Thread
        threading.Thread(target=self.game_loop, daemon=True).start()

    def generate_level(self):
        self.map_data = {}
        self.enemies = []
        # Simple procedural: 20x15 grid
        for x in range(20):
            for y in range(15):
                if x == 0 or x == 19 or y == 0 or y == 14:
                    self.map_data[(x,y)] = "wall"
                else:
                    self.map_data[(x,y)] = "floor"
        
        # Add staircase
        self.map_data[(18, 13)] = "stairs"
        # Add a chest
        self.map_data[(random.randint(2,17), random.randint(2,12))] = "chest"
        
        # Spawn Enemies
        for _ in range(3 + self.current_floor):
            ex, ey = random.randint(5, 17), random.randint(5, 12)
            if (ex, ey) not in self.map_data or self.map_data[(ex,ey)] == "floor":
                self.enemies.append(Enemy("Skeleton", [ex, ey], 30 + (self.current_floor*5)))

        self.render_all()

    def render_all(self):
        self.game_canvas.delete("all")
        tw, th = 30, 30
        for (x, y), tile_type in self.map_data.items():
            color = self.theme["wall"] if tile_type == "wall" else self.theme["floor"]
            self.game_canvas.create_rectangle(x*tw, y*th, (x+1)*tw, (y+1)*th, fill=color, outline="#444")
            
            if tile_type == "stairs":
                self.draw_sprite(x, y, "▼", "yellow", "square")
            elif tile_type == "chest":
                self.draw_sprite(x, y, "C", "brown", "square")

        # Draw Player
        px, py = self.player["pos"]
        self.draw_sprite(px, py, "@", "white", "circle")
        
        # Draw Enemies
        for en in self.enemies:
            self.draw_sprite(en.pos[0], en.pos[1], "S", "red", "circle")
            # Enemy HP Bar
            pct = en.hp / en.max_hp
            self.game_canvas.create_rectangle(en.pos[0]*tw, en.pos[1]*th-5, (en.pos[0]+1)*tw, en.pos[1]*th-2, fill="red")
            self.game_canvas.create_rectangle(en.pos[0]*tw, en.pos[1]*th-5, en.pos[0]*tw + (tw*pct), en.pos[1]*th-2, fill="green")

    def draw_sprite(self, x, y, char, color, shape):
        tw, th = 30, 30
        x1, y1, x2, y2 = x*tw, y*th, (x+1)*tw, (y+1)*th
        if shape == "circle":
            self.game_canvas.create_oval(x1+2, y1+2, x2-2, y2-2, fill=color)
        else:
            self.game_canvas.create_rectangle(x1+2, y1+2, x2-2, y2-2, fill=color)
        
        text_color = "black" if color in ["white", "yellow", "cyan"] else "white"
        icon = char
        if self.use_emojis.get():
            mapping = {"@": "🧙", "S": "💀", "C": "📦", "▼": "🪜"}
            icon = mapping.get(char, char)
            
        self.game_canvas.create_text(x*tw + 15, y*th + 15, text=icon, fill=text_color, font=("Arial", 12, "bold"))

    # --- Interaction Logic ---
    def handle_input(self, event):
        if not self.game_running: return
        
        # Konami check
        self.konami_progress.append(event.keysym)
        if self.konami_progress == self.konami_code:
            self.log("Cheats Enabled!")
            self.cmd_entry.pack(fill="x", padx=10)
            self.cheats_enabled = True
        elif len(self.konami_progress) >= len(self.konami_code):
            self.konami_progress.pop(0)

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
        if self.map_data.get((new_x, new_y)) == "wall":
            return
            
        # Attack Check
        target = None
        for en in self.enemies:
            if en.pos == [new_x, new_y]:
                target = en
                break
        
        if target:
            dmg = self.player["stats"]["dmg"]
            target.hp -= dmg
            self.log(f"You hit {target.name} for {dmg} damage!")
            if target.hp <= 0:
                self.enemies.remove(target)
                self.player["stats"]["xp"] += 20
                self.log(f"{target.name} died! +20 XP")
            self.end_turn()
        else:
            self.player["pos"] = [new_x, new_y]
            self.end_turn()

    def interact(self):
        pos = tuple(self.player["pos"])
        tile = self.map_data.get(pos)
        if tile == "stairs":
            self.current_floor += 1
            self.log(f"Descending to floor {self.current_floor}...")
            self.generate_level()
        elif tile == "chest":
            item = random.choice(self.loot_table.get(min(self.current_floor, 3), ["Rusty Sword"]))
            self.add_to_inventory(item)
            self.map_data[pos] = "floor"
            self.log(f"Found a {item}!")
            self.render_all()

    def end_turn(self):
        self.turn_count += 1
        # Enemy AI
        for en in self.enemies:
            en.act(self.player, self.map_data, self.enemies)
        
        if self.player["stats"]["hp"] <= 0:
            self.game_over()
        
        self.render_all()
        self.update_stats()

    def log(self, msg):
        self.terminal.config(state="normal")
        self.terminal.insert("end", f"> {msg}\n")
        self.terminal.see("end")
        self.terminal.config(state="disabled")

    # --- UI Components ---
    def update_stats(self):
        s = self.player["stats"]
        txt = (f"FLOOR: {self.current_floor} | TURN: {self.turn_count}\n"
               f"HP: {s['hp']}/{s['max_hp']}\nXP: {s['xp']}\n"
               f"DMG: {s['dmg']} | DEF: {s['def']}\n"
               f"EQUIPPED: {self.player['equipped'] or 'None'}")
        self.stat_label.config(text=txt)

    def add_to_inventory(self, item_name):
        # Find first empty slot in 9x3 grid
        for y in range(3):
            for x in range(9):
                if (x, y) not in self.player["inventory"].values():
                    self.player["inventory"][item_name + f"_{random.getrandbits(16)}"] = (x, y)
                    self.draw_inventory()
                    return

    def draw_inventory(self):
        self.inv_canvas.delete("all")
        # Draw Grids
        for i in range(10): # Vert lines
            self.inv_canvas.create_line(i*30 + 5, 5, i*30 + 5, 95, fill="#555")
        for i in range(4): # Horiz lines
            self.inv_canvas.create_line(5, i*30 + 5, 275, i*30 + 5, fill="#555")
        
        # Populate items
        for item_id, (ix, iy) in self.player["inventory"].items():
            clean_name = item_id.split("_")[0]
            x, y = ix*30 + 20, iy*30 + 20
            item_tag = self.inv_canvas.create_text(x, y, text="🎁", fill="cyan", font=("Arial", 14))
            self.inv_canvas.tag_bind(item_tag, "<Button-1>", lambda e, name=item_id: self.show_tooltip(name))

    def show_tooltip(self, item_id):
        clean_name = item_id.split("_")[0]
        stats = self.item_stats.get(clean_name, {})
        msg = f"{clean_name}\n" + "\n".join([f"{k}: {v}" for k, v in stats.items()])
        if messagebox.askyesno(clean_name, f"{msg}\n\nEquip this item?"):
            self.player["equipped"] = clean_name
            self.update_stats()

    def toggle_upgrades(self):
        # Simple upgrade overlay simulation
        win = tk.Toplevel(self.root)
        win.title("Upgrades")
        tk.Label(win, text=f"Available XP: {self.player['stats']['xp']}").pack()
        
        def upgrade(stat):
            cost = 50
            if self.player["stats"]["xp"] >= cost:
                self.player["stats"]["xp"] -= cost
                self.player["stats"][stat] += 5
                self.update_stats()
                win.destroy()
            else: messagebox.showwarning("XP", "Not enough XP!")

        tk.Button(win, text="Upgrade HP (50 XP)", command=lambda: upgrade("max_hp")).pack()
        tk.Button(win, text="Upgrade Damage (50 XP)", command=lambda: upgrade("dmg")).pack()

    def handle_command(self, event):
        cmd = self.cmd_entry.get()
        if cmd == "+hp": self.player["stats"]["max_hp"] += 100; self.player["stats"]["hp"] = self.player["stats"]["max_hp"]
        elif cmd == "+dmg": self.player["stats"]["dmg"] += 50
        self.cmd_entry.delete(0, tk.END)
        self.update_stats()

    def game_loop(self):
        # In a turn-based game, this handles background animations or timing if needed
        while self.game_running:
            time.sleep(0.1)

    def game_over(self):
        self.game_running = False
        res = messagebox.askquestion("GAME OVER", f"You died on Floor {self.current_floor}. Restart?")
        if res == 'yes':
            self.root.destroy()
            RogueGame()
        else:
            self.root.destroy()

class Enemy:
    def __init__(self, name, pos, hp):
        self.name = name
        self.pos = pos
        self.hp = hp
        self.max_hp = hp

    def act(self, player, map_data, all_enemies):
        px, py = player["pos"]
        ex, ey = self.pos
        dist = math.sqrt((px-ex)**2 + (py-ey)**2)
        
        if dist < 1.5: # Adjacent
            dmg = max(2, 10 - player["stats"]["def"] // 2)
            player["stats"]["hp"] -= dmg
        elif dist < 6: # Chase
            dx = 1 if px > ex else -1 if px < ex else 0
            dy = 1 if py > ey else -1 if py < ey else 0
            
            new_pos = [ex + dx, ey + dy]
            # Simple collision check
            if map_data.get(tuple(new_pos)) != "wall":
                # Ensure not walking onto player or other enemy
                if new_pos != player["pos"] and not any(e.pos == new_pos for e in all_enemies if e != self):
                    self.pos = new_pos

if __name__ == "__main__":
    game = RogueGame()
    game.root.mainloop()