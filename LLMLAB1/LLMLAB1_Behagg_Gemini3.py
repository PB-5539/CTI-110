import tkinter as tk
import math
import random
import time
import threading
import os

# --- Configuration & Data Structures ---
GRID_W, GRID_H = 20, 15
TILE_SIZE = 32

item_stats = {
    "sword": {"damage": 5, "defense": 0, "block": 0, "type": "weapon"},
    "shield": {"damage": 0, "defense": 3, "block": 10, "type": "armor"},
    "potion": {"heal": 30, "type": "consumable"},
    "boots": {"speed": 1, "defense": 1, "type": "armor"}
}

loot_table = {
    1: ["sword", "potion"],
    2: ["sword", "shield", "potion", "potion"],
    3: ["shield", "potion", "boots", "sword"]
}

# Pre-set list of map combinations (list containing dictionaries of tile locations)
map_presets = []
for i in range(3):
    temp_map = {}
    for x in range(GRID_W):
        for y in range(GRID_H):
            if x == 0 or y == 0 or x == GRID_W-1 or y == GRID_H-1:
                temp_map[(x, y)] = "wall"
            else:
                # Add random interior walls
                if random.random() < 0.15 and x > 2 and y > 2:
                    temp_map[(x, y)] = "wall"
                else:
                    temp_map[(x, y)] = "floor"
    map_presets.append(temp_map)

# Player Data Structure
player_data = {
    "inventory_data": {
        "inventory": {}, # format: {item_name_id: (x, y)} for 9x3 grid
        "hotbar": {}     # format: {item_name_id: (x, 0)} for 9x1 grid
    },
    "player_stats": {
        "hp": 100, "max_hp": 100, 
        "base_damage": 5, "base_defense": 0, 
        "speed": 1, "xp": 0
    },
    "position": {"x": 1, "y": 1},
    "equipped": {"weapon": None, "armor": None},
    "multipliers": {"damage": 1.0, "health": 1.0, "speed": 1.0}
}


# --- Entities ---
class Monster:
    def __init__(self, name, x, y, hp, damage, xp_value, m_type="goblin"):
        self.name = name
        self.type = m_type
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.damage = damage
        self.xp_value = xp_value

    def take_turn(self, px, py, game_engine):
        if self.hp <= 0: return

        dx = px - self.x
        dy = py - self.y
        dist = abs(dx) + abs(dy) # Manhattan distance

        # Run away if low on health
        if self.hp < self.max_hp * 0.2:
            step_x = -1 if dx > 0 else (1 if dx < 0 else 0)
            step_y = -1 if dy > 0 else (1 if dy < 0 else 0)
        else:
            # Move towards player
            step_x = 1 if dx > 0 else (-1 if dx < 0 else 0)
            step_y = 1 if dy > 0 else (-1 if dy < 0 else 0)

        if dist == 1:
            # Attack player if adjacent
            game_engine.monster_attacks(self)
        else:
            # Move
            if abs(dx) > abs(dy):
                nx, ny = self.x + step_x, self.y
                if game_engine.is_walkable(nx, ny):
                    self.x, self.y = nx, ny
                    return
            nx, ny = self.x, self.y + step_y
            if game_engine.is_walkable(nx, ny):
                self.x, self.y = nx, ny


# --- Game Engine (Logic & Threading) ---
class GameEngine:
    def __init__(self, ui_callback, log_callback):
        self.ui_callback = ui_callback
        self.log_callback = log_callback
        
        self.floor = 1
        self.turn_count = 0
        self.current_map = {}
        self.monsters = []
        self.chests = {}
        self.stairs = (0, 0)
        
        self.moves_left = 1
        self.game_over = False
        
        self.turn_event = threading.Event()
        self.running = True
        self.logic_thread = threading.Thread(target=self.logic_loop, daemon=True)
        
        self.item_counter = 0 # To give unique dictionary keys to items

        self.generate_level()
        self.logic_thread.start()

    def generate_level(self):
        # Load map from preset
        preset = random.choice(map_presets)
        self.current_map = preset.copy()
        self.monsters.clear()
        self.chests.clear()
        
        # Place Player
        player_data["position"] = {"x": 1, "y": 1}
        
        # Place Stairs
        while True:
            sx, sy = random.randint(2, GRID_W-2), random.randint(2, GRID_H-2)
            if self.current_map[(sx, sy)] == "floor":
                self.stairs = (sx, sy)
                break
                
        # Place Chests
        for _ in range(random.randint(1, 3)):
            cx, cy = random.randint(2, GRID_W-2), random.randint(2, GRID_H-2)
            if self.current_map[(cx, cy)] == "floor" and (cx, cy) != self.stairs:
                loot_level = min(self.floor, max(loot_table.keys()))
                self.chests[(cx, cy)] = random.choice(loot_table[loot_level])
                
        # Spawn Monsters
        num_monsters = min(10, self.floor + 3)
        for i in range(num_monsters):
            mx, my = random.randint(2, GRID_W-2), random.randint(2, GRID_H-2)
            if self.current_map[(mx, my)] == "floor" and (mx, my) != self.stairs and (mx, my) not in self.chests:
                m_type = random.choice(["goblin", "skeleton", "orc"])
                hp = 15 + (self.floor * 5)
                dmg = 2 + self.floor
                xp = 10 + (self.floor * 5)
                self.monsters.append(Monster(f"{m_type}_{i}", mx, my, hp, dmg, xp, m_type))
                
        self.update_stats()

    def is_walkable(self, x, y):
        if self.current_map.get((x, y)) == "wall": return False
        if player_data["position"]["x"] == x and player_data["position"]["y"] == y: return False
        for m in self.monsters:
            if m.x == x and m.y == y and m.hp > 0: return False
        return True

    def get_monster_at(self, x, y):
        for m in self.monsters:
            if m.x == x and m.y == y and m.hp > 0:
                return m
        return None

    def logic_loop(self):
        while self.running:
            self.turn_event.wait() # Wait for player action
            if not self.running: break
            
            if not self.game_over:
                px = player_data["position"]["x"]
                py = player_data["position"]["y"]
                for m in self.monsters:
                    m.take_turn(px, py, self)
                
                self.turn_count += 1
                self.moves_left = self.get_total_speed()
                
            self.turn_event.clear()
            self.ui_callback()

    def player_move(self, dx, dy):
        if self.game_over or self.moves_left <= 0: return
        
        px = player_data["position"]["x"]
        py = player_data["position"]["y"]
        nx, ny = px + dx, py + dy
        
        target_monster = self.get_monster_at(nx, ny)
        if target_monster:
            self.player_attacks(target_monster)
            self.end_player_action()
            return

        if self.is_walkable(nx, ny):
            player_data["position"]["x"] = nx
            player_data["position"]["y"] = ny
            self.check_tile_events(nx, ny)
            self.end_player_action()

    def player_attacks(self, monster):
        dmg = int(self.get_total_damage())
        monster.hp -= dmg
        self.log_callback(f"Player hit {monster.type} for {dmg} dmg!")
        if monster.hp <= 0:
            self.log_callback(f"{monster.type} died! +{monster.xp_value} XP.")
            player_data["player_stats"]["xp"] += monster.xp_value
            self.update_stats()

    def monster_attacks(self, monster):
        defense = self.get_total_defense()
        dmg = max(0, monster.damage - defense)
        
        # Check block chance
        block = 0
        armor = player_data["equipped"]["armor"]
        if armor: block = item_stats[armor.split("_")[0]].get("block", 0)
        
        if random.randint(1, 100) <= block:
            self.log_callback(f"{monster.type} attacked, but you BLOCKED it!")
        else:
            player_data["player_stats"]["hp"] -= dmg
            self.log_callback(f"{monster.type} dealt {dmg} damage to player.")
            
        if player_data["player_stats"]["hp"] <= 0:
            self.game_over = True
            self.log_callback("YOU DIED! Game Over.")
        self.update_stats()

    def check_tile_events(self, x, y):
        if (x, y) == self.stairs:
            self.floor += 1
            self.log_callback(f"Descended to floor {self.floor}!")
            self.generate_level()
            
        if (x, y) in self.chests:
            item = self.chests.pop((x, y))
            self.add_item_to_inventory(item)
            self.log_callback(f"Opened chest and found: {item}!")

    def add_item_to_inventory(self, item_base_name):
        self.item_counter += 1
        item_id = f"{item_base_name}_{self.item_counter}"
        
        inv = player_data["inventory_data"]["inventory"]
        # Find empty spot in 9x3
        occupied = list(inv.values())
        for y in range(3):
            for x in range(9):
                if (x, y) not in occupied:
                    inv[item_id] = (x, y)
                    return
        self.log_callback("Inventory full!")

    def use_item(self, item_id):
        base_name = item_id.split("_")[0]
        i_type = item_stats[base_name]["type"]
        
        if i_type == "consumable":
            heal = item_stats[base_name].get("heal", 0)
            player_data["player_stats"]["hp"] = min(
                player_data["player_stats"]["hp"] + heal,
                self.get_max_hp()
            )
            self.log_callback(f"Used {base_name}, healed {heal} HP.")
            del player_data["inventory_data"]["inventory"][item_id]
            
        elif i_type == "weapon":
            if player_data["equipped"]["weapon"] == item_id:
                player_data["equipped"]["weapon"] = None
                self.log_callback(f"Unequipped {base_name}.")
            else:
                player_data["equipped"]["weapon"] = item_id
                self.log_callback(f"Equipped {base_name}.")
                
        elif i_type == "armor":
            if player_data["equipped"]["armor"] == item_id:
                player_data["equipped"]["armor"] = None
                self.log_callback(f"Unequipped {base_name}.")
            else:
                player_data["equipped"]["armor"] = item_id
                self.log_callback(f"Equipped {base_name}.")
                
        self.update_stats()
        self.ui_callback()

    def end_player_action(self):
        self.moves_left -= 1
        if self.moves_left <= 0:
            self.turn_event.set()
        else:
            self.ui_callback()

    def get_max_hp(self):
        return int(player_data["player_stats"]["max_hp"] * player_data["multipliers"]["health"])

    def get_total_speed(self):
        spd = player_data["player_stats"]["speed"]
        armor = player_data["equipped"]["armor"]
        if armor: spd += item_stats[armor.split("_")[0]].get("speed", 0)
        return math.floor(spd * player_data["multipliers"]["speed"])

    def get_total_damage(self):
        dmg = player_data["player_stats"]["base_damage"]
        wpn = player_data["equipped"]["weapon"]
        if wpn: dmg += item_stats[wpn.split("_")[0]].get("damage", 0)
        return math.floor(dmg * player_data["multipliers"]["damage"])

    def get_total_defense(self):
        def_val = player_data["player_stats"]["base_defense"]
        armor = player_data["equipped"]["armor"]
        if armor: def_val += item_stats[armor.split("_")[0]].get("defense", 0)
        wpn = player_data["equipped"]["weapon"]
        if wpn: def_val += item_stats[wpn.split("_")[0]].get("defense", 0)
        return def_val

    def update_stats(self):
        # Force clamp HP
        max_h = self.get_max_hp()
        if player_data["player_stats"]["hp"] > max_h:
            player_data["player_stats"]["hp"] = max_h

    def upgrade_skill(self, stat):
        cost = 20
        if player_data["player_stats"]["xp"] >= cost:
            player_data["player_stats"]["xp"] -= cost
            if stat == "speed":
                player_data["multipliers"]["speed"] += 0.5
            elif stat == "damage":
                player_data["multipliers"]["damage"] += 0.2
            elif stat == "health":
                player_data["multipliers"]["health"] += 0.2
                self.update_stats()
            self.log_callback(f"Upgraded {stat} multiplier!")
            self.ui_callback()
        else:
            self.log_callback("Not enough XP!")

    def cleanup(self):
        self.running = False
        self.turn_event.set()


# --- Game Window UI ---
class GameWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("Dungeon Crawler")
        self.geometry("1000x650")
        self.configure(bg="#222222")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.image_cache = {}
        
        # --- Layout ---
        self.left_frame = tk.Frame(self, bg="#333333", width=300)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.right_frame = tk.Frame(self, bg="#222222")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # --- Stats UI (Left Top) ---
        self.stats_lbl = tk.Label(self.left_frame, text="", bg="#333333", fg="white", font=("Arial", 12), justify=tk.LEFT)
        self.stats_lbl.pack(pady=10, padx=10, anchor="w")
        
        self.skill_btn = tk.Button(self.left_frame, text="Toggle Skill Tree", command=self.toggle_skill_tree, bg="#555555", fg="white")
        self.skill_btn.pack(fill=tk.X, padx=10)
        
        # --- Container for Inv and Skills (Left Bottom) ---
        self.container = tk.Frame(self.left_frame, bg="#333333")
        self.container.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.inv_canvas = tk.Canvas(self.container, width=288, height=128, bg="#444444", highlightthickness=0)
        self.inv_canvas.place(x=6, y=0)
        self.inv_canvas.bind("<Button-1>", self.on_inv_click)
        
        self.skill_frame = tk.Frame(self.container, bg="#2a2a2a")
        tk.Label(self.skill_frame, text="SKILL TREE (20 XP each)", bg="#2a2a2a", fg="#ffcc00", font=("Arial", 10, "bold")).pack(pady=10)
        tk.Button(self.skill_frame, text="+ Damage", command=lambda: self.engine.upgrade_skill("damage"), bg="#882222", fg="white").pack(fill=tk.X, pady=5, padx=20)
        tk.Button(self.skill_frame, text="+ Health", command=lambda: self.engine.upgrade_skill("health"), bg="#228822", fg="white").pack(fill=tk.X, pady=5, padx=20)
        tk.Button(self.skill_frame, text="+ Speed (Rare)", command=lambda: self.engine.upgrade_skill("speed"), bg="#222288", fg="white").pack(fill=tk.X, pady=5, padx=20)
        
        self.skill_open = False
        
        # --- Game Canvas (Right Top) ---
        self.canvas = tk.Canvas(self.right_frame, width=GRID_W*TILE_SIZE, height=GRID_H*TILE_SIZE, bg="#111111", highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # --- Text Terminal (Right Bottom) ---
        self.terminal = tk.Text(self.right_frame, height=8, bg="#000000", fg="#00ff00", font=("Consolas", 10), state=tk.DISABLED)
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- Initialize Engine ---
        self.engine = GameEngine(self.schedule_draw, self.log_msg)
        
        # --- Bindings ---
        self.bind("<w>", lambda e: self.engine.player_move(0, -1))
        self.bind("<s>", lambda e: self.engine.player_move(0, 1))
        self.bind("<a>", lambda e: self.engine.player_move(-1, 0))
        self.bind("<d>", lambda e: self.engine.player_move(1, 0))
        self.bind("<Up>", lambda e: self.engine.player_move(0, -1))
        self.bind("<Down>", lambda e: self.engine.player_move(0, 1))
        self.bind("<Left>", lambda e: self.engine.player_move(-1, 0))
        self.bind("<Right>", lambda e: self.engine.player_move(1, 0))
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        self.draw()

    def load_image(self, name):
        if name in self.image_cache: return self.image_cache[name]
        try:
            filename = f"{name}.png"
            if os.path.exists(filename):
                img = tk.PhotoImage(file=filename)
                self.image_cache[name] = img
                return img
        except: pass
        self.image_cache[name] = None
        return None

    def log_msg(self, msg):
        self.terminal.config(state=tk.NORMAL)
        self.terminal.insert(tk.END, msg + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state=tk.DISABLED)

    def schedule_draw(self):
        self.after(0, self.draw)

    def toggle_skill_tree(self):
        self.skill_open = not self.skill_open
        if self.skill_open:
            self.skill_frame.place(x=0, y=0, relwidth=1, relheight=1)
        else:
            self.skill_frame.place_forget()

    def on_inv_click(self, event):
        grid_x, grid_y = event.x // TILE_SIZE, event.y // TILE_SIZE
        inv = player_data["inventory_data"]["inventory"]
        for item_id, coords in list(inv.items()):
            if coords == (grid_x, grid_y):
                self.engine.use_item(item_id)
                break

    def on_canvas_click(self, event):
        x, y = event.x // TILE_SIZE, event.y // TILE_SIZE
        px = player_data["position"]["x"]
        py = player_data["position"]["y"]
        if abs(px - x) + abs(py - y) == 1:
            monster = self.engine.get_monster_at(x, y)
            if monster:
                self.engine.player_attacks(monster)
                self.engine.end_player_action()

    def draw(self):
        self.canvas.delete("all")
        
        # Draw Map
        for (x, y), tile in self.engine.current_map.items():
            img = self.load_image(tile)
            cx, cy = x * TILE_SIZE, y * TILE_SIZE
            if img:
                self.canvas.create_image(cx, cy, image=img, anchor=tk.NW)
            else:
                color = "#444444" if tile == "wall" else "#222222"
                self.canvas.create_rectangle(cx, cy, cx+TILE_SIZE, cy+TILE_SIZE, fill=color, outline="#111111")
                
        # Draw Stairs
        sx, sy = self.engine.stairs
        img = self.load_image("stairs")
        if img:
            self.canvas.create_image(sx*TILE_SIZE, sy*TILE_SIZE, image=img, anchor=tk.NW)
        else:
            self.canvas.create_rectangle(sx*TILE_SIZE, sy*TILE_SIZE, sx*TILE_SIZE+TILE_SIZE, sy*TILE_SIZE+TILE_SIZE, fill="#8888aa")
            self.canvas.create_text(sx*TILE_SIZE+16, sy*TILE_SIZE+16, text="S", fill="white")

        # Draw Chests
        for cx, cy in self.engine.chests:
            img = self.load_image("chest")
            if img:
                self.canvas.create_image(cx*TILE_SIZE, cy*TILE_SIZE, image=img, anchor=tk.NW)
            else:
                self.canvas.create_rectangle(cx*TILE_SIZE, cy*TILE_SIZE, cx*TILE_SIZE+TILE_SIZE, cy*TILE_SIZE+TILE_SIZE, fill="#aa8800")
                self.canvas.create_text(cx*TILE_SIZE+16, cy*TILE_SIZE+16, text="C", fill="white")

        # Draw Monsters
        for m in self.engine.monsters:
            if m.hp > 0:
                img = self.load_image(m.type)
                if img:
                    self.canvas.create_image(m.x*TILE_SIZE, m.y*TILE_SIZE, image=img, anchor=tk.NW)
                else:
                    self.canvas.create_oval(m.x*TILE_SIZE+2, m.y*TILE_SIZE+2, m.x*TILE_SIZE+TILE_SIZE-2, m.y*TILE_SIZE+TILE_SIZE-2, fill="red")
                # HP Bar
                hp_pct = max(0, m.hp / m.max_hp)
                self.canvas.create_rectangle(m.x*TILE_SIZE, m.y*TILE_SIZE-5, m.x*TILE_SIZE+TILE_SIZE, m.y*TILE_SIZE-2, fill="black")
                self.canvas.create_rectangle(m.x*TILE_SIZE, m.y*TILE_SIZE-5, m.x*TILE_SIZE+(TILE_SIZE*hp_pct), m.y*TILE_SIZE-2, fill="red")

        # Draw Player
        px, py = player_data["position"]["x"], player_data["position"]["y"]
        img = self.load_image("player")
        if img:
            self.canvas.create_image(px*TILE_SIZE, py*TILE_SIZE, image=img, anchor=tk.NW)
        else:
            self.canvas.create_oval(px*TILE_SIZE+4, py*TILE_SIZE+4, px*TILE_SIZE+TILE_SIZE-4, py*TILE_SIZE+TILE_SIZE-4, fill="#00ff00")

        # Draw Inventory
        self.inv_canvas.delete("all")
        for x in range(9):
            for y in range(3):
                self.inv_canvas.create_rectangle(x*TILE_SIZE, y*TILE_SIZE, x*TILE_SIZE+TILE_SIZE, y*TILE_SIZE+TILE_SIZE, outline="#666666")
                
        for item_id, (ix, iy) in player_data["inventory_data"]["inventory"].items():
            base_name = item_id.split("_")[0]
            img = self.load_image(base_name)
            cx, cy = ix*TILE_SIZE, iy*TILE_SIZE
            if img:
                self.inv_canvas.create_image(cx, cy, image=img, anchor=tk.NW)
            else:
                color = "cyan" if item_stats[base_name]["type"] == "weapon" else ("magenta" if item_stats[base_name]["type"] == "armor" else "yellow")
                self.inv_canvas.create_rectangle(cx+4, cy+4, cx+TILE_SIZE-4, cy+TILE_SIZE-4, fill=color)
                self.inv_canvas.create_text(cx+16, cy+16, text=base_name[0].upper(), fill="black")
                
            # Outline if equipped
            if player_data["equipped"]["weapon"] == item_id or player_data["equipped"]["armor"] == item_id:
                self.inv_canvas.create_rectangle(cx+1, cy+1, cx+TILE_SIZE-1, cy+TILE_SIZE-1, outline="#00ff00", width=2)

        # Draw UI Stats
        hp = player_data["player_stats"]["hp"]
        mhp = self.engine.get_max_hp()
        dmg = self.engine.get_total_damage()
        dfn = self.engine.get_total_defense()
        spd = self.engine.get_total_speed()
        xp = player_data["player_stats"]["xp"]
        
        stat_text = (
            f"HEALTH: {hp}/{mhp}\n"
            f"DAMAGE: {dmg}\n"
            f"DEFENSE: {dfn}\n"
            f"SPEED: {spd} (Moves: {self.engine.moves_left})\n"
            f"XP: {xp}\n"
            f"FLOOR: {self.engine.floor}\n"
            f"TURN: {self.engine.turn_count}\n"
        )
        self.stats_lbl.config(text=stat_text)

        if self.engine.game_over:
            self.canvas.create_rectangle(0, 0, GRID_W*TILE_SIZE, GRID_H*TILE_SIZE, fill="black", stipple="gray50")
            self.canvas.create_text(GRID_W*TILE_SIZE/2, GRID_H*TILE_SIZE/2, text="GAME OVER", fill="red", font=("Arial", 36, "bold"))

    def on_close(self):
        self.engine.cleanup()
        self.master.destroy()


# --- Main Menu & App Root ---
class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Main Menu")
        self.root.geometry("400x300")
        self.root.configure(bg="#222222")
        
        tk.Label(self.root, text="DUNGEON CRAWLER", font=("Arial", 24, "bold"), bg="#222222", fg="#00ff00").pack(pady=40)
        
        btn_frame = tk.Frame(self.root, bg="#222222")
        btn_frame.pack()
        
        tk.Button(btn_frame, text="Play", width=20, command=self.open_game, bg="#444444", fg="white", font=("Arial", 12)).pack(pady=5)
        tk.Button(btn_frame, text="Settings", width=20, command=self.open_settings, bg="#444444", fg="white", font=("Arial", 12)).pack(pady=5)
        tk.Button(btn_frame, text="Quit", width=20, command=self.root.destroy, bg="#882222", fg="white", font=("Arial", 12)).pack(pady=5)
        
    def open_game(self):
        self.root.withdraw() # Hide main menu while playing
        GameWindow(self.root)
        
    def open_settings(self):
        top = tk.Toplevel(self.root)
        top.title("Settings")
        top.geometry("250x150")
        top.configure(bg="#333333")
        tk.Label(top, text="Miscellaneous Settings", bg="#333333", fg="white", font=("Arial", 12)).pack(pady=20)
        tk.Button(top, text="Close", command=top.destroy, bg="#555555", fg="white").pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()