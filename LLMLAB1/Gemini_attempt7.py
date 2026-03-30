import math
import random
import time
import tkinter as tk
from tkinter import messagebox
import threading

# --- GLOBAL SETTINGS & DATA ---

THEMES = {
    "Default": {"bg": "#2b213a", "wall": "#4a4a5a", "floor": "#303040", "text": "white", "ui": "#1e1728"},
    "Green": {"bg": "#1a3320", "wall": "#2a4a30", "floor": "#203a25", "text": "white", "ui": "#122416"},
    "Red": {"bg": "#331a1a", "wall": "#4a2a2a", "floor": "#3a2020", "text": "white", "ui": "#241212"}
}

# Base items list
BASE_ITEMS = {
    "Wooden Sword": {"type": "weapon", "damage": 5},
    "Iron Sword": {"type": "weapon", "damage": 10},
    "Steel Sword": {"type": "weapon", "damage": 18},
    "Leather Armor": {"type": "armor", "defense": 2},
    "Iron Armor": {"type": "armor", "defense": 5},
    "Steel Armor": {"type": "armor", "defense": 9},
    "Wooden Shield": {"type": "shield", "block": 0.1, "defense": 1},
    "Iron Shield": {"type": "shield", "block": 0.2, "defense": 2},
    "Steel Shield": {"type": "shield", "block": 0.35, "defense": 4},
    "Small Potion": {"type": "consumable", "hp": 25},
    "Health Potion": {"type": "consumable", "hp": 50},
    "Large Potion": {"type": "consumable", "hp": 100}
}

LOOT_TABLES = {
    1: ["Wooden Sword", "Leather Armor", "Small Potion", "Wooden Shield"],
    2: ["Iron Sword", "Iron Armor", "Health Potion", "Iron Shield"],
    3: ["Steel Sword", "Steel Armor", "Large Potion", "Steel Shield"]
}

# Generate Map Dictionary Pool
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
    ],
    [
        "111111111111111",
        "1P00000000000G1",
        "111110001111101",
        "10C010S0100C101",
        "100010001000101",
        "100011011000101",
        "100000000000001",
        "111111011111111",
        "100000000000001",
        "100S000C000G001",
        "100000000000001",
        "101110001111111",
        "101X00001C00001",
        "101110001111101",
        "111111111111111"
    ]
]

def build_map_dicts():
    pool = []
    for raw in RAW_MAPS:
        m_dict = []
        for y, row in enumerate(raw):
            for x, char in enumerate(row):
                t = "wall" if char == "1" else "floor" if char == "0" else "player" if char == "P" else "skeleton" if char == "S" else "goblin" if char == "G" else "chest" if char == "C" else "stairs"
                m_dict.append({"x": x, "y": y, "type": t})
        pool.append(m_dict)
    return pool

MAP_POOL = build_map_dicts()

def get_contrast_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return "#000000" if luminance > 128 else "#ffffff"

# --- GAME LOGIC CLASSES ---

class Monster:
    def __init__(self, x, y, m_type, floor):
        self.x = x
        self.y = y
        self.m_type = m_type
        
        # Scaling stats based on floor
        scale = 1 + (floor * 0.2)
        if m_type == "goblin":
            self.hp = int(12 * scale); self.max_hp = int(12 * scale); self.damage = int(3 * scale)
        else: # skeleton
            self.hp = int(20 * scale); self.max_hp = int(20 * scale); self.damage = int(5 * scale)

    def act(self, player, engine):
        dist = abs(self.x - player["position"]["x"]) + abs(self.y - player["position"]["y"])
        if dist == 1:
            self.attack(player, engine)
        elif self.hp < self.max_hp * 0.3:
            self.run_away(player["position"]["x"], player["position"]["y"], engine)
        elif dist <= 6:
            self.move_towards(player["position"]["x"], player["position"]["y"], engine)

    def attack(self, player, engine):
        # Calculate defense and block
        equip_def = 0
        block_chance = 0.0
        
        if player["equipment"]["armor"]:
            equip_def += engine.item_stats[player["equipment"]["armor"]].get("defense", 0)
        if player["equipment"]["shield"]:
            shield_id = player["equipment"]["shield"]
            equip_def += engine.item_stats[shield_id].get("defense", 0)
            block_chance = engine.item_stats[shield_id].get("block", 0.0)

        total_def = player["stats"]["base_defense"] + equip_def

        # Block Check
        if random.random() < block_chance:
            engine.log(f"You blocked the {self.m_type}'s attack!")
            return

        # Dodge Check
        if random.randint(0, 100) < player["stats"]["dodge"]:
            engine.log(f"{self.m_type.capitalize()} missed!")
            return

        final_dmg = max(1, self.damage - total_def)
        player["stats"]["hp"] -= final_dmg
        engine.log(f"{self.m_type.capitalize()} dealt {final_dmg} damage.")

    def move_towards(self, px, py, engine):
        dx, dy = px - self.x, py - self.y
        step_x, step_y = self.x, self.y
        
        if abs(dx) > abs(dy):
            step_x += 1 if dx > 0 else -1
            if not engine.is_walkable(step_x, step_y):
                step_x = self.x
                step_y += 1 if dy > 0 else -1
        else:
            step_y += 1 if dy > 0 else -1
            if not engine.is_walkable(step_x, step_y):
                step_y = self.y
                step_x += 1 if dx > 0 else -1

        if engine.is_walkable(step_x, step_y) and not engine.get_monster_at(step_x, step_y):
            self.x, self.y = step_x, step_y

    def run_away(self, px, py, engine):
        # Flee logic
        dx, dy = self.x - px, self.y - py
        step_x = self.x + (1 if dx > 0 else -1)
        step_y = self.y + (1 if dy > 0 else -1)
        if engine.is_walkable(step_x, self.y) and not engine.get_monster_at(step_x, self.y):
            self.x = step_x
        elif engine.is_walkable(self.x, step_y) and not engine.get_monster_at(self.x, step_y):
            self.y = step_y

class GameEngine:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.settings = app.settings
        self.colors = THEMES[self.settings["theme"]]
        
        self.is_running = True
        self.turn_event = threading.Event()
        self.images = {}
        
        self.floor_count = 1
        self.turn_count = 0
        
        self.player = {
            "stats": {"hp": 100, "max_hp": 100, "base_damage": 5, "base_defense": 0, "speed": 1, "xp": 0, "dodge": 0},
            "position": {"x": 1, "y": 1},
            "equipment": {"weapon": None, "armor": None, "shield": None}
        }
        
        self.ap = self.player["stats"]["speed"]
        self.upgrade_levels = {"damage": 0.0, "health": 0.0, "speed": 0}
        
        # Strict dictionary formats
        self.inventories = {"inventory": {}, "hotbar": {}}
        self.item_stats = {}
        
        self.map_grid = {}
        self.monsters = []
        self.chests = []
        self.staircase = (0, 0)
        
        # UI Overlays
        self.active_tooltip = None
        
        # Cheat sequence
        self.konami = ['Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'b', 'a']
        self.key_buffer = []
        self.cheat_enabled = False

        self.setup_ui()
        self.load_level()
        
        # Start Thread
        self.game_thread = threading.Thread(target=self.game_loop, daemon=True)
        self.game_thread.start()
        
        self.update_ui()
        self.root.bind("<Key>", self.handle_input)
        self.log("Welcome to the Dungeon! Use WASD/Arrows to move, Space to interact.")

    def setup_ui(self):
        self.root.geometry("1000x800")
        self.root.configure(bg=self.colors["bg"])
        
        self.left_frame = tk.Frame(self.root, bg=self.colors["ui"], width=400, height=800)
        self.left_frame.pack(side="left", fill="y")
        self.left_frame.pack_propagate(False)
        
        self.right_frame = tk.Frame(self.root, bg=self.colors["bg"], width=600, height=800)
        self.right_frame.pack(side="right", fill="both", expand=True)
        
        # Stats UI
        self.stats_lbl = tk.Label(self.left_frame, text="", bg=self.colors["ui"], fg=self.colors["text"], font=("Arial", 14, "bold"), justify="left")
        self.stats_lbl.pack(pady=10, padx=10, anchor="w")
        
        # Upgrades Button
        self.btn_upgrade = tk.Button(self.left_frame, text="Toggle Upgrades Menu", command=self.toggle_upgrades, bg="#444", fg="white")
        self.btn_upgrade.pack(pady=5)
        
        # Inventory Canvas
        self.inv_canvas = tk.Canvas(self.left_frame, width=380, height=220, bg=self.colors["bg"], highlightthickness=0)
        self.inv_canvas.pack(pady=10)
        self.inv_canvas.bind("<Button-1>", self.handle_inv_click)
        
        # Upgrades Overlay Frame
        self.upgrade_frame = tk.Frame(self.left_frame, bg="#222", width=380, height=220)
        self.upgrade_lbl = tk.Label(self.upgrade_frame, text="Upgrades Menu", bg="#222", fg="white", font=("Arial", 12, "bold"))
        self.upgrade_lbl.pack(pady=5)
        
        tk.Button(self.upgrade_frame, text="+ Damage Multiplier (Cost: 10 XP)", command=lambda: self.buy_upgrade("damage"), bg="#444", fg="white").pack(pady=5)
        tk.Button(self.upgrade_frame, text="+ Health Multiplier (Cost: 10 XP)", command=lambda: self.buy_upgrade("health"), bg="#444", fg="white").pack(pady=5)
        tk.Button(self.upgrade_frame, text="+ Speed (Cost: 30 XP)", command=lambda: self.buy_upgrade("speed"), bg="#444", fg="white").pack(pady=5)
        
        # Game Canvas
        self.game_canvas = tk.Canvas(self.right_frame, width=600, height=600, bg=self.colors["floor"], highlightthickness=0)
        self.game_canvas.pack(pady=10)
        
        # Terminal Log
        self.log_text = tk.Text(self.right_frame, height=8, bg="black", fg="lime", font=("Consolas", 10), state="disabled")
        self.log_text.pack(fill="x", padx=10, pady=5)
        
        # Cheat Entry
        self.cheat_entry = tk.Entry(self.right_frame, font=("Consolas", 12), bg="#111", fg="lime", insertbackground="lime")
        self.cheat_entry.bind("<Return>", self.on_cheat_enter)

    def log(self, text):
        self.log_text.config(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def toggle_upgrades(self):
        if self.upgrade_frame.winfo_ismapped():
            self.upgrade_frame.place_forget()
        else:
            # Place perfectly over inventory canvas
            self.upgrade_frame.place(in_=self.inv_canvas, x=0, y=0, relwidth=1, relheight=1)

    def buy_upgrade(self, stat):
        cost = 30 if stat == "speed" else 10
        if self.player["stats"]["xp"] >= cost:
            self.player["stats"]["xp"] -= cost
            if stat == "speed":
                self.player["stats"]["speed"] += 1
                self.upgrade_levels["speed"] += 1
            elif stat == "damage":
                self.upgrade_levels["damage"] += 0.1
            elif stat == "health":
                self.upgrade_levels["health"] += 0.1
                bonus = int(self.player["stats"]["max_hp"] * 0.1)
                self.player["stats"]["max_hp"] += bonus
                self.player["stats"]["hp"] += bonus
            self.log(f"Upgraded {stat}!")
            self.update_ui()
        else:
            self.log("Not enough XP!")

    def load_level(self):
        self.monsters.clear()
        self.chests.clear()
        self.map_grid.clear()
        
        map_dicts = random.choice(MAP_POOL)
        for tile in map_dicts:
            x, y, t = tile["x"], tile["y"], tile["type"]
            if t in ["wall", "floor"]:
                self.map_grid[(x, y)] = tile.copy()
            else:
                self.map_grid[(x, y)] = {"x": x, "y": y, "type": "floor"}
                if t == "player":
                    self.player["position"]["x"] = x
                    self.player["position"]["y"] = y
                elif t in ["skeleton", "goblin"]:
                    self.monsters.append(Monster(x, y, t, self.floor_count))
                elif t == "chest":
                    self.chests.append((x, y))
                elif t == "stairs":
                    self.staircase = (x, y)

    def is_walkable(self, x, y):
        if (x, y) not in self.map_grid: return False
        if self.map_grid[(x, y)]["type"] == "wall": return False
        return True

    def get_monster_at(self, x, y):
        for m in self.monsters:
            if m.x == x and m.y == y and m.hp > 0: return m
        return None

    def add_item(self, base_name):
        used_inv = set(self.inventories["inventory"].values())
        slot = None
        for y in range(3):
            for x in range(9):
                if (x, y) not in used_inv:
                    slot = (x, y)
                    break
            if slot: break

        if not slot:
            # Check hotbar
            used_hot = set(self.inventories["hotbar"].values())
            for x in range(9):
                if (x, 3) not in used_hot:
                    slot = (x, 3)
                    break

        if not slot:
            self.log("Inventory full!")
            return

        item_id = f"{base_name}_{random.randint(1000,9999)}"
        if slot[1] == 3:
            self.inventories["hotbar"][item_id] = slot
        else:
            self.inventories["inventory"][item_id] = slot
            
        self.item_stats[item_id] = BASE_ITEMS.get(base_name, {"type": "junk"}).copy()
        self.log(f"Looted {base_name}.")

    def open_chest(self):
        pool = LOOT_TABLES[min(self.floor_count, 3)]
        loot = random.choice(pool)
        self.add_item(loot)

    def get_image(self, name):
        if name not in self.images:
            try:
                self.images[name] = tk.PhotoImage(file=f"{name}.png")
            except:
                self.images[name] = None
        return self.images[name]

    def draw_entity(self, x, y, name, fallback_char, bg_color, emoji_fallback):
        cx, cy = x * 40, y * 40
        img = self.get_image(name)
        if img:
            self.game_canvas.create_image(cx+20, cy+20, image=img)
        else:
            if self.settings["fallback"] == "Emoji":
                self.game_canvas.create_text(cx+20, cy+20, text=emoji_fallback, font=("Arial", 20))
            else:
                text_col = get_contrast_color(bg_color)
                shape_func = self.game_canvas.create_rectangle if fallback_char in ['C', '▼'] else self.game_canvas.create_oval
                shape_func(cx+5, cy+5, cx+35, cy+35, fill=bg_color, outline="black")
                self.game_canvas.create_text(cx+20, cy+20, text=fallback_char, fill=text_col, font=("Arial", 16, "bold"))

    def update_ui(self):
        if not self.is_running: return
        
        # Update Stats
        base_dmg = self.player["stats"]["base_damage"]
        eq_dmg = sum([self.item_stats[i].get("damage", 0) for i in self.player["equipment"].values() if i])
        tot_dmg = int((base_dmg + eq_dmg) * (1 + self.upgrade_levels["damage"]))
        
        base_def = self.player["stats"]["base_defense"]
        eq_def = sum([self.item_stats[i].get("defense", 0) for i in self.player["equipment"].values() if i])
        
        stats_text = (
            f"Floor: {self.floor_count} | Turn: {self.turn_count}\n"
            f"HP: {self.player['stats']['hp']}/{self.player['stats']['max_hp']}\n"
            f"Damage: {tot_dmg} | Defense: {base_def + eq_def}\n"
            f"Speed: {self.player['stats']['speed']} | Dodge: {self.player['stats']['dodge']}%\n"
            f"XP: {self.player['stats']['xp']}"
        )
        self.stats_lbl.config(text=stats_text)
        
        # Draw Inventory & Hotbar
        self.inv_canvas.delete("all")
        # Grid lines
        for r in range(4):
            for c in range(9):
                y_off = 10 if r < 3 else 30
                x1, y1 = c * 40 + 10, r * 40 + y_off
                x2, y2 = x1 + 38, y1 + 38
                self.inv_canvas.create_rectangle(x1, y1, x2, y2, fill="#444", outline="#222")
        
        all_items = {**self.inventories["inventory"], **self.inventories["hotbar"]}
        equipped_ids = list(self.player["equipment"].values())
        
        for i_id, pos in all_items.items():
            cx, cy = pos[0], pos[1]
            y_off = 10 if cy < 3 else 30
            x1, y1 = cx * 40 + 10, cy * 40 + y_off
            
            # Simple placeholder for item graphic
            color = "#a67c00" if "Sword" in i_id else "#555555" if "Armor" in i_id or "Shield" in i_id else "#cc0000"
            self.inv_canvas.create_rectangle(x1+2, y1+2, x1+36, y1+36, fill=color, outline="white")
            self.inv_canvas.create_text(x1+19, y1+19, text=i_id[:2], fill="white", font=("Arial", 10, "bold"))
            
            if i_id in equipped_ids:
                self.inv_canvas.create_text(x1+30, y1+10, text="E", fill="lime", font=("Arial", 10, "bold"))

        # Draw Game Canvas
        self.game_canvas.delete("all")
        for pos, tile in self.map_grid.items():
            cx, cy = pos[0] * 40, pos[1] * 40
            color = self.colors["wall"] if tile["type"] == "wall" else self.colors["floor"]
            self.game_canvas.create_rectangle(cx, cy, cx+40, cy+40, fill=color, outline="")

        # Draw Chests & Stairs
        for cx, cy in self.chests:
            self.draw_entity(cx, cy, "chest", "C", "#d4af37", "🎁")
        
        sx, sy = self.staircase
        self.draw_entity(sx, sy, "staircase", "▼", "#888888", "🪜")

        # Draw Monsters
        for m in self.monsters:
            if m.hp > 0:
                color, emoji, char = ("#00aa00", "👺", "G") if m.m_type == "goblin" else ("#dddddd", "💀", "S")
                self.draw_entity(m.x, m.y, m.m_type, char, color, emoji)
                # Health Bar
                hx, hy = m.x * 40, m.y * 40
                pct = max(0, m.hp / m.max_hp)
                self.game_canvas.create_rectangle(hx+5, hy, hx+35, hy+4, fill="red", outline="")
                self.game_canvas.create_rectangle(hx+5, hy, hx+5+(30*pct), hy+4, fill="lime", outline="")

        # Draw Player
        px, py = self.player["position"]["x"], self.player["position"]["y"]
        self.draw_entity(px, py, "player", "@", "#0066cc", "🧙")

        if self.player["stats"]["hp"] <= 0:
            self.trigger_game_over()

    def handle_inv_click(self, event):
        for c in range(9):
            for r in range(4):
                y_off = 10 if r < 3 else 30
                x1, y1 = c * 40 + 10, r * 40 + y_off
                if x1 <= event.x <= x1+38 and y1 <= event.y <= y1+38:
                    clicked = None
                    all_items = {**self.inventories["inventory"], **self.inventories["hotbar"]}
                    for i_id, pos in all_items.items():
                        if pos == (c, r):
                            clicked = i_id; break
                    
                    if clicked:
                        self.show_item_tooltip(clicked, event.x_root, event.y_root)

    def show_item_tooltip(self, item_id, rx, ry):
        if self.active_tooltip:
            self.active_tooltip.destroy()
            
        self.active_tooltip = tk.Toplevel(self.root)
        self.active_tooltip.wm_overrideredirect(True)
        self.active_tooltip.geometry(f"+{rx}+{ry}")
        self.active_tooltip.configure(bg="black", bd=2, relief="ridge")
        
        stats = self.item_stats[item_id]
        name = item_id.split("_")[0]
        
        tk.Label(self.active_tooltip, text=name, bg="black", fg="yellow", font=("Arial", 10, "bold")).pack(padx=5, pady=2)
        for k, v in stats.items():
            if k != "type":
                tk.Label(self.active_tooltip, text=f"{k.capitalize()}: {v}", bg="black", fg="white", font=("Arial", 9)).pack()
                
        is_equipped = item_id in self.player["equipment"].values()
        if stats["type"] == "consumable":
            tk.Button(self.active_tooltip, text="Use", bg="#444", fg="white", command=lambda: self.use_item(item_id)).pack(fill="x")
        else:
            if is_equipped:
                tk.Button(self.active_tooltip, text="Unequip", bg="#444", fg="white", command=lambda: self.unequip_item(item_id)).pack(fill="x")
            else:
                tk.Button(self.active_tooltip, text="Equip", bg="#444", fg="white", command=lambda: self.equip_item(item_id)).pack(fill="x")
                
        tk.Button(self.active_tooltip, text="Close", bg="red", fg="white", command=self.active_tooltip.destroy).pack(fill="x")

    def equip_item(self, item_id):
        i_type = self.item_stats[item_id]["type"]
        self.player["equipment"][i_type] = item_id
        self.log(f"Equipped {item_id.split('_')[0]}.")
        self.active_tooltip.destroy()
        self.update_ui()

    def unequip_item(self, item_id):
        i_type = self.item_stats[item_id]["type"]
        self.player["equipment"][i_type] = None
        self.log(f"Unequipped {item_id.split('_')[0]}.")
        self.active_tooltip.destroy()
        self.update_ui()

    def use_item(self, item_id):
        stats = self.item_stats[item_id]
        if "hp" in stats:
            self.player["stats"]["hp"] = min(self.player["stats"]["max_hp"], self.player["stats"]["hp"] + stats["hp"])
            self.log(f"Used {item_id.split('_')[0]}, restored {stats['hp']} HP.")
            
        if item_id in self.inventories["inventory"]: del self.inventories["inventory"][item_id]
        if item_id in self.inventories["hotbar"]: del self.inventories["hotbar"][item_id]
        
        self.active_tooltip.destroy()
        self.update_ui()

    def handle_input(self, event):
        if not self.is_running or self.player["stats"]["hp"] <= 0: return

        # Cheat Tracker
        self.key_buffer.append(event.keysym)
        if len(self.key_buffer) > 10: self.key_buffer.pop(0)
        if self.key_buffer == self.konami and not self.cheat_enabled:
            self.cheat_enabled = True
            self.cheat_entry.place(in_=self.log_text, relx=0, rely=0, relwidth=1)
            self.cheat_entry.focus_set()
            self.log("Cheat terminal unlocked! Enter +hp, +def, +dodge")

        if self.ap <= 0: return # Wait for thread

        dx, dy = 0, 0
        if event.keysym in ['w', 'W', 'Up']: dy = -1
        elif event.keysym in ['s', 'S', 'Down']: dy = 1
        elif event.keysym in ['a', 'A', 'Left']: dx = -1
        elif event.keysym in ['d', 'D', 'Right']: dx = 1
        elif event.keysym == 'space':
            self.interact()
            return
            
        if dx != 0 or dy != 0:
            nx = self.player["position"]["x"] + dx
            ny = self.player["position"]["y"] + dy
            
            monster = self.get_monster_at(nx, ny)
            if monster:
                self.attack_monster(monster)
                self.consume_ap()
            elif self.is_walkable(nx, ny):
                self.player["position"]["x"] = nx
                self.player["position"]["y"] = ny
                self.consume_ap()

    def on_cheat_enter(self, event):
        cmd = self.cheat_entry.get().strip()
        if cmd == "+hp":
            self.player["stats"]["max_hp"] += 500
            self.player["stats"]["hp"] = self.player["stats"]["max_hp"]
            self.log("Cheat: Max HP increased!")
        elif cmd == "+def":
            self.player["stats"]["base_defense"] += 50
            self.log("Cheat: Defense increased!")
        elif cmd == "+dodge":
            self.player["stats"]["dodge"] += 50
            self.log("Cheat: Dodge increased!")
            
        self.cheat_entry.delete(0, tk.END)
        self.cheat_entry.place_forget()
        self.update_ui()

    def interact(self):
        px, py = self.player["position"]["x"], self.player["position"]["y"]
        if self.staircase == (px, py):
            self.floor_count += 1
            self.log(f"Descended to floor {self.floor_count}!")
            self.load_level()
            self.ap = self.player["stats"]["speed"]
            self.update_ui()
            return
            
        chest_to_remove = None
        for c in self.chests:
            if c == (px, py):
                chest_to_remove = c
                break
        if chest_to_remove:
            self.chests.remove(chest_to_remove)
            self.open_chest()
            self.consume_ap()

    def consume_ap(self):
        self.ap -= 1
        self.update_ui()
        if self.ap <= 0:
            self.turn_event.set()

    def attack_monster(self, monster):
        base_dmg = self.player["stats"]["base_damage"]
        eq_dmg = sum([self.item_stats[i].get("damage", 0) for i in self.player["equipment"].values() if i])
        tot_dmg = int((base_dmg + eq_dmg) * (1 + self.upgrade_levels["damage"]))
        
        monster.hp -= tot_dmg
        self.log(f"You hit {monster.m_type.capitalize()} for {tot_dmg} damage.")
        if monster.hp <= 0:
            self.monsters.remove(monster)
            xp_gain = 5 * self.floor_count
            self.player["stats"]["xp"] += xp_gain
            self.log(f"Killed {monster.m_type.capitalize()}! +{xp_gain} XP.")

    def game_loop(self):
        while self.is_running:
            self.turn_event.wait()
            if not self.is_running: break
            
            self.turn_count += 1
            for m in list(self.monsters):
                if m.hp > 0: m.act(self.player, self)
                
            self.ap = self.player["stats"]["speed"]
            self.turn_event.clear()
            self.root.after(0, self.update_ui)

    def trigger_game_over(self):
        self.is_running = False
        self.turn_event.set() # Release thread
        self.game_canvas.create_rectangle(100, 200, 500, 400, fill="black", outline="red", width=5)
        self.game_canvas.create_text(300, 260, text="GAME OVER", fill="red", font=("Arial", 36, "bold"))
        restart_btn = tk.Button(self.game_canvas, text="Restart", command=self.restart_game, bg="red", fg="white", font=("Arial", 16))
        self.game_canvas.create_window(300, 340, window=restart_btn)

    def restart_game(self):
        self.is_running = False
        self.turn_event.set()
        time.sleep(0.1) # Let thread exit safely
        self.root.destroy()
        self.app.root.deiconify()

    def shutdown(self):
        self.is_running = False
        self.turn_event.set()

# --- MAIN APP MENU ---

class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Roguelike Dungeon Crawler")
        self.root.geometry("400x400")
        
        self.settings = {"theme": "Default", "fallback": "Text"}
        self.settings_win = None
        self.game_toplevel = None
        self.engine = None
        
        # Build Main Menu
        tk.Label(self.root, text="DUNGEON", font=("Arial", 28, "bold")).pack(pady=40)
        
        tk.Button(self.root, text="Play", command=self.play, width=15, font=("Arial", 14)).pack(pady=10)
        tk.Button(self.root, text="Settings", command=self.open_settings, width=15, font=("Arial", 14)).pack(pady=10)
        tk.Button(self.root, text="Quit", command=self.root.destroy, width=15, font=("Arial", 14)).pack(pady=10)

    def play(self):
        self.root.withdraw()
        self.game_toplevel = tk.Toplevel(self.root)
        self.game_toplevel.title("Dungeon")
        self.game_toplevel.protocol("WM_DELETE_WINDOW", self.on_game_close)
        self.engine = GameEngine(self.game_toplevel, self)

    def on_game_close(self):
        if self.engine: self.engine.shutdown()
        self.root.destroy()

    def open_settings(self):
        if self.settings_win and self.settings_win.winfo_exists():
            self.settings_win.lift()
            return
            
        self.settings_win = tk.Toplevel(self.root)
        self.settings_win.title("Settings")
        self.settings_win.geometry("300x300")
        
        tk.Label(self.settings_win, text="Theme:", font=("Arial", 12, "bold")).pack(pady=5)
        for t in THEMES.keys():
            tk.Radiobutton(self.settings_win, text=t, value=t, variable=tk.StringVar(value=self.settings["theme"]), command=lambda v=t: self.update_setting("theme", v)).pack()
            
        tk.Label(self.settings_win, text="Image Fallback Style:", font=("Arial", 12, "bold")).pack(pady=(15, 5))
        for f in ["Text", "Emoji"]:
            tk.Radiobutton(self.settings_win, text=f, value=f, variable=tk.StringVar(value=self.settings["fallback"]), command=lambda v=f: self.update_setting("fallback", v)).pack()

    def update_setting(self, key, val):
        self.settings[key] = val

if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()