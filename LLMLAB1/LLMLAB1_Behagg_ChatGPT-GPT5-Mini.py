#attempt #: 5
import math
import random
import time
import tkinter as tk
import threading

TILE_SIZE = 48
GRID_W = 10
GRID_H = 10

# ------------------ DATA ------------------

item_stats = {
    "sword": {"damage": 5},
    "shield": {"defense": 3},
    "boots": {"speed": 1},
}

loot_tables = {
    1: ["sword", "shield"],
    2: ["sword", "boots"],
}

level_maps = [
    {"walls": [(1,1),(2,2),(3,3)], "monsters": [(5,5),(7,7)], "stairs": (9,9)},
    {"walls": [(2,1),(4,4),(6,6)], "monsters": [(3,5),(8,2)], "stairs": (0,9)},
]

# ------------------ PLAYER ------------------

def create_player():
    return {
        "stats": {"hp": 100, "max_hp": 100, "damage": 10, "defense": 0, "speed": 1},
        "pos": [0, 0],
        "inventory": {},
        "hotbar": {},
        "xp": 0
    }

# ------------------ MONSTER ------------------

class Monster:
    def __init__(self, x, y, name="Goblin"):
        self.x = x
        self.y = y
        self.hp = 30
        self.name = name

    def distance(self, player):
        return abs(self.x - player["pos"][0]) + abs(self.y - player["pos"][1])

    def act(self, game):
        px, py = game.player["pos"]

        if self.hp < 10:
            # flee
            if self.x < px: self.x -= 1
            elif self.x > px: self.x += 1
            if self.y < py: self.y -= 1
            elif self.y > py: self.y += 1
            return

        if self.distance(game.player) == 1:
            dmg = 5
            game.player["stats"]["hp"] -= dmg
            game.log(f"{self.name} dealt {dmg} damage!")
        else:
            if self.x < px: self.x += 1
            elif self.x > px: self.x -= 1
            if self.y < py: self.y += 1
            elif self.y > py: self.y -= 1

# ------------------ GAME ------------------

class Game:
    def __init__(self, root):
        self.root = root
        self.player = create_player()
        self.turn = 0
        self.floor = 1
        self.running = True

        self.window = tk.Toplevel(root)
        self.window.title("Dungeon")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        self.setup_ui()
        self.load_level()

        self.thread = threading.Thread(target=self.game_loop)
        self.thread.start()

    def setup_ui(self):
        self.left_frame = tk.Frame(self.window)
        self.left_frame.pack(side="left")

        self.stats_label = tk.Label(self.left_frame, text="Stats")
        self.stats_label.pack()

        self.inventory_canvas = tk.Canvas(self.left_frame, width=9*TILE_SIZE, height=4*TILE_SIZE, bg="gray")
        self.inventory_canvas.pack()

        self.skill_btn = tk.Button(self.left_frame, text="Skill Tree", command=self.open_skill_tree)
        self.skill_btn.pack()

        self.right_frame = tk.Frame(self.window)
        self.right_frame.pack(side="right")

        self.canvas = tk.Canvas(self.right_frame, width=GRID_W*TILE_SIZE, height=GRID_H*TILE_SIZE, bg="black")
        self.canvas.pack()

        self.log_box = tk.Text(self.right_frame, height=8, bg="black", fg="white")
        self.log_box.pack()

        self.window.bind("<Key>", self.key_input)

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def load_level(self):
        data = random.choice(level_maps)
        self.walls = data["walls"]
        self.stairs = data["stairs"]
        self.monsters = [Monster(x,y) for x,y in data["monsters"]]

    def draw(self):
        self.canvas.delete("all")

        # draw grid
        for x in range(GRID_W):
            for y in range(GRID_H):
                self.canvas.create_rectangle(
                    x*TILE_SIZE, y*TILE_SIZE,
                    (x+1)*TILE_SIZE, (y+1)*TILE_SIZE,
                    outline="white"
                )

        # stairs
        sx, sy = self.stairs
        self.canvas.create_rectangle(sx*TILE_SIZE, sy*TILE_SIZE,
                                     (sx+1)*TILE_SIZE, (sy+1)*TILE_SIZE,
                                     fill="yellow")

        # player
        px, py = self.player["pos"]
        self.canvas.create_rectangle(px*TILE_SIZE, py*TILE_SIZE,
                                     (px+1)*TILE_SIZE, (py+1)*TILE_SIZE,
                                     fill="blue")

        # monsters
        for m in self.monsters:
            self.canvas.create_rectangle(m.x*TILE_SIZE, m.y*TILE_SIZE,
                                         (m.x+1)*TILE_SIZE, (m.y+1)*TILE_SIZE,
                                         fill="red")

    def move_player(self, dx, dy):
        for _ in range(self.player["stats"]["speed"]):
            nx = self.player["pos"][0] + dx
            ny = self.player["pos"][1] + dy

            if (nx, ny) in self.walls:
                return

            self.player["pos"] = [nx, ny]

            if (nx, ny) == self.stairs:
                self.floor += 1
                self.log("You descend deeper...")
                self.load_level()

        self.end_turn()

    def attack(self):
        px, py = self.player["pos"]

        for m in self.monsters:
            if abs(m.x - px) + abs(m.y - py) == 1:
                dmg = self.player["stats"]["damage"]
                m.hp -= dmg
                self.log(f"You hit {m.name} for {dmg}")

                if m.hp <= 0:
                    self.log(f"{m.name} died!")
                    self.monsters.remove(m)
                    self.player["xp"] += 5
                break

        self.end_turn()

    def end_turn(self):
        self.turn += 1

        for m in self.monsters:
            m.act(self)

        if self.player["stats"]["hp"] <= 0:
            self.death_screen()

    def key_input(self, event):
        key = event.keysym.lower()

        if key in ["w","up"]:
            self.move_player(0,-1)
        elif key in ["s","down"]:
            self.move_player(0,1)
        elif key in ["a","left"]:
            self.move_player(-1,0)
        elif key in ["d","right"]:
            self.move_player(1,0)
        elif key == "e":
            self.attack()

    def game_loop(self):
        while self.running:
            self.draw()
            time.sleep(0.1)

    def open_skill_tree(self):
        win = tk.Toplevel(self.window)
        win.title("Skills")

        tk.Button(win, text="Damage +1", command=lambda:self.upgrade("damage")).pack()
        tk.Button(win, text="Health +10", command=lambda:self.upgrade("hp")).pack()
        tk.Button(win, text="Speed +1", command=lambda:self.upgrade("speed")).pack()

    def upgrade(self, stat):
        if self.player["xp"] <= 0:
            return

        if stat == "damage":
            self.player["stats"]["damage"] += 1
        elif stat == "hp":
            self.player["stats"]["max_hp"] += 10
            self.player["stats"]["hp"] += 10
        elif stat == "speed":
            self.player["stats"]["speed"] += 1

        self.player["xp"] -= 1

    def death_screen(self):
        self.running = False
        win = tk.Toplevel(self.window)
        win.title("You Died")
        tk.Label(win, text="Game Over").pack()
        tk.Button(win, text="Quit", command=self.window.destroy).pack()

    def on_close(self):
        self.running = False
        self.window.destroy()
        self.root.destroy()

# ------------------ MENU ------------------

def open_settings(root):
    win = tk.Toplevel(root)
    win.title("Settings")
    tk.Label(win, text="Settings go here").pack()

def start_game(root):
    Game(root)

def main_menu():
    root = tk.Tk()
    root.title("Main Menu")

    tk.Button(root, text="Play", command=lambda:start_game(root)).pack()
    tk.Button(root, text="Settings", command=lambda:open_settings(root)).pack()
    tk.Button(root, text="Quit", command=root.destroy).pack()

    root.mainloop()

# ------------------ RUN ------------------

if __name__ == "__main__":
    main_menu()