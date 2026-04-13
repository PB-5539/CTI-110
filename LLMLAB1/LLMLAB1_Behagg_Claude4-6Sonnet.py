"""
Dungeon Crawler - A Roguelike Game
===================================
Place image files (goblin.png, skeleton.png, player.png, floor.png,
wall.png, stairs.png, chest.png, sword.png, shield.png, potion.png)
in the same directory as this script.

Controls:
  Arrow Keys / WASD  - Move player
  1-9                - Select hotbar slot
  I                  - Open/close inventory
  Space              - Interact (open chest / descend stairs)
"""

import math
import random
import time
import tkinter as tk
from tkinter import ttk, messagebox
import threading

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
TILE  = 24          # pixel size of one grid tile
COLS  = 30          # map width  (tiles)
ROWS  = 22          # map height (tiles)
FPS   = 30
MAX_FLOORS = 50

# ─────────────────────────────────────────────
#  LEVEL GENERATION CONSTANTS
# ─────────────────────────────────────────────
GEN_BASE_ROOMS = 12        # starting number of rooms per floor
GEN_ROOMS_PER_FLOOR = 1   # increase rooms every N floors
GEN_MAX_ROOMS = 25         # cap max rooms per floor
GEN_CORRIDOR_MIN = 2      # minimum corridor length
GEN_CORRIDOR_MAX = 8      # maximum corridor length
GEN_CHEST_MIN = 3         # minimum chests per floor
GEN_CHEST_MAX = 7         # maximum chests per floor
GEN_MONSTER_MIN = 2       # minimum monsters per floor
GEN_MONSTER_MAX = 12      # maximum monsters per floor

COLORS = {
    "bg":          "#0d0d0f",
    "panel":       "#14141a",
    "border":      "#2a2a3a",
    "accent":      "#c8a84b",
    "accent2":     "#7b5ea7",
    "hp_full":     "#3ddc84",
    "hp_low":      "#e05252",
    "text":        "#ddd8cc",
    "dim":         "#6b6878",
    "wall":        "#1e1e2e",
    "floor":       "#252535",
    "player":      "#f0d080",
    "goblin":      "#5a9e5a",
    "skeleton":    "#a0a0c0",
    "stairs":      "#c8a84b",
    "chest":       "#c87832",
    "slot_bg":     "#1a1a28",
    "slot_sel":    "#3a3050",
    "slot_border": "#3a3a55",
    "button":      "#1e1e2e",
    "button_h":    "#2e2e4e",
}

# ─────────────────────────────────────────────
#  ITEM STATS DATABASE
# ─────────────────────────────────────────────
ITEM_STATS = {
    "sword":    {"type": "weapon",  "damage": 8,  "value": 20, "stack": 1},
    "shield":   {"type": "shield",  "defense": 4, "value": 15, "stack": 1},
    "potion":   {"type": "consumable", "heal": 25, "value": 10, "stack": 5},
    "gold":     {"type": "currency","value": 1,   "stack": 99},
    "dagger":   {"type": "weapon",  "damage": 5,  "value": 12, "stack": 1},
    "bow":      {"type": "weapon",  "damage": 6,  "value": 18, "stack": 1},
    "chest_armor": {"type": "armor","defense": 6, "value": 25, "stack": 1},
    "torch":    {"type": "misc",    "light": 3,   "value": 5,  "stack": 10},
    "elixir":   {"type": "consumable", "heal": 75, "value": 120, "stack": 2},
    "magic_ring": {"type": "misc",  "value": 200, "stack": 1},
    "greatsword": {"type": "weapon", "damage": 14, "value": 150, "stack": 1},
    "plate_armor": {"type": "armor", "defense": 12, "value": 180, "stack": 1},
    "gem": {"type": "currency", "value": 10, "stack": 20},
    "wooden_shield": {"type": "shield", "defense": 3, "value": 12, "stack": 1},
    "iron_shield": {"type": "shield", "defense": 5, "value": 35, "stack": 1},
    "steel_shield": {"type": "shield", "defense": 7, "value": 60, "stack": 1},
    "leather_armor": {"type": "armor", "defense": 4, "value": 18, "stack": 1},
    "chain_mail": {"type": "armor", "defense": 8, "value": 45, "stack": 1},
    "bronze_armor": {"type": "armor", "defense": 10, "value": 85, "stack": 1},
    "dragon_scale": {"type": "armor", "defense": 15, "value": 300, "stack": 1},
    "mithril_sword": {"type": "weapon", "damage": 16, "value": 200, "stack": 1},
    "dragon_slayer": {"type": "weapon", "damage": 20, "value": 400, "stack": 1},
    "ancient_bow": {"type": "weapon", "damage": 12, "value": 120, "stack": 1},
    "crossbow": {"type": "weapon", "damage": 10, "value": 80, "stack": 1},
    "mace": {"type": "weapon", "damage": 11, "value": 70, "stack": 1},
    "battle_axe": {"type": "weapon", "damage": 13, "value": 110, "stack": 1},
    "spear": {"type": "weapon", "damage": 9, "value": 50, "stack": 1},
    "healing_potion": {"type": "consumable", "heal": 50, "value": 40, "stack": 10},
    "minor_elixir": {"type": "consumable", "heal": 40, "value": 60, "stack": 5},
    "legendary_elixir": {"type": "consumable", "heal": 150, "value": 500, "stack": 1},
    "ruby": {"type": "currency", "value": 50, "stack": 5},
    "sapphire": {"type": "currency", "value": 50, "stack": 5},
    "diamond": {"type": "currency", "value": 100, "stack": 2},
    "scroll_of_power": {"type": "misc", "value": 150, "stack": 3},
    "amulet": {"type": "misc", "value": 250, "stack": 1},
    "crown_of_wisdom": {"type": "misc", "value": 500, "stack": 1},
    "cursed_pendant": {"type": "misc", "value": 75, "stack": 1},
    "rope": {"type": "misc", "value": 5, "stack": 20},
    "pickaxe": {"type": "weapon", "damage": 7, "value": 30, "stack": 1},
    "holy_water": {"type": "consumable", "heal": 80, "value": 150, "stack": 5},
}

ITEM_DESCRIPTIONS = {
    "sword": "A basic steel sword. Reliable and well-balanced.",
    "shield": "A wooden shield that provides moderate protection.",
    "potion": "Restores a small amount of health when consumed.",
    "gold": "Common currency used for trading.",
    "dagger": "A light blade. Faster but less damaging than a sword.",
    "bow": "A short bow for ranged attacks.",
    "chest_armor": "Light chest armor that increases defense.",
    "torch": "Provides light in dark areas.",
    "elixir": "A rare restorative potion that heals a large amount of HP.",
    "magic_ring": "A mysterious ring with unknown magical properties.",
    "greatsword": "A heavy two-handed sword that deals massive damage.",
    "plate_armor": "Heavy armor offering excellent protection.",
    "gem": "A precious gemstone. Valuable to merchants.",
    "wooden_shield": "A sturdy wooden shield.",
    "iron_shield": "A solid iron shield for better defense.",
    "steel_shield": "An advanced steel shield offering superior protection.",
    "leather_armor": "Soft but flexible armor.",
    "chain_mail": "Interlocked metal rings provide good protection.",
    "bronze_armor": "Bronze plating gives strong defense.",
    "dragon_scale": "Legendary dragon scales. Extremely rare and powerful.",
    "mithril_sword": "A mystical silver blade with incredible sharpness.",
    "dragon_slayer": "A legendary blade forged to slay dragons.",
    "ancient_bow": "An ancient bow of great power and accuracy.",
    "crossbow": "A mechanized bow for powerful shots.",
    "mace": "A heavy club ideal for crushing enemies.",
    "battle_axe": "A large axe built for warfare.",
    "spear": "A long polearm good for both melee and range.",
    "healing_potion": "A quality potion that restores moderate HP.",
    "minor_elixir": "A weak magical elixir.",
    "legendary_elixir": "An extremely rare potion of legendary power.",
    "ruby": "A precious red gemstone.",
    "sapphire": "A precious blue gemstone.",
    "diamond": "The rarest and most valuable gemstone.",
    "scroll_of_power": "An ancient magical scroll.",
    "amulet": "A mystical amulet of protection.",
    "crown_of_wisdom": "A regal crown said to grant wisdom.",
    "cursed_pendant": "A pendant with a dark curse.",
    "rope": "Useful rope for various purposes.",
    "pickaxe": "A tool for mining or as a weapon.",
    "holy_water": "Blessed water with healing properties.",
}

# ─────────────────────────────────────────────
#  MAP PRESETS (disabled) — levels are generated procedurally now
#  Keep as an empty list in case code references length elsewhere.
MAP_PRESETS = []

MONSTER_SPAWNS = [
    [{"type": "goblin",   "pos": (3, 3)},
     {"type": "goblin",   "pos": (11, 7)},
     {"type": "skeleton", "pos": (7,  5)}],
    [{"type": "goblin",   "pos": (2,  2)},
     {"type": "goblin",   "pos": (12, 8)},
     {"type": "skeleton", "pos": (5,  5)},
     {"type": "skeleton", "pos": (9,  3)}],
    [{"type": "skeleton", "pos": (3,  2)},
     {"type": "skeleton", "pos": (11, 8)},
     {"type": "goblin",   "pos": (4,  8)},
     {"type": "goblin",   "pos": (10, 2)},
     {"type": "skeleton", "pos": (7,  5)}],
    # Floor 4 spawns
    [{"type": "goblin",   "pos": (4,  4)},
     {"type": "goblin",   "pos": (10, 6)},
     {"type": "skeleton", "pos": (7,  3)}],
    # Floor 5 spawns
    [{"type": "skeleton", "pos": (6, 4)},
     {"type": "goblin",   "pos": (3, 6)},
     {"type": "goblin",   "pos": (11,6)}],
    # Floor 6 spawns
    [{"type": "skeleton", "pos": (7, 2)},
     {"type": "skeleton", "pos": (8, 6)},
     {"type": "goblin",   "pos": (4, 4)},
     {"type": "goblin",   "pos": (10,4)}],
]

CHEST_LOOT_COMMON = [
    "sword", "shield", "potion", "gold", "dagger", "bow", "chest_armor", 
    "torch", "healing_potion", "rope", "wooden_shield", "leather_armor", 
    "minor_elixir", "spear", "pickaxe"
]

CHEST_LOOT_UNCOMMON = [
    "elixir", "ancient_bow", "crossbow", "mace", "battle_axe", 
    "iron_shield", "chain_mail", "bronze_armor", "ruby", "sapphire", 
    "scroll_of_power", "holy_water"
]

CHEST_LOOT_RARE = [
    "greatsword", "plate_armor", "mithril_sword", "steel_shield", "amulet"
]

CHEST_LOOT_LEGENDARY = [
    "dragon_slayer", "dragon_scale", "crown_of_wisdom", "cursed_pendant", 
    "legendary_elixir", "diamond", "magic_ring", "gem"
]

# Legacy CHEST_LOOT kept for compatibility
CHEST_LOOT = [CHEST_LOOT_COMMON + CHEST_LOOT_UNCOMMON + CHEST_LOOT_RARE + CHEST_LOOT_LEGENDARY]


def generate_map(floor_idx, cols=None, rows=None):
    """Procedurally generate a connected map for higher floors.
    Ensures rooms are connected by corridors so nothing is fully enclosed by walls.
    Uses global COLS/ROWS if not provided, so it scales with those constants.
    Uses GEN_BASE_ROOMS, GEN_ROOMS_PER_FLOOR, GEN_MAX_ROOMS, GEN_CORRIDOR_MIN/MAX,
    GEN_CHEST_MIN/MAX, and GEN_MONSTER_MIN/MAX constants to control generation.
    """
    if cols is None:
        cols = COLS
    if rows is None:
        rows = ROWS
    grid = [["1"] * cols for _ in range(rows)]

    rooms = []
    # Calculate room count using GEN_BASE_ROOMS and GEN_ROOMS_PER_FLOOR
    room_count = GEN_BASE_ROOMS + (floor_idx // GEN_ROOMS_PER_FLOOR)
    room_count = min(room_count, GEN_MAX_ROOMS)

    for i in range(room_count):
        rw = random.randint(3, 6)
        rh = random.randint(2, 4)
        x = random.randint(1, cols - rw - 1)
        y = random.randint(1, rows - rh - 1)
        rooms.append((x, y, rw, rh))
        for yy in range(y, y + rh):
            for xx in range(x, x + rw):
                grid[yy][xx] = "0"
        if i > 0:
            px, py, prw, prh = rooms[i - 1]
            cx = x + rw // 2
            cy = y + rh // 2
            pcx = px + prw // 2
            pcy = py + prh // 2
            # horizontal corridor from pcx->cx at pcy
            for xx in range(min(pcx, cx), max(pcx, cx) + 1):
                grid[pcy][xx] = "0"
            # vertical corridor from pcy->cy at cx
            for yy in range(min(pcy, cy), max(pcy, cy) + 1):
                grid[yy][cx] = "0"

    # Place stairs in last room center
    scx = rooms[-1][0] + rooms[-1][2] // 2
    scy = rooms[-1][1] + rooms[-1][3] // 2
    grid[scy][scx] = "S"

    # Place chests using GEN_CHEST_MIN and GEN_CHEST_MAX
    chest_count = random.randint(GEN_CHEST_MIN, GEN_CHEST_MAX)
    candidates = [(c, r) for r in range(1, rows - 1) for c in range(1, cols - 1) if grid[r][c] == "0" and (c, r) != (scx, scy)]
    random.shuffle(candidates)
    for i in range(min(chest_count, len(candidates))):
        cx, cy = candidates[i]
        grid[cy][cx] = "C"

    return ["".join(row) for row in grid]

# ─────────────────────────────────────────────
#  MONSTER CLASS
# ─────────────────────────────────────────────
class Monster:
    STATS = {
        "goblin":   {"hp": 20, "max_hp": 20, "damage": 4,  "speed": 1,
                     "flee_hp": 5, "detect": 5, "color": COLORS["goblin"],
                     "xp": 10, "symbol": "G"},
        "skeleton": {"hp": 30, "max_hp": 30, "damage": 6,  "speed": 1,
                     "flee_hp": 8, "detect": 6, "color": COLORS["skeleton"],
                     "xp": 15, "symbol": "S"},
    }

    def __init__(self, mtype, col, row, floor_idx=0):
        self.type   = mtype
        self.col    = col
        self.row    = row
        base        = Monster.STATS[mtype]
        
        # Scale stats based on floor depth (10% increase per floor)
        scale_factor = 1.0 + (floor_idx * 0.1)
        
        self.hp     = int(base["hp"] * scale_factor)
        self.max_hp = int(base["max_hp"] * scale_factor)
        self.damage = int(base["damage"] * scale_factor) if base["damage"] > 0 else 0
        self.speed  = base["speed"]
        self.flee_hp= int(base["flee_hp"] * scale_factor)
        self.detect = base["detect"]
        self.color  = base["color"]
        self.xp     = int(base["xp"] * scale_factor)
        self.symbol = base["symbol"]
        self.alive  = True
        self.canvas_id   = None
        self.hp_bar_id   = None
        self.hp_bar_bg   = None

    def dist_to(self, pc, pr):
        return math.sqrt((self.col - pc) ** 2 + (self.row - pr) ** 2)

    def decide(self, pc, pr, tilemap, monsters):
        """Return (dcol, drow) for this monster's move, or (0,0) to attack."""
        if not self.alive:
            return 0, 0
        d = self.dist_to(pc, pr)

        if d > self.detect:      # too far – idle
            return 0, 0

        if self.hp <= self.flee_hp:   # flee away from player
            dcol = self.col - pc
            drow = self.row - pr
        elif d <= 1.5:                # adjacent – attack (signal with None)
            return None, None
        else:                         # chase player
            dcol = pc - self.col
            drow = pr - self.row

        # Normalise direction to (-1,0,1)
        sc = (1 if dcol > 0 else -1) if dcol != 0 else 0
        sr = (1 if drow > 0 else -1) if drow != 0 else 0

        # Try preferred, then axis alternatives
        for dc, dr in [(sc, sr), (sc, 0), (0, sr), (-sc, 0), (0, -sr)]:
            nc, nr = self.col + dc, self.row + dr
            if self._walkable(nc, nr, tilemap, monsters):
                return dc, dr
        return 0, 0

    def _walkable(self, nc, nr, tilemap, monsters):
        if nr < 0 or nr >= len(tilemap) or nc < 0 or nc >= len(tilemap[0]):
            return False
        if tilemap[nr][nc] == "1":
            return False
        for m in monsters:
            if m is not self and m.alive and m.col == nc and m.row == nr:
                return False
        return True


# ─────────────────────────────────────────────
#  GAME WINDOW
# ─────────────────────────────────────────────
class GameWindow(tk.Toplevel):
    GRID_INV_COLS = 9
    GRID_INV_ROWS = 3
    HOT_COLS      = 9
    INV_SLOT_SIZE = 44
    HOT_SLOT_SIZE = 44

    def __init__(self, master, settings):
        super().__init__(master)
        self.settings = settings
        self.title("Dungeon Crawler")
        self.configure(bg=COLORS["bg"])
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # ── player data ──
        self.player = {
            "position":     {"col": 1, "row": 1},
            "player_stats": {
                "hp":       80,
                "max_hp":   80,
                "damage":   6,
                "defense":  0,
                "xp":       0,
                "level":    1,
            },
            "inventory": {
                "inventory": {},   # {item_name: (col, row)}
                "hotbar":    {},   # {item_name: col_index}
            },
            "item_stats":   {},    # {item_name: {…stats copy…}}
            "equipped":     {"weapon": None, "armor": None, "shield": None},
            "turn":         0,
            "floor":        1,
        }

        self.floor_idx   = 0
        self.tilemap     = []
        self.monsters    = []
        self.chests      = []   # list of (col, row, opened)
        self.stair_pos   = None
        self.selected_slot = 0
        self.inv_open    = False
        self.log         = []
        self.game_over   = False
        self.images      = {}   # loaded PhotoImage cache
        self.monster_img_cache = {}
        
        # Initialize UI dimensions (will be recalculated on resize)
        self.inv_slot_size = 44
        self.hot_slot_size = 44
        self.canvas_width = COLS * TILE
        self.canvas_height = ROWS * TILE

        self._build_ui()
        self._load_images()
        self._load_floor()
        self._draw_map()
        self._draw_player()
        self._draw_monsters()
        self._update_ui()
        
        # Bind resize event for responsive UI
        self.bind("<Configure>", self._on_window_resize)

        self.bind("<KeyPress>", self._on_key)
        self.focus_set()

    def _on_window_resize(self, event):
        """Handle window resize/fullscreen and scale UI accordingly."""
        if event.widget is not self:
            return
        
        # Calculate available space
        available_width = max(300, self.winfo_width() - 50)
        available_height = max(200, self.winfo_height() - 50)
        
        # Scale inventory slots based on available width (right panel shrinks if needed)
        right_panel_max_width = int(available_width * 0.25)
        self.inv_slot_size = max(30, min(50, right_panel_max_width // 9))
        self.hot_slot_size = self.inv_slot_size
        
        # Scale canvas to fit remaining space
        self.canvas_width = max(300, available_width - right_panel_max_width - 30)
        self.canvas_height = max(200, available_height - 100)
        
        # Update canvas size
        if hasattr(self, 'canvas'):
            self.canvas.configure(width=self.canvas_width, height=self.canvas_height)
            self._draw_map()
            self._draw_player()
            self._draw_monsters()

    def _on_window_resize_inventory(self):
        """Rebuild inventory slots with new size."""
        if not hasattr(self, 'inv_slots'):
            return
        
        # Clear and rebuild inventory slots
        for slot in self.inv_slots.values():
            slot.destroy()
        self.inv_slots.clear()
        
        for r in range(self.GRID_INV_ROWS):
            for c in range(self.GRID_INV_COLS):
                slot = tk.Canvas(self.inv_frame,
                                 width=self.inv_slot_size,
                                 height=self.inv_slot_size,
                                 bg=COLORS["slot_bg"],
                                 highlightthickness=1,
                                 highlightbackground=COLORS["slot_border"])
                slot.grid(row=r, column=c, padx=1, pady=1)
                slot.bind("<Button-1>",
                          lambda e, cc=c, rr=r: self._on_inv_click(cc, rr))
                self.inv_slots[(c, r)] = slot
        
        self._draw_inventory()

    def _on_window_resize_hotbar(self):
        """Rebuild hotbar slots with new size."""
        if not hasattr(self, 'hot_slots'):
            return
        
        # Clear and rebuild hotbar slots
        for slot in self.hot_slots.values():
            slot.destroy()
        self.hot_slots.clear()
        
        for c in range(self.HOT_COLS):
            num = tk.Label(self.hot_frame, text=str(c + 1),
                           bg=COLORS["panel"], fg=COLORS["dim"],
                           font=("Consolas", 7))
            num.grid(row=0, column=c)
            slot = tk.Canvas(self.hot_frame,
                             width=self.hot_slot_size,
                             height=self.hot_slot_size,
                             bg=COLORS["slot_bg"],
                             highlightthickness=1,
                             highlightbackground=COLORS["slot_border"])
            slot.grid(row=1, column=c, padx=1, pady=1)
            slot.bind("<Button-1>",
                      lambda e, cc=c: self._on_hot_click(cc))
            self.hot_slots[c] = slot
        
        self._draw_hotbar()

    def _build_ui(self):
        # Left: game canvas
        canvas_w = self.canvas_width
        canvas_h = self.canvas_height

        self.left_frame = tk.Frame(self, bg=COLORS["bg"])
        self.left_frame.grid(row=0, column=0, padx=8, pady=8, sticky="nsew")

        self.canvas = tk.Canvas(self.left_frame,
                                width=canvas_w, height=canvas_h,
                                bg=COLORS["wall"], highlightthickness=2,
                                highlightbackground=COLORS["border"])
        self.canvas.pack(fill="both", expand=True)

        # Log
        self.log_frame = tk.Frame(self.left_frame, bg=COLORS["panel"],
                                  height=80)
        self.log_frame.pack(fill="x", pady=(4, 0))
        self.log_frame.pack_propagate(False)
        self.log_text = tk.Text(self.log_frame, bg=COLORS["panel"],
                                fg=COLORS["dim"], font=("Consolas", 9),
                                relief="flat", state="disabled",
                                wrap="word", height=4)
        self.log_text.pack(fill="both", expand=True, padx=4, pady=2)

        # Right: stats + inventory
        self.right_frame = tk.Frame(self, bg=COLORS["bg"])
        self.right_frame.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="nsew")

        self._build_stats_panel()
        self._build_inventory_panel()
        self._build_hotbar_panel()

        # Configure grid weights for responsiveness
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def _build_stats_panel(self):
        f = tk.Frame(self.right_frame, bg=COLORS["panel"],
                     relief="flat", bd=0)
        f.pack(fill="x", pady=(0, 6))

        tk.Label(f, text="⚔ DUNGEON CRAWLER", bg=COLORS["panel"],
                 fg=COLORS["accent"], font=("Consolas", 11, "bold")).pack(pady=(6, 2))

        # HP bar
        hp_row = tk.Frame(f, bg=COLORS["panel"])
        hp_row.pack(fill="x", padx=8, pady=2)
        tk.Label(hp_row, text="HP", bg=COLORS["panel"],
                 fg=COLORS["text"], font=("Consolas", 9, "bold"), width=4).pack(side="left")
        self.hp_canvas = tk.Canvas(hp_row, height=14, bg=COLORS["border"],
                                   highlightthickness=0)
        self.hp_canvas.pack(side="left", fill="x", expand=True)

        # XP bar
        xp_row = tk.Frame(f, bg=COLORS["panel"])
        xp_row.pack(fill="x", padx=8, pady=2)
        tk.Label(xp_row, text="XP", bg=COLORS["panel"],
                 fg=COLORS["text"], font=("Consolas", 9, "bold"), width=4).pack(side="left")
        self.xp_canvas = tk.Canvas(xp_row, height=8, bg=COLORS["border"],
                                   highlightthickness=0)
        self.xp_canvas.pack(side="left", fill="x", expand=True)

        # Text stats
        stats_row = tk.Frame(f, bg=COLORS["panel"])
        stats_row.pack(fill="x", padx=8, pady=(4, 6))
        self.lbl_hp    = tk.Label(stats_row, bg=COLORS["panel"], fg=COLORS["hp_full"],
                                  font=("Consolas", 9))
        self.lbl_hp.grid(row=0, column=0, sticky="w")
        self.lbl_atk   = tk.Label(stats_row, bg=COLORS["panel"], fg=COLORS["text"],
                                   font=("Consolas", 9))
        self.lbl_atk.grid(row=0, column=1, sticky="w", padx=8)
        self.lbl_def   = tk.Label(stats_row, bg=COLORS["panel"], fg=COLORS["text"],
                                   font=("Consolas", 9))
        self.lbl_def.grid(row=1, column=0, sticky="w")
        self.lbl_turn  = tk.Label(stats_row, bg=COLORS["panel"], fg=COLORS["dim"],
                                   font=("Consolas", 9))
        self.lbl_turn.grid(row=1, column=1, sticky="w", padx=8)
        self.lbl_floor = tk.Label(stats_row, bg=COLORS["panel"], fg=COLORS["accent"],
                                   font=("Consolas", 9))
        self.lbl_floor.grid(row=2, column=0, sticky="w")
        self.lbl_lvl   = tk.Label(stats_row, bg=COLORS["panel"], fg=COLORS["accent2"],
                                   font=("Consolas", 9))
        self.lbl_lvl.grid(row=2, column=1, sticky="w", padx=8)

    def _build_inventory_panel(self):
        tk.Label(self.right_frame, text="INVENTORY  (I)", bg=COLORS["bg"],
                 fg=COLORS["dim"], font=("Consolas", 8)).pack(anchor="w")

        self.inv_frame = tk.Frame(self.right_frame, bg=COLORS["panel"],
                                  relief="flat", bd=0)
        self.inv_frame.pack()

        self.inv_slots = {}   # (col, row) -> canvas
        for r in range(self.GRID_INV_ROWS):
            for c in range(self.GRID_INV_COLS):
                slot = tk.Canvas(self.inv_frame,
                                 width=self.inv_slot_size,
                                 height=self.inv_slot_size,
                                 bg=COLORS["slot_bg"],
                                 highlightthickness=1,
                                 highlightbackground=COLORS["slot_border"])
                slot.grid(row=r, column=c, padx=1, pady=1)
                slot.bind("<Button-1>",
                          lambda e, cc=c, rr=r: self._on_inv_click(cc, rr))
                self.inv_slots[(c, r)] = slot

    def _build_hotbar_panel(self):
        tk.Label(self.right_frame, text="HOTBAR  (1-9)", bg=COLORS["bg"],
                 fg=COLORS["dim"], font=("Consolas", 8)).pack(anchor="w", pady=(6, 0))

        self.hot_frame = tk.Frame(self.right_frame, bg=COLORS["panel"])
        self.hot_frame.pack()

        self.hot_slots = {}
        for c in range(self.HOT_COLS):
            num = tk.Label(self.hot_frame, text=str(c + 1),
                           bg=COLORS["panel"], fg=COLORS["dim"],
                           font=("Consolas", 7))
            num.grid(row=0, column=c)
            slot = tk.Canvas(self.hot_frame,
                             width=self.hot_slot_size,
                             height=self.hot_slot_size,
                             bg=COLORS["slot_bg"],
                             highlightthickness=1,
                             highlightbackground=COLORS["slot_border"])
            slot.grid(row=1, column=c, padx=1, pady=1)
            slot.bind("<Button-1>",
                      lambda e, cc=c: self._on_hot_click(cc))
            self.hot_slots[c] = slot

        # Equipped display
        eq_frame = tk.Frame(self.right_frame, bg=COLORS["panel"])
        eq_frame.pack(fill="x", pady=(6, 0))
        tk.Label(eq_frame, text="Equipped:", bg=COLORS["panel"],
                 fg=COLORS["dim"], font=("Consolas", 8)).pack(side="left", padx=4)
        self.lbl_eq = tk.Label(eq_frame, text="—", bg=COLORS["panel"],
                               fg=COLORS["accent"], font=("Consolas", 9))
        self.lbl_eq.pack(side="left")

    # ── IMAGE LOADING ─────────────────────────
    def _load_images(self):
        names = ["player", "goblin", "skeleton", "floor", "wall",
                 "stairs", "chest", "sword", "shield", "potion",
                 "gold", "dagger", "bow", "chest_armor", "torch"]
        for n in names:
            try:
                img = tk.PhotoImage(file=f"{n}.png")
                # Scale to fit tile
                img = img.subsample(max(1, img.width() // TILE),
                                    max(1, img.height() // TILE))
                self.images[n] = img
            except Exception:
                self.images[n] = None  # fallback to colored rectangles

    def _get_item_image(self, item_name):
        return self.images.get(item_name)

    # ── FLOOR LOADING ─────────────────────────
    def _load_floor(self):
        # Always generate the map procedurally
        raw = generate_map(self.floor_idx)
        self.tilemap = [list(row) for row in raw]
        self.monsters = []
        self.chests   = []
        self.stair_pos = None

        # Scan for stairs / chests
        for r, row in enumerate(self.tilemap):
            for c, ch in enumerate(row):
                if ch == "S":
                    self.stair_pos = (c, r)
                    self.tilemap[r][c] = "0"
                elif ch == "C":
                    self.chests.append([c, r, False])
                    self.tilemap[r][c] = "0"

        # Spawn monsters procedurally using GEN_MONSTER_MIN/MAX
        spawns = []
        floor_tiles = [(c, r) for r, row in enumerate(self.tilemap)
                        for c, ch in enumerate(row) if ch == "0"]
        random.shuffle(floor_tiles)
        monster_count = random.randint(GEN_MONSTER_MIN, GEN_MONSTER_MAX)
        for i in range(monster_count):
            if not floor_tiles:
                break
            mc, mr = floor_tiles.pop()
            # Skeleton probability increases with floor depth
            skeleton_chance = min(0.85, 0.2 + 0.03 * self.floor_idx)
            mtype = "skeleton" if random.random() < skeleton_chance else "goblin"
            spawns.append({"type": mtype, "pos": (mc, mr)})

        for s in spawns:
            mc, mr = s["pos"]
            if 0 <= mr < len(self.tilemap) and 0 <= mc < len(self.tilemap[0]) and self.tilemap[mr][mc] != "1":
                self.monsters.append(Monster(s["type"], mc, mr, self.floor_idx))

        # Place player at first open tile, avoiding existing monsters and chests
        placed = False
        for r in range(1, len(self.tilemap)):
            for c in range(1, len(self.tilemap[0])):
                if self.tilemap[r][c] != "0":
                    continue
                # Check if a monster is here
                if any(m.col == c and m.row == r for m in self.monsters):
                    continue
                # Check if a chest is here
                if any(ch[0] == c and ch[1] == r for ch in self.chests):
                    continue
                # Valid spawn location
                self.player["position"] = {"col": c, "row": r}
                placed = True
                break
            if placed:
                break

        if not placed:
            # Fallback: find any open floor tile
            for r in range(1, len(self.tilemap)):
                for c in range(1, len(self.tilemap[0])):
                    if self.tilemap[r][c] == "0":
                        self.player["position"] = {"col": c, "row": r}
                        placed = True
                        break
                if placed:
                    break

        self._add_log(f"Entered floor {self.player['floor']}.")

    # ── DRAWING ───────────────────────────────
    def _draw_map(self):
        self.canvas.delete("map")
        for r, row in enumerate(self.tilemap):
            for c, ch in enumerate(row):
                x0, y0 = c * TILE, r * TILE
                if ch == "1":
                    if self.images.get("wall"):
                        self.canvas.create_image(x0, y0, anchor="nw",
                                                  image=self.images["wall"], tags="map")
                    else:
                        self.canvas.create_rectangle(x0, y0, x0+TILE, y0+TILE,
                                                     fill=COLORS["wall"],
                                                     outline=COLORS["border"],
                                                     tags="map")
                else:
                    if self.images.get("floor"):
                        self.canvas.create_image(x0, y0, anchor="nw",
                                                  image=self.images["floor"], tags="map")
                    else:
                        self.canvas.create_rectangle(x0, y0, x0+TILE, y0+TILE,
                                                     fill=COLORS["floor"],
                                                     outline="#1a1a2a",
                                                     tags="map")

        # Draw stairs
        if self.stair_pos:
            sc, sr = self.stair_pos
            x0, y0 = sc * TILE, sr * TILE
            if self.images.get("stairs"):
                self.canvas.create_image(x0, y0, anchor="nw",
                                          image=self.images["stairs"], tags="map")
            else:
                self.canvas.create_rectangle(x0+4, y0+4, x0+TILE-4, y0+TILE-4,
                                             fill=COLORS["stairs"], outline="",
                                             tags="map")
                self.canvas.create_text(x0+TILE//2, y0+TILE//2, text="▼",
                                        fill=COLORS["bg"], font=("Consolas", 14, "bold"),
                                        tags="map")

        # Draw chests
        for ch in self.chests:
            cc, cr, opened = ch
            x0, y0 = cc * TILE, cr * TILE
            color = COLORS["dim"] if opened else COLORS["chest"]
            if self.images.get("chest"):
                self.canvas.create_image(x0, y0, anchor="nw",
                                          image=self.images["chest"], tags="map")
            else:
                self.canvas.create_rectangle(x0+4, y0+4, x0+TILE-4, y0+TILE-4,
                                             fill=color, outline=COLORS["accent"],
                                             tags="map")
                self.canvas.create_text(x0+TILE//2, y0+TILE//2, text="📦",
                                        fill=COLORS["bg"], font=("Consolas", 12),
                                        tags="map")

    def _draw_player(self):
        self.canvas.delete("player")
        pc = self.player["position"]["col"]
        pr = self.player["position"]["row"]
        x0, y0 = pc * TILE, pr * TILE
        if self.images.get("player"):
            self.canvas.create_image(x0, y0, anchor="nw",
                                      image=self.images["player"], tags="player")
        else:
            self.canvas.create_oval(x0+4, y0+4, x0+TILE-4, y0+TILE-4,
                                    fill=COLORS["player"], outline=COLORS["accent"],
                                    width=2, tags="player")
            self.canvas.create_text(x0+TILE//2, y0+TILE//2, text="@",
                                    fill=COLORS["bg"], font=("Consolas", 16, "bold"),
                                    tags="player")

    def _draw_monsters(self):
        self.canvas.delete("monster")
        for m in self.monsters:
            if not m.alive:
                continue
            x0, y0 = m.col * TILE, m.row * TILE
            img = self.images.get(m.type)
            if img:
                self.canvas.create_image(x0, y0, anchor="nw",
                                          image=img, tags="monster")
            else:
                self.canvas.create_oval(x0+4, y0+4, x0+TILE-4, y0+TILE-4,
                                        fill=m.color, outline="#ffffff",
                                        tags="monster")
                self.canvas.create_text(x0+TILE//2, y0+TILE//2, text=m.symbol,
                                        fill="#ffffff", font=("Consolas", 14, "bold"),
                                        tags="monster")
            # HP bar above monster
            hp_pct = m.hp / m.max_hp
            bar_w  = TILE - 8
            self.canvas.create_rectangle(x0+4, y0+2, x0+4+bar_w, y0+6,
                                         fill=COLORS["border"], outline="",
                                         tags="monster")
            col = COLORS["hp_full"] if hp_pct > 0.4 else COLORS["hp_low"]
            self.canvas.create_rectangle(x0+4, y0+2,
                                         x0+4+int(bar_w*hp_pct), y0+6,
                                         fill=col, outline="",
                                         tags="monster")

    def _update_ui(self):
        ps   = self.player["player_stats"]
        hp_pct = ps["hp"] / ps["max_hp"]

        # HP bar
        self.hp_canvas.update_idletasks()
        w = self.hp_canvas.winfo_width() or 150
        self.hp_canvas.delete("all")
        col = COLORS["hp_full"] if hp_pct > 0.35 else COLORS["hp_low"]
        self.hp_canvas.create_rectangle(0, 0, int(w * hp_pct), 14,
                                        fill=col, outline="")

        # XP bar (100 xp per level)
        xp_need = ps["level"] * 100
        xp_pct  = min(1.0, ps["xp"] / xp_need)
        self.xp_canvas.update_idletasks()
        w2 = self.xp_canvas.winfo_width() or 150
        self.xp_canvas.delete("all")
        self.xp_canvas.create_rectangle(0, 0, int(w2 * xp_pct), 8,
                                        fill=COLORS["accent2"], outline="")

        self.lbl_hp["text"]    = f"HP: {ps['hp']}/{ps['max_hp']}"
        self.lbl_atk["text"]   = f"ATK: {ps['damage']}"
        self.lbl_def["text"]   = f"DEF: {ps['defense']}"
        self.lbl_turn["text"]  = f"Turn: {self.player['turn']}"
        self.lbl_floor["text"] = f"Floor: {self.player['floor']}"
        self.lbl_lvl["text"]   = f"Lv.{ps['level']} ({ps['xp']}/{xp_need}xp)"

        eq_w = self.player["equipped"]["weapon"]
        eq_a = self.player["equipped"]["armor"]
        eq_s = self.player["equipped"]["shield"]
        eq_txt = (f"W:{eq_w or '—'} | A:{eq_a or '—'} | S:{eq_s or '—'}")
        self.lbl_eq["text"] = eq_txt

        self._draw_hotbar()
        self._draw_inventory()

    def _draw_hotbar(self):
        inv   = self.player["inventory"]["hotbar"]
        # Build reverse map: col -> item_name
        slot_map = {v: k for k, v in inv.items()}

        for c in range(self.HOT_COLS):
            slot = self.hot_slots[c]
            slot.delete("all")
            bg = COLORS["slot_sel"] if c == self.selected_slot else COLORS["slot_bg"]
            slot.configure(bg=bg)
            border = COLORS["accent"] if c == self.selected_slot else COLORS["slot_border"]
            slot.configure(highlightbackground=border)

            item = slot_map.get(c)
            if item:
                img = self._get_item_image(item.split(":")[0])
                if img:
                    slot.create_image(self.hot_slot_size//2, self.hot_slot_size//2,
                                      image=img)
                else:
                    slot.create_rectangle(4, 4, self.hot_slot_size-4,
                                          self.hot_slot_size-4,
                                          fill=COLORS["accent2"], outline="")
                    slot.create_text(self.hot_slot_size//2, self.hot_slot_size//2,
                                     text=item.split(":")[0][:3].upper(),
                                     fill=COLORS["text"], font=("Consolas", 7))

    def _draw_inventory(self):
        inv = self.player["inventory"]["inventory"]
        
        # Group items by base name and count stackable items
        item_groups = {}  # {base_name: [(key, slot_pos), ...]}
        for key, slot_pos in inv.items():
            base_name = key.split(":")[0]
            if base_name not in item_groups:
                item_groups[base_name] = []
            item_groups[base_name].append((key, slot_pos))
        
        # Build display map: only show first of each item type with count
        display_map = {}  # {(c, r): (item_name, count, first_key)}
        for base_name, items in item_groups.items():
            # Use first item's slot position
            first_key, first_slot = items[0]
            count = len(items)
            display_map[first_slot] = (base_name, count, first_key)
        
        slot_map = {v: k for k, v in inv.items()}

        for (c, r), slot in self.inv_slots.items():
            slot.delete("all")
            
            if (c, r) in display_map:
                base_name, count, first_key = display_map[(c, r)]
                img = self._get_item_image(base_name)
                if img:
                    slot.create_image(self.inv_slot_size//2, self.inv_slot_size//2,
                                      image=img)
                else:
                    slot.create_rectangle(4, 4, self.inv_slot_size-4,
                                          self.inv_slot_size-4,
                                          fill=COLORS["accent2"], outline="")
                    slot.create_text(self.inv_slot_size//2, self.inv_slot_size//2,
                                     text=base_name[:3].upper(),
                                     fill=COLORS["text"], font=("Consolas", 7))
                
                # Show count if more than 1
                if count > 1:
                    slot.create_rectangle(self.inv_slot_size-12, self.inv_slot_size-12,
                                         self.inv_slot_size-2, self.inv_slot_size-2,
                                         fill=COLORS["accent"], outline="")
                    slot.create_text(self.inv_slot_size-7, self.inv_slot_size-7,
                                    text=str(count), fill=COLORS["bg"],
                                    font=("Consolas", 6, "bold"))

    # ── INPUT ─────────────────────────────────
    def _on_key(self, event):
        if self.game_over:
            return
        k = event.keysym.lower()

        # Movement
        dirs = {
            "up": (0, -1), "w": (0, -1),
            "down": (0, 1), "s": (0, 1),
            "left": (-1, 0), "a": (-1, 0),
            "right": (1, 0), "d": (1, 0),
        }
        if k in dirs:
            dc, dr = dirs[k]
            self._try_move(dc, dr)
            return

        # Hotbar selection
        if k in "123456789":
            self.selected_slot = int(k) - 1
            self._update_ui()
            return

        # Inventory toggle
        if k == "i":
            self.inv_open = not self.inv_open
            return

        # Interact
        if k == "space":
            self._interact()
            return

        # Use hotbar item
        if k == "u" or k == "return":
            self._use_hotbar_item()
            return

    def _try_move(self, dc, dr):
        pc = self.player["position"]["col"]
        pr = self.player["position"]["row"]
        nc, nr = pc + dc, pr + dr

        # Check bounds & walls
        if nr < 0 or nr >= ROWS or nc < 0 or nc >= COLS:
            return
        if self.tilemap[nr][nc] == "1":
            return

        # Check monster collision → attack
        for m in self.monsters:
            if m.alive and m.col == nc and m.row == nr:
                self._player_attack(m)
                self._end_turn()
                return

        # Move
        self.player["position"]["col"] = nc
        self.player["position"]["row"] = nr
        self._end_turn()

    def _interact(self):
        pc = self.player["position"]["col"]
        pr = self.player["position"]["row"]

        # Check stairs
        if self.stair_pos and (pc, pr) == self.stair_pos:
            self._descend()
            return

        # Check adjacent chests
        for ch in self.chests:
            cc, cr, opened = ch
            if not opened and abs(pc - cc) <= 1 and abs(pr - cr) <= 1:
                self._open_chest(ch)
                self._end_turn()
                return

    def _descend(self):
        # Prevent descending beyond max floor
        if self.player.get("floor", 1) >= MAX_FLOORS:
            self._add_log("You cannot descend further.")
            return
        self.player["floor"] += 1
        self.floor_idx += 1
        self.canvas.delete("all")
        self._load_floor()
        self._draw_map()
        self._draw_player()
        self._draw_monsters()
        self._update_ui()

    def _open_chest(self, ch):
        ch[2] = True  # mark opened
        # Calculate floor progress as percentage of max floors
        floor_progress = (self.floor_idx / MAX_FLOORS) * 100
        
        # Build available loot pool based on progress
        available_loot = list(CHEST_LOOT_COMMON)
        
        if floor_progress >= 25:
            available_loot += CHEST_LOOT_UNCOMMON
        if floor_progress >= 50:
            available_loot += CHEST_LOOT_RARE
        if floor_progress >= 75:
            available_loot += CHEST_LOOT_LEGENDARY
        
        # Select random item from available pool
        loot = random.choice(available_loot)
        self._add_item_to_inventory(loot)
        self._add_log(f"Opened chest: found {loot}!")
        self._draw_map()

    # ── COMBAT ────────────────────────────────
    def _player_attack(self, m):
        ps  = self.player["player_stats"]
        dmg = ps["damage"] + random.randint(-1, 2)
        m.hp -= dmg
        self._add_log(f"You hit {m.type} for {dmg} dmg. ({m.hp}/{m.max_hp} HP)")
        if m.hp <= 0:
            m.alive = False
            ps["xp"] += m.xp
            self._add_log(f"{m.type.capitalize()} defeated! +{m.xp} XP")
            self._check_level_up()

    def _monster_attack(self, m):
        ps  = self.player["player_stats"]
        dmg = max(0, m.damage - ps["defense"] + random.randint(-1, 1))
        ps["hp"] -= dmg
        self._add_log(f"{m.type.capitalize()} hits you for {dmg} dmg!")
        if ps["hp"] <= 0:
            ps["hp"] = 0
            self._game_over()

    def _check_level_up(self):
        ps      = self.player["player_stats"]
        needed  = ps["level"] * 100
        if ps["xp"] >= needed:
            ps["xp"]    -= needed
            ps["level"] += 1
            ps["max_hp"] += 10
            ps["hp"]     = min(ps["hp"] + 10, ps["max_hp"])
            ps["damage"] += 1
            self._add_log(f"⬆ Level up! Now Lv.{ps['level']}!")

    # ── TURN END ──────────────────────────────
    def _end_turn(self):
        self.player["turn"] += 1
        pc = self.player["position"]["col"]
        pr = self.player["position"]["row"]

        for m in self.monsters:
            if not m.alive:
                continue
            dc, dr = m.decide(pc, pr, self.tilemap, self.monsters)
            if dc is None:  # attack
                self._monster_attack(m)
            elif dc != 0 or dr != 0:
                m.col += dc
                m.row += dr

        self._draw_map()
        self._draw_player()
        self._draw_monsters()
        self._update_ui()

    # ── INVENTORY ─────────────────────────────
    def _add_item_to_inventory(self, item_name):
        """Find first empty inv slot and place item."""
        inv  = self.player["inventory"]["inventory"]
        used = set(inv.values())

        for r in range(self.GRID_INV_ROWS):
            for c in range(self.GRID_INV_COLS):
                if (c, r) not in used:
                    key = f"{item_name}:{id(item_name)}{random.randint(0,9999)}"
                    inv[key] = (c, r)
                    # Store stats copy
                    if item_name in ITEM_STATS:
                        self.player["item_stats"][key] = dict(ITEM_STATS[item_name])
                    self._update_ui()
                    return True
        self._add_log("Inventory full!")
        return False

    def _on_inv_click(self, c, r):
        inv = self.player["inventory"]["inventory"]
        for k, pos in list(inv.items()):
            if pos == (c, r):
                self._show_item_popup(k, "inventory")
                return

    def _on_hot_click(self, c):
        hot = self.player["inventory"]["hotbar"]
        for k, pos in list(hot.items()):
            if pos == c:
                self._show_item_popup(k, "hotbar")
                return

    def _show_item_popup(self, key, source):
        """Show a modal popup with item description and an option to use/equip/discard."""
        name = key.split(":")[0]
        stats = self.player["item_stats"].get(key, ITEM_STATS.get(name, {}))
        itype = stats.get("type", "")
        desc = ITEM_DESCRIPTIONS.get(name, "No description available.")

        win = tk.Toplevel(self)
        win.title(name.capitalize())
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)

        tk.Label(win, text=name.capitalize(), font=("Consolas", 11, "bold")).pack(padx=12, pady=(8, 4))
        tk.Label(win, text=desc, wraplength=320, justify="left").pack(padx=12)

        # Stats summary
        stat_lines = []
        if itype == "weapon":
            stat_lines.append(f"Damage: {stats.get('damage', '?')}")
        if itype == "armor":
            stat_lines.append(f"Defense: {stats.get('defense', '?')}")
        if itype == "shield":
            stat_lines.append(f"Defense: {stats.get('defense', '?')}")
        if itype == "consumable":
            if 'heal' in stats:
                stat_lines.append(f"Heals: {stats.get('heal')}")
        if 'value' in stats:
            stat_lines.append(f"Value: {stats.get('value')}")
        if stat_lines:
            tk.Label(win, text=" | ".join(stat_lines), fg=COLORS['dim'], font=("Consolas", 9)).pack(padx=12, pady=(6, 0))

        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10)

        action_text = "Equip" if itype in ("weapon", "armor", "shield") else "Use"
        def _do_action():
            self._use_item(key, source)
            try:
                win.destroy()
            except Exception:
                pass
        
        def _do_discard():
            self._discard_item(key, source)
            try:
                win.destroy()
            except Exception:
                pass

        tk.Button(btn_frame, text=action_text, width=10, command=_do_action).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Discard", width=10, command=_do_discard).pack(side="left", padx=4)
        tk.Button(btn_frame, text="Cancel", width=10, command=win.destroy).pack(side="left", padx=4)
        win.bind("<Escape>", lambda e: win.destroy())

    def _discard_item(self, key, source):
        """Remove an item from inventory or hotbar."""
        name = key.split(":")[0]
        
        if source == "inventory":
            if key in self.player["inventory"]["inventory"]:
                del self.player["inventory"]["inventory"][key]
        else:  # hotbar
            if key in self.player["inventory"]["hotbar"]:
                del self.player["inventory"]["hotbar"][key]
        
        if key in self.player["item_stats"]:
            del self.player["item_stats"][key]
        
        self._add_log(f"Discarded {name}.")
        self._update_ui()

    def _use_hotbar_item(self):
        hot = self.player["inventory"]["hotbar"]
        for k, pos in list(hot.items()):
            if pos == self.selected_slot:
                self._use_item(k, "hotbar")
                return

    def _use_item(self, key, source):
        stats = self.player["item_stats"].get(key, {})
        itype = stats.get("type", "")
        name  = key.split(":")[0]
        ps    = self.player["player_stats"]

        if itype == "consumable":
            heal = stats.get("heal", 0)
            ps["hp"] = min(ps["max_hp"], ps["hp"] + heal)
            self._add_log(f"Used {name}: healed {heal} HP.")
            # Remove item
            if source == "inventory":
                del self.player["inventory"]["inventory"][key]
            else:
                del self.player["inventory"]["hotbar"][key]
            if key in self.player["item_stats"]:
                del self.player["item_stats"][key]

        elif itype == "weapon":
            old = self.player["equipped"]["weapon"]
            self.player["equipped"]["weapon"] = name
            ps["damage"] = 6 + stats.get("damage", 0)
            self._add_log(f"Equipped {name} (ATK +{stats.get('damage',0)}).")

        elif itype == "armor":
            self.player["equipped"]["armor"] = name
            ps["defense"] = stats.get("defense", 0)
            if self.player["equipped"]["shield"]:
                shield_stats = self.player["item_stats"].get(self.player["equipped"]["shield"], {})
                ps["defense"] += shield_stats.get("defense", 0)
            self._add_log(f"Equipped {name} (DEF +{stats.get('defense',0)}).")

        elif itype == "shield":
            self.player["equipped"]["shield"] = name
            ps["defense"] = stats.get("defense", 0)
            if self.player["equipped"]["armor"]:
                armor_stats = self.player["item_stats"].get(self.player["equipped"]["armor"], {})
                ps["defense"] += armor_stats.get("defense", 0)
            self._add_log(f"Equipped {name} (DEF +{stats.get('defense',0)}).")

        else:
            # Move to hotbar if in inventory, or vice versa
            self._add_log(f"{name} – no use effect.")

        self._update_ui()

    # ── MISC ──────────────────────────────────
    def _add_log(self, msg):
        self.log.append(msg)
        if len(self.log) > 60:
            self.log.pop(0)
        self.log_text.configure(state="normal")
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _game_over(self):
        self.game_over = True
        
        # Create a modal game over window
        win = tk.Toplevel(self)
        win.title("Game Over")
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)
        win.configure(bg=COLORS["bg"])
        
        # Center the window on screen
        win.geometry("400x300+300+200")
        
        # You Died message
        tk.Label(win, text="YOU DIED", bg=COLORS["bg"],
                 fg=COLORS["hp_low"], font=("Consolas", 32, "bold")).pack(pady=(40, 10))
        
        # Stats summary
        ps = self.player["player_stats"]
        stats_text = f"""
Floor Reached: {self.player['floor']}
Level: {ps['level']}
Total XP: {ps['xp']}
"""
        tk.Label(win, text=stats_text, bg=COLORS["bg"],
                 fg=COLORS["text"], font=("Consolas", 11), justify="center").pack(pady=10)
        
        # Buttons
        btn_frame = tk.Frame(win, bg=COLORS["bg"])
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Return to Menu",
                  bg=COLORS["button"], fg=COLORS["text"],
                  font=("Consolas", 11, "bold"),
                  relief="flat", width=16,
                  activebackground=COLORS["button_h"],
                  command=lambda: self._on_close()).pack(padx=6, pady=6)
        
        win.focus_set()
        win.bind("<Return>", lambda e: self._on_close())
        win.bind("<Escape>", lambda e: self._on_close())

    def _on_close(self):
        self.master.destroy()


# ─────────────────────────────────────────────
#  SETTINGS WINDOW
# ─────────────────────────────────────────────
class SettingsWindow(tk.Toplevel):
    def __init__(self, master, settings):
        super().__init__(master)
        self.title("Settings")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)
        self.settings = settings

        tk.Label(self, text="⚙  SETTINGS", bg=COLORS["bg"],
                 fg=COLORS["accent"], font=("Consolas", 13, "bold")).pack(pady=(16, 8))

        self._row("Music Volume",   "music_vol",    0, 100, tk.IntVar(value=settings.get("music_vol", 70)))
        self._row("SFX Volume",     "sfx_vol",      0, 100, tk.IntVar(value=settings.get("sfx_vol", 80)))
        self._row("Scroll Speed",   "scroll_spd",   1, 10,  tk.IntVar(value=settings.get("scroll_spd", 5)))
        self._check("Show Grid",    "show_grid",    tk.BooleanVar(value=settings.get("show_grid", True)))
        self._check("Auto-save",    "auto_save",    tk.BooleanVar(value=settings.get("auto_save", True)))
        self._check("Show Tooltips","show_tips",    tk.BooleanVar(value=settings.get("show_tips", True)))

        tk.Button(self, text="Close", bg=COLORS["button"], fg=COLORS["text"],
                  font=("Consolas", 10), relief="flat",
                  activebackground=COLORS["button_h"],
                  command=self.destroy).pack(pady=12)

    def _row(self, label, key, lo, hi, var):
        f = tk.Frame(self, bg=COLORS["bg"])
        f.pack(fill="x", padx=24, pady=4)
        tk.Label(f, text=label, bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Consolas", 9), width=16, anchor="w").pack(side="left")
        s = ttk.Scale(f, from_=lo, to=hi, orient="horizontal",
                      variable=var, length=140)
        s.pack(side="left")
        s.bind("<ButtonRelease-1>", lambda e, k=key, v=var: self.settings.update({k: v.get()}))

    def _check(self, label, key, var):
        f = tk.Frame(self, bg=COLORS["bg"])
        f.pack(fill="x", padx=24, pady=4)
        tk.Label(f, text=label, bg=COLORS["bg"], fg=COLORS["text"],
                 font=("Consolas", 9), width=16, anchor="w").pack(side="left")
        cb = tk.Checkbutton(f, variable=var, bg=COLORS["bg"],
                            fg=COLORS["accent"], selectcolor=COLORS["panel"],
                            activebackground=COLORS["bg"],
                            command=lambda k=key, v=var: self.settings.update({k: v.get()}))
        cb.pack(side="left")


# ─────────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────────
class MainMenu(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dungeon Crawler")
        self.configure(bg=COLORS["bg"])
        self.resizable(False, False)

        self.settings = {
            "music_vol":  70,
            "sfx_vol":    80,
            "scroll_spd": 5,
            "show_grid":  True,
            "auto_save":  True,
            "show_tips":  True,
        }

        self._build()

    def _build(self):
        # Title art
        art = (
            "  ██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ███████╗ ██████╗ ███╗   ██╗\n"
            "  ██╔══██╗██║   ██║████╗  ██║██╔════╝ ██╔════╝██╔═══██╗████╗  ██║\n"
            "  ██║  ██║██║   ██║██╔██╗ ██║██║  ███╗█████╗  ██║   ██║██╔██╗ ██║\n"
            "  ██║  ██║██║   ██║██║╚██╗██║██║   ██║██╔══╝  ██║   ██║██║╚██╗██║\n"
            "  ██████╔╝╚██████╔╝██║ ╚████║╚██████╔╝███████╗╚██████╔╝██║ ╚████║\n"
            "  ╚═════╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝"
        )
        tk.Label(self, text=art, bg=COLORS["bg"], fg=COLORS["accent"],
                 font=("Consolas", 7), justify="left").pack(pady=(20, 4))

        tk.Label(self, text="C R A W L E R", bg=COLORS["bg"],
                 fg=COLORS["accent2"], font=("Consolas", 9, "bold"),
                ).pack()

        tk.Label(self, text="A Roguelike Dungeon Adventure",
                 bg=COLORS["bg"], fg=COLORS["dim"],
                 font=("Consolas", 9)).pack(pady=(0, 24))

        for label, cmd in [("▶  PLAY", self._play),
                            ("⚙  SETTINGS", self._settings),
                            ("✕  QUIT", self.destroy)]:
            b = tk.Button(self, text=label, width=20,
                          bg=COLORS["button"], fg=COLORS["text"],
                          font=("Consolas", 11, "bold"),
                          relief="flat", cursor="hand2",
                          activebackground=COLORS["button_h"],
                          activeforeground=COLORS["accent"],
                          command=cmd, pady=8)
            b.pack(pady=5)
            b.bind("<Enter>", lambda e, w=b: w.configure(bg=COLORS["button_h"]))
            b.bind("<Leave>", lambda e, w=b: w.configure(bg=COLORS["button"]))

        tk.Label(self, text="Arrow/WASD=Move  Space=Interact  1-9=Hotbar  I=Inventory  U=Use",
                 bg=COLORS["bg"], fg=COLORS["dim"],
                 font=("Consolas", 7)).pack(pady=(16, 8))

        tk.Label(self, text="v1.0  —  Place .png images in game directory",
                 bg=COLORS["bg"], fg="#333344",
                 font=("Consolas", 7)).pack(pady=(0, 8))

    def _play(self):
        # Start game in same thread (tkinter must stay on main thread)
        gw = GameWindow(self, self.settings)
        # protocol to destroy root when game window closes is set inside GameWindow
        self.withdraw()

        def _on_game_close():
            gw._on_close()
            self.deiconify()

        gw.protocol("WM_DELETE_WINDOW", _on_game_close)

    def _settings(self):
        SettingsWindow(self, self.settings)


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = MainMenu()
    app.mainloop()