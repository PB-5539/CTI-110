import math
import random
import time
import threading
import tkinter as tk
from tkinter import messagebox

# Constants
TILE_SIZE = 32
MAP_WIDTH = 10
MAP_HEIGHT = 10

# Sample assets (user must provide images with these names)
ASSETS = {
    "player": "player.png",
    "goblin": "goblin.png",
    "chest": "chest.png",
    "stair": "stair.png"
}

# Sample loot tables
LOOT_TABLES = {
    1: ["Potion", "Sword"],
    2: ["Potion", "Shield", "Bow"]
}

# Sample item stats
ITEM_STATS = {
    "Potion": {"heal": 20},
    "Sword": {"damage": 5},
    "Shield": {"defense": 2},
    "Bow": {"damage": 3}
}

class Monster:
    def __init__(self, name, x, y, hp=10):
        self.name = name
        self.x = x
        self.y = y
        self.hp = hp
    
    def take_turn(self, player_pos):
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        if abs(dx) + abs(dy) <= 1:
            self.attack()
        else:
            self.move_towards(player_pos)
    
    def move_towards(self, pos):
        if pos[0] > self.x: self.x += 1
        elif pos[0] < self.x: self.x -= 1
        if pos[1] > self.y: self.y += 1
        elif pos[1] < self.y: self.y -= 1
    
    def attack(self):
        print(f"{self.name} attacks!")

class Game:
    def __init__(self):
        # Player structure
        self.player = {
            "stats": {"hp": 100, "damage": 5, "defense": 2, "speed": 1},
            "position": [0, 0],
            "inventory": {},
            "hotbar": {},
            "xp": 0
        }
        self.turn_count = 0
        self.floor = 1
        self.monsters = []
        self.running = True
        
        # Initialize main menu
        self.root = tk.Tk()
        self.root.title("Roguelike")
        self.create_main_menu()
        self.root.mainloop()
    
    def create_main_menu(self):
        tk.Label(self.root, text="Roguelike Dungeon").pack(pady=20)
        tk.Button(self.root, text="Play", command=self.start_game).pack(fill="x")
        tk.Button(self.root, text="Settings", command=self.open_settings).pack(fill="x")
        tk.Button(self.root, text="Quit", command=self.root.destroy).pack(fill="x")
    
    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        tk.Label(win, text="Misc Settings").pack(pady=10)
    
    def start_game(self):
        self.root.destroy()  # Close main menu
        self.game_window = tk.Tk()
        self.game_window.title("Dungeon Crawl")
        self.create_ui()
        self.spawn_monsters()
        self.draw()
        threading.Thread(target=self.game_loop).start()
        self.game_window.mainloop()
    
    def create_ui(self):
        self.canvas = tk.Canvas(self.game_window, width=MAP_WIDTH*TILE_SIZE, height=MAP_HEIGHT*TILE_SIZE, bg="black")
        self.canvas.grid(row=0, column=1)
        
        # Inventory frame
        self.inv_frame = tk.Frame(self.game_window)
        self.inv_frame.grid(row=0, column=0)
        tk.Label(self.inv_frame, text="Inventory").pack()
        self.inv_list = tk.Listbox(self.inv_frame)
        self.inv_list.pack()
        
        # Stats
        self.stats_label = tk.Label(self.inv_frame, text=f"HP: {self.player['stats']['hp']}  Turn: {self.turn_count}  Floor: {self.floor}")
        self.stats_label.pack()
        
        # Skill tree button
        tk.Button(self.inv_frame, text="Skill Tree", command=self.open_skill_tree).pack()
        
        # Text terminal
        self.terminal = tk.Text(self.game_window, height=5)
        self.terminal.grid(row=1, column=1)
    
    def spawn_monsters(self):
        self.monsters.append(Monster("Goblin", 5, 5))
    
    def open_skill_tree(self):
        win = tk.Toplevel(self.game_window)
        win.title("Skill Tree")
        tk.Label(win, text="XP: "+str(self.player["xp"])).pack()
        tk.Button(win, text="Increase Damage", command=lambda:self.upgrade("damage")).pack()
        tk.Button(win, text="Increase HP", command=lambda:self.upgrade("hp")).pack()
        tk.Button(win, text="Increase Speed", command=lambda:self.upgrade("speed")).pack()
    
    def upgrade(self, stat):
        if stat == "damage": self.player["stats"]["damage"] += 1
        elif stat == "hp": self.player["stats"]["hp"] += 10
        elif stat == "speed": self.player["stats"]["speed"] += 1
        print(f"{stat} upgraded!")
    
    def game_loop(self):
        while self.running:
            time.sleep(0.5)
            self.turn_count += 1
            self.update_monsters()
            self.draw()
            self.update_stats()
            if self.player["stats"]["hp"] <= 0:
                self.death_screen()
    
    def update_monsters(self):
        for m in self.monsters:
            m.take_turn(self.player["position"])
    
    def draw(self):
        self.canvas.delete("all")
        # Player
        x, y = self.player["position"]
        self.canvas.create_rectangle(x*TILE_SIZE, y*TILE_SIZE, (x+1)*TILE_SIZE, (y+1)*TILE_SIZE, fill="white")
        # Monsters
        for m in self.monsters:
            self.canvas.create_rectangle(m.x*TILE_SIZE, m.y*TILE_SIZE, (m.x+1)*TILE_SIZE, (m.y+1)*TILE_SIZE, fill="red")
    
    def update_stats(self):
        self.stats_label.config(text=f"HP: {self.player['stats']['hp']}  Turn: {self.turn_count}  Floor: {self.floor}")
    
    def death_screen(self):
        self.running = False
        messagebox.showinfo("Death", "You have died!")
        self.game_window.destroy()

if __name__ == "__main__":
    Game()