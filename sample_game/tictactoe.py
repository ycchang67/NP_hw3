import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
import sys

try:
    from common.protocol import send_json, recv_json
except ImportError:
    sys.path.append('../')
    from common.protocol import send_json, recv_json

HOST = 'linux2.cs.nycu.edu.tw'
PORT = 12131

COLORS = {
    "bg": "#2c3e50",          
    "btn_default": "#ecf0f1", 
    "btn_hover": "#bdc3c7",
    "text_dark": "#2c3e50",
    "text_light": "#ffffff",
    "x_color": "#e74c3c",     
    "o_color": "#3498db",     
    "win_bg": "#2ecc71",      
    "lose_bg": "#e74c3c",     
    "draw_bg": "#f39c12"      
}

class Game:
    def __init__(self, root, user, rid):
        self.root = root
        self.user = user
        self.rid = int(rid)
        self.root.config(cursor="arrow")
        self.root.title(f"Tic-Tac-Toe - {user}")
        self.root.configure(bg=COLORS["bg"])
        self.center_window(450, 650)
        
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            send_json(self.sock, {'command': 'game_join', 'room_id': self.rid, 'username': self.user})
        except Exception as e:
            messagebox.showerror("Error", f"Connection Failed: {e}")
            self.root.destroy()
            return

        self.btns = []
        self.running = True
        self.dialog_win = None 
        
        self.setup_ui()
        self.reset_game_state() 
        
        threading.Thread(target=self.loop, daemon=True).start()

    def center_window(self, w, h):
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(ws-w)//2}+{(hs-h)//2}")

    def reset_game_state(self):
        self.turn = False
        self.sym = "?"
        self.opponent_sym = "?"
        self.board_state = [""] * 9
        self.game_over = False
        
        for btn in self.btns:
            btn.config(text="", bg=COLORS["btn_default"], state="normal")
        
        if hasattr(self, 'lbl_status'):
            self.lbl_status.config(text="Waiting for Opponent...", fg=COLORS["text_light"])
        if hasattr(self, 'lbl_vs'):
            self.lbl_vs.config(text="")

    def setup_ui(self):
        self.info_frame = tk.Frame(self.root, bg=COLORS["bg"], pady=20)
        self.info_frame.pack(fill="x")
        
        self.lbl_status = tk.Label(self.info_frame, text="Connecting...", font=("Helvetica", 16, "bold"), 
                                   bg=COLORS["bg"], fg=COLORS["text_light"])
        self.lbl_status.pack()
        
        self.lbl_vs = tk.Label(self.info_frame, text="", font=("Arial", 10), bg=COLORS["bg"], fg="#bdc3c7")
        self.lbl_vs.pack()

        self.board_frame = tk.Frame(self.root, bg=COLORS["bg"])
        self.board_frame.pack(expand=True)
        
        for i in range(9):
            cell = tk.Frame(self.board_frame, bg=COLORS["bg"], padx=5, pady=5)
            cell.grid(row=i//3, column=i%3)
            
            btn = tk.Button(cell, text="", font=("Arial", 28, "bold"), width=4, height=2,
                            bg=COLORS["btn_default"], relief="flat",
                            activebackground=COLORS["btn_hover"],
                            command=lambda x=i: self.make_move(x))
            btn.pack(fill="both", expand=True)
            self.btns.append(btn)
            
        self.bottom_frame = tk.Frame(self.root, bg=COLORS["bg"], pady=20)
        self.bottom_frame.pack(fill="x")
        
        self.btn_quit = tk.Button(self.bottom_frame, text="Leave Room", font=("Arial", 12),
                                  bg="#95a5a6", fg="white", relief="flat", padx=20, pady=5,
                                  command=self.on_exit)
        self.btn_quit.pack()

    def make_move(self, idx):
        if not self.running or self.game_over: return
        if not self.turn: return
        if self.board_state[idx] != "": return

        self.update_board(idx, self.sym)
        self.turn = False
        self.lbl_status.config(text="Opponent's Turn...", fg="#bdc3c7")
        
        send_json(self.sock, {'command': 'game_move', 'room_id': self.rid, 'index': idx, 'symbol': self.sym})
        
        if self.check_win(self.sym):
            self.end_game("win")
        elif "" not in self.board_state:
            self.end_game("draw")

    def loop(self):
        while self.running:
            try:
                msg = recv_json(self.sock)
                if not msg: break
                
                if msg['type'] == 'game_start':
                    self.root.after(0, lambda m=msg: self.start_new_game(m))
                    
                elif msg['type'] == 'opponent_move':
                    idx = msg['index']
                    sym = msg['symbol']
                    self.root.after(0, lambda: self.handle_opponent_move(idx, sym))
                
                elif msg['type'] == 'opponent_left':
                    self.root.after(0, self.handle_opponent_left)
                
                elif msg['type'] == 'game_error':
                    self.root.after(0, lambda m=msg: messagebox.showerror("Error", m['msg']))

            except Exception as e:
                print(f"Loop Error: {e}")
                break

    def start_new_game(self, msg):
        if self.dialog_win and self.dialog_win.winfo_exists():
            self.dialog_win.destroy()
        
        self.reset_game_state()
        
        self.sym = msg['symbol']
        self.opponent_sym = "O" if self.sym == "X" else "X"
        self.turn = msg['turn']
        opp_name = msg['opponent']
        
        self.lbl_vs.config(text=f"You ({self.sym}) vs {opp_name} ({self.opponent_sym})")
        if self.turn:
            self.lbl_status.config(text="Your Turn!", fg=COLORS["win_bg"])
        else:
            self.lbl_status.config(text=f"{opp_name}'s Turn", fg="#bdc3c7")

    def handle_opponent_move(self, idx, sym):
        self.update_board(idx, sym)
        if self.check_win(sym):
            self.end_game("lose")
        elif "" not in self.board_state:
            self.end_game("draw")
        else:
            self.turn = True
            self.lbl_status.config(text="Your Turn!", fg=COLORS["win_bg"])
    
    def handle_opponent_left(self):
        if self.dialog_win and self.dialog_win.winfo_exists():
            self.dialog_win.destroy()
        
        messagebox.showinfo("Game Info", "Opponent has left the game.")
        self.on_exit()

    def update_board(self, idx, sym):
        self.board_state[idx] = sym
        color = COLORS["x_color"] if sym == "X" else COLORS["o_color"]
        self.btns[idx].config(text=sym, fg=color, state="disabled")

    def check_win(self, player_sym):
        wins = [
            (0,1,2), (3,4,5), (6,7,8),
            (0,3,6), (1,4,7), (2,5,8),
            (0,4,8), (2,4,6)
        ]
        for a, b, c in wins:
            if self.board_state[a] == self.board_state[b] == self.board_state[c] == player_sym:
                self.highlight_win(a, b, c)
                return True
        return False

    def highlight_win(self, a, b, c):
        for idx in [a, b, c]:
            self.btns[idx].config(bg=COLORS["win_bg"], fg="white")

    def end_game(self, result):
        self.game_over = True
        
        title = ""
        msg = ""
        bg_color = ""
        
        if result == "win":
            title = "VICTORY!"
            msg = "You won! Play again?"
            bg_color = COLORS["win_bg"]
            self.lbl_status.config(text="YOU WON!", fg=COLORS["win_bg"])
        elif result == "lose":
            title = "DEFEAT"
            msg = "You lost. Rematch?"
            bg_color = COLORS["lose_bg"]
            self.lbl_status.config(text="YOU LOST", fg=COLORS["lose_bg"])
        else:
            title = "DRAW"
            msg = "It's a tie! Try again?"
            bg_color = COLORS["draw_bg"]
            self.lbl_status.config(text="DRAW", fg=COLORS["draw_bg"])

        try:
            send_json(self.sock, {'command': 'game_over', 'room_id': self.rid})
        except: pass
        
        self.show_game_over_dialog(title, msg, bg_color)

    def show_game_over_dialog(self, title, msg, color):
        if self.dialog_win and self.dialog_win.winfo_exists():
            self.dialog_win.destroy()

        self.dialog_win = tk.Toplevel(self.root)
        self.dialog_win.title("Game Over")
        self.dialog_win.geometry("400x250")
        self.dialog_win.configure(bg="white")
        ws = self.dialog_win.winfo_screenwidth()
        hs = self.dialog_win.winfo_screenheight()
        self.dialog_win.geometry(f"+{(ws-400)//2}+{(hs-250)//2}")
        
        head = tk.Frame(self.dialog_win, bg=color, pady=15)
        head.pack(fill="x")
        tk.Label(head, text=title, font=("Arial", 20, "bold"), bg=color, fg="white").pack()
        
        body = tk.Frame(self.dialog_win, bg="white", pady=20)
        body.pack(fill="both", expand=True)
        tk.Label(body, text=msg, font=("Arial", 12), bg="white").pack(pady=10)
        
        btn_frame = tk.Frame(body, bg="white")
        btn_frame.pack(pady=10)

        def on_restart():
            try:
                send_json(self.sock, {'command': 'game_restart', 'room_id': self.rid})
                self.dialog_win.destroy()
                self.lbl_status.config(text="Waiting for other player...", fg="gray")
            except: pass

        def on_leave():
            self.dialog_win.destroy()
            self.on_exit()

        tk.Button(btn_frame, text="Play Again", font=("Arial", 11, "bold"), 
                  bg=COLORS["win_bg"], fg="white", padx=15, pady=5, relief="flat",
                  command=on_restart).pack(side="left", padx=10)
                  
        tk.Button(btn_frame, text="Exit to Room", font=("Arial", 11, "bold"), 
                  bg="gray", fg="white", padx=15, pady=5, relief="flat",
                  command=on_leave).pack(side="left", padx=10)
        
        self.dialog_win.protocol("WM_DELETE_WINDOW", on_leave)

    def on_exit(self):
        self.running = False
        if self.sock: self.sock.close()
        self.root.destroy()

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        root = tk.Tk()
        Game(root, sys.argv[1], sys.argv[2])
        root.mainloop()