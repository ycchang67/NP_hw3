import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import sys
import os
import random

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from common.protocol import send_json, recv_json
except ImportError:
    print("Error: Cannot find 'common.protocol'.")
    sys.exit(1)

HOST = 'linux2.cs.nycu.edu.tw'
PORT = 12131

class GuessGame:
    def __init__(self, root, username, room_id):
        self.root = root
        self.username = username
        self.room_id = int(room_id)
        
        self.root.title(f"Ultimate Number - Room {self.room_id}")
        self.root.geometry("500x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
        self.running = True
        self.min_val = 0
        self.max_val = 100
        
        random.seed(self.room_id) 
        self.target = random.randint(1, 99) 
    
        if not self.connect_server():
            self.root.destroy()
            return

        self.init_ui()
        threading.Thread(target=self.network_loop, daemon=True).start()

    def connect_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            send_json(self.sock, {
                'command': 'game_join', 
                'room_id': self.room_id, 
                'username': self.username
            })
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Connection failed: {e}")
            return False

    def init_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Big.TLabel", font=("Arial", 36, "bold"), foreground="#2c3e50")
        style.configure("Info.TLabel", font=("Arial", 14), foreground="#7f8c8d")
        
        frame_top = tk.Frame(self.root, pady=20, bg="#ecf0f1")
        frame_top.pack(fill="x")
        
        tk.Label(frame_top, text="Current Range", bg="#ecf0f1", font=("Arial", 12)).pack()
        self.lbl_range = ttk.Label(frame_top, text=f"{self.min_val} ~ {self.max_val}", style="Big.TLabel")
        self.lbl_range.pack()

        frame_mid = tk.Frame(self.root, pady=20)
        frame_mid.pack()
        
        self.ent_guess = ttk.Entry(frame_mid, font=("Arial", 16), width=10, justify="center")
        self.ent_guess.pack(side="left", padx=10)
        self.ent_guess.bind('<Return>', lambda e: self.do_guess())
        
        self.btn_guess = ttk.Button(frame_mid, text="GUESS!", command=self.do_guess)
        self.btn_guess.pack(side="left", ipadx=10, ipady=5)

        frame_btm = tk.Frame(self.root, padx=20, pady=10)
        frame_btm.pack(fill="both", expand=True)
        
        tk.Label(frame_btm, text="Game Log:", anchor="w").pack(fill="x")
        
        self.list_log = tk.Listbox(frame_btm, font=("Courier", 11), bg="#f9f9f9", relief="flat")
        self.list_log.pack(fill="both", expand=True)
        
        self.lbl_status = tk.Label(self.root, text=f"Target locked (Seed: {self.room_id})", bd=1, relief="sunken", anchor="w")
        self.lbl_status.pack(side="bottom", fill="x")

    def do_guess(self):
        val_str = self.ent_guess.get()
        if not val_str.isdigit():
            messagebox.showwarning("Invalid", "Please enter a number.")
            return
            
        val = int(val_str)
        if val <= self.min_val or val >= self.max_val:
            messagebox.showwarning("Range Error", f"Number must be between {self.min_val} and {self.max_val}!")
            self.ent_guess.delete(0, 'end')
            return
        self.send_move(val)
        self.ent_guess.delete(0, 'end')

    def send_move(self, number):
        try:
            result = "range"
            if number == self.target:
                result = "win"
            
            payload = {
                'command': 'game_move',
                'room_id': self.room_id,
                'index': number,    
                'symbol': result    
            }
            send_json(self.sock, payload)
        except: pass

    def update_game_state(self, player, number, result):
        if result == "win":
            self.log(f"{player} guessed {number} and EXPLODED! (Game Over)")
            self.lbl_range.config(text=f"{number}", foreground="#c0392b")
            self.btn_guess.config(state="disabled")
            messagebox.showinfo("Game Over", f"{player} hit the number {number}!\nGame Over!")
            self.running = False
            return

        if self.min_val < number < self.target:
            self.min_val = number
        elif self.target < number < self.max_val:
            self.max_val = number
        
        self.lbl_range.config(text=f"{self.min_val} ~ {self.max_val}")
        self.log(f"{player} guessed {number}")

    def log(self, msg):
        self.list_log.insert(tk.END, msg)
        self.list_log.see(tk.END)

    def network_loop(self):
        while self.running:
            try:
                msg = recv_json(self.sock)
                if not msg: break
                
                mtype = msg.get('type')
                
                
                if mtype == 'opponent_move':
                   
                    user = "Opponent" 
                    
                    num = msg['index']
                    res = msg['symbol']
                    self.root.after(0, lambda: self.update_game_state("Someone", num, res))

                
            except: break
        self.on_close()

    def send_move(self, number):
        super_send = super
        try:
            result = "range"
            if number == self.target: result = "win"
          
            payload = {
                'command': 'game_move',
                'room_id': self.room_id,
                'index': number,
                'symbol': result
            }
            send_json(self.sock, payload)

            self.update_game_state(f"{self.username} (You)", number, result)
            
        except: pass

    def on_close(self):
        self.running = False
        if self.sock: self.sock.close()
        self.root.destroy()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        root = tk.Tk()
        GuessGame(root, "DevUser", "100")
        root.mainloop()
    else:
        root = tk.Tk()
        GuessGame(root, sys.argv[1], sys.argv[2])
        root.mainloop()