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
TILE  = 48          # pixel size of one grid tile
COLS  = 15          # map width  (tiles)
ROWS  = 11          # map height (tiles)
FPS   = 30

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
    "shield":   {"type": "armor",   "defense": 4, "value": 15, "stack": 1},
    "potion":   {"type": "consumable", "heal": 25, "value": 10, "stack": 5},
    "gold":     {"type": "currency","value": 1,   "stack": 99},
    "dagger":   {"type": "weapon",  "damage": 5,  "value": 12, "stack": 1},
    "bow":      {"type": "weapon",  "damage": 6,  "value": 18, "stack": 1},
    "chest_armor": {"type": "armor","defense": 6, "value": 25, "stack": 1},
    "torch":    {"type": "misc",    "light": 3,   "value": 5,  "stack": 10},
}

# ─────────────────────────────────────────────
#  MAP PRESETS
# ─────────────────────────────────────────────
# 0 = floor, 1 = wall, S = stairs, C = chest
MAP_PRESETS = [
    # Floor 1
    [
        "111111111111111",
        "100000000000001",
        "100111011101001",
        "100100010001001",
        "100100010001001",
        "10000000000S001",
        "100100010001001",
        "100100010001001",
        "100111011101001",
        "100000000000001",
        "111111111111111",
    ],
    # Floor 2
    [
        "111111111111111",
        "100000000000001",
        "101111010111101",
        "100000010000001",
        "100000010000001",
        "100000000000S01",
        "100000010000001",
        "100000010000001",
        "101111010111101",
        "100000000000001",
        "111111111111111",
    ],
    # Floor 3
    [
        "111111111111111",
        "100000000000001",
        "100011100011001",
        "100010100010001",
        "100010100010001",
        "10001010001S001",
        "100010100010001",
        "100010100010001",
        "100011100011001",
        "100000000000001",
        "111111111111111",
    ],
]

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
]

CHEST_LOOT = [
    ["sword"],
    ["shield", "potion"],
    ["sword", "shield", "potion", "potion"],
]

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

    def __init__(self, mtype, col, row):
        self.type   = mtype
        self.col    = col
        self.row    = row
        base        = Monster.STATS[mtype]
        self.hp     = base["hp"]
        self.max_hp = base["max_hp"]
        self.damage = base["damage"]
        self.speed  = base["speed"]
        self.flee_hp= base["flee_hp"]
        self.detect = base["detect"]
        self.color  = base["color"]
        self.xp     = base["xp"]
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
        self.resizable(False, False)
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
            "equipped":     {"weapon": None, "armor": None},
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

        self._build_ui()
        self._load_images()
        self._load_floor()
        self._draw_map()
        self._draw_player()
        self._draw_monsters()
        self._update_ui()

        self.bind("<KeyPress>", self._on_key)
        self.focus_set()

    # ── UI CONSTRUCTION ──────────────────────
    def _build_ui(self):
        # Left: game canvas
        canvas_w = COLS * TILE
        canvas_h = ROWS * TILE

        self.left_frame = tk.Frame(self, bg=COLORS["bg"])
        self.left_frame.grid(row=0, column=0, padx=8, pady=8, sticky="n")

        self.canvas = tk.Canvas(self.left_frame,
                                width=canvas_w, height=canvas_h,
                                bg=COLORS["wall"], highlightthickness=2,
                                highlightbackground=COLORS["border"])
        self.canvas.pack()

        # Log
        self.log_frame = tk.Frame(self.left_frame, bg=COLORS["panel"],
                                  width=canvas_w, height=80)
        self.log_frame.pack(fill="x", pady=(4, 0))
        self.log_frame.pack_propagate(False)
        self.log_text = tk.Text(self.log_frame, bg=COLORS["panel"],
                                fg=COLORS["dim"], font=("Consolas", 9),
                                relief="flat", state="disabled",
                                wrap="word", height=4)
        self.log_text.pack(fill="both", expand=True, padx=4, pady=2)

        # Right: stats + inventory
        self.right_frame = tk.Frame(self, bg=COLORS["bg"])
        self.right_frame.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="n")

        self._build_stats_panel()
        self._build_inventory_panel()
        self._build_hotbar_panel()

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
                                 width=self.INV_SLOT_SIZE,
                                 height=self.INV_SLOT_SIZE,
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
                             width=self.HOT_SLOT_SIZE,
                             height=self.HOT_SLOT_SIZE,
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
        idx = min(self.floor_idx, len(MAP_PRESETS) - 1)
        raw = MAP_PRESETS[idx]
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

        # Spawn monsters
        spawns = MONSTER_SPAWNS[min(self.floor_idx, len(MONSTER_SPAWNS) - 1)]
        for s in spawns:
            mc, mr = s["pos"]
            if self.tilemap[mr][mc] != "1":
                self.monsters.append(Monster(s["type"], mc, mr))

        # Place player at first open tile top-left
        placed = False
        for r in range(1, ROWS):
            for c in range(1, COLS):
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
        eq_txt = (f"{eq_w or '—'} / {eq_a or '—'}")
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
                    slot.create_image(self.HOT_SLOT_SIZE//2, self.HOT_SLOT_SIZE//2,
                                      image=img)
                else:
                    slot.create_rectangle(4, 4, self.HOT_SLOT_SIZE-4,
                                          self.HOT_SLOT_SIZE-4,
                                          fill=COLORS["accent2"], outline="")
                    slot.create_text(self.HOT_SLOT_SIZE//2, self.HOT_SLOT_SIZE//2,
                                     text=item.split(":")[0][:3].upper(),
                                     fill=COLORS["text"], font=("Consolas", 7))

    def _draw_inventory(self):
        inv = self.player["inventory"]["inventory"]
        slot_map = {v: k for k, v in inv.items()}

        for (c, r), slot in self.inv_slots.items():
            slot.delete("all")
            item = slot_map.get((c, r))
            if item:
                img = self._get_item_image(item.split(":")[0])
                if img:
                    slot.create_image(self.INV_SLOT_SIZE//2, self.INV_SLOT_SIZE//2,
                                      image=img)
                else:
                    slot.create_rectangle(4, 4, self.INV_SLOT_SIZE-4,
                                          self.INV_SLOT_SIZE-4,
                                          fill=COLORS["accent2"], outline="")
                    slot.create_text(self.INV_SLOT_SIZE//2, self.INV_SLOT_SIZE//2,
                                     text=item.split(":")[0][:3].upper(),
                                     fill=COLORS["text"], font=("Consolas", 7))

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
        self.player["floor"] += 1
        self.floor_idx = min(self.floor_idx + 1, len(MAP_PRESETS) - 1)
        self.canvas.delete("all")
        self._load_floor()
        self._draw_map()
        self._draw_player()
        self._draw_monsters()
        self._update_ui()

    def _open_chest(self, ch):
        ch[2] = True  # mark opened
        idx   = min(self.floor_idx, len(CHEST_LOOT) - 1)
        loot  = random.choice(CHEST_LOOT[idx])
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
                self._use_item(k, "inventory")
                return

    def _on_hot_click(self, c):
        hot = self.player["inventory"]["hotbar"]
        for k, pos in list(hot.items()):
            if pos == c:
                self._use_item(k, "hotbar")
                return

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
        self.canvas.create_rectangle(0, 0, COLS*TILE, ROWS*TILE,
                                     fill="#000000", stipple="gray50",
                                     tags="overlay")
        self.canvas.create_text(COLS*TILE//2, ROWS*TILE//2,
                                text="YOU DIED",
                                fill=COLORS["hp_low"],
                                font=("Consolas", 28, "bold"),
                                tags="overlay")

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