import tkinter as tk
from tkinter import messagebox
import socket
import threading
import sys
import os
import json

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from common.protocol import send_json, recv_json
except ImportError:
    print("Error: Cannot find 'common.protocol'. Please ensure 'common' folder is in the parent directory.")
    sys.exit(1)

HOST = 'linux2.cs.nycu.edu.tw'
PORT = 12131

class GameTemplate:
    def __init__(self, root, username, room_id):
        self.root = root
        self.username = username
        self.room_id = int(room_id)
        
        self.root.title(f"Game Room {self.room_id} - Player: {self.username}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.my_turn = False
        self.my_symbol = None 
        self.opponent_name = "Unknown"
        self.running = True

        if not self.connect_server():
            self.root.destroy()
            return

        self.init_ui()
        
        threading.Thread(target=self.network_loop, daemon=True).start()

    def init_ui(self):
        """[TODO] 初始化你的遊戲介面 (Button, Label, Canvas...)"""
        self.lbl_info = tk.Label(self.root, text="Waiting for opponent...", font=("Arial", 14))
        self.lbl_info.pack(pady=20)
        
        # 範例：一個簡單的動作按鈕
        self.btn_action = tk.Button(self.root, text="My Action", command=self.on_action, state="disabled")
        self.btn_action.pack(pady=20)

    def on_action(self):
        """[TODO] 當玩家觸發操作時 (例如點擊按鈕/棋盤)"""
        if not self.my_turn: return

        # 1. 更新本地狀態 (Visual)
        print("I took an action!")
        
        # 2. 傳送資料給對手
        # 注意：Server 預設轉送 'index' 和 'symbol' 兩個欄位
        # 'index' 可以是數字，也可以是 Dictionary (例如複雜的遊戲數據)
        move_data = {"action": "attack", "damage": 10} 
        self.send_move(move_data)
        
        # 3. 結束回合
        self.my_turn = False
        self.update_turn_ui()

    def handle_opponent_move(self, move_data, symbol):
        """[TODO] 當收到對手動作時，更新畫面"""
        print(f"Opponent ({symbol}) moved: {move_data}")
        
        # 範例：解析資料
        # action = move_data.get('action')
        
        # 輪到我了
        self.my_turn = True
        self.update_turn_ui()

    def update_turn_ui(self):
        """[TODO] 根據 self.my_turn 更新介面狀態 (例如鎖定按鈕)"""
        if self.my_turn:
            self.lbl_info.config(text="Your Turn!", fg="green")
            self.btn_action.config(state="normal")
        else:
            self.lbl_info.config(text=f"{self.opponent_name}'s Turn", fg="red")
            self.btn_action.config(state="disabled")


    def connect_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            # 加入房間指令
            send_json(self.sock, {
                'command': 'game_join', 
                'room_id': self.room_id, 
                'username': self.username
            })
            return True
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect: {e}")
            return False

    def send_move(self, move_data):
        """傳送遊戲動作至 Server"""
        try:
            # Server 協議要求欄位: command, room_id, index(資料), symbol(標記)
            payload = {
                'command': 'game_move',
                'room_id': self.room_id,
                'index': move_data,      # 這裡放入你的遊戲數據
                'symbol': self.my_symbol # 這裡放入你的玩家標記
            }
            send_json(self.sock, payload)
        except:
            pass

    def network_loop(self):
        """背景監聽 Server 訊息"""
        while self.running:
            try:
                msg = recv_json(self.sock)
                if not msg: break
                
                msg_type = msg.get('type')

                # 1. 遊戲開始
                if msg_type == 'game_start':
                    self.my_symbol = msg['symbol']      # Server 分配的標記 (X/O)
                    self.opponent_name = msg['opponent']
                    self.my_turn = msg['turn']          # 是否先手 (True/False)
                    
                    # 使用 `after` 避免 Thread 安全問題
                    self.root.after(0, lambda: self.root.title(f"Playing against {self.opponent_name}"))
                    self.root.after(0, self.update_turn_ui)

                # 2. 對手移動
                elif msg_type == 'opponent_move':
                    data = msg['index']  # 對手傳來的數據
                    sym = msg['symbol']  # 對手的標記
                    self.root.after(0, lambda: self.handle_opponent_move(data, sym))

                # 3. 對手離開
                elif msg_type == 'opponent_left':
                    self.root.after(0, lambda: messagebox.showinfo("Info", "Opponent left the game."))
                    self.running = False
                    self.root.after(0, self.root.destroy)

            except Exception as e:
                print(f"Network Error: {e}")
                break

    def on_close(self):
        self.running = False
        if self.sock: self.sock.close()
        self.root.destroy()

if __name__ == "__main__":
    user = sys.argv[1]
    rid = sys.argv[2]

    root = tk.Tk()
    root.geometry("600x400")
    game = GameTemplate(root, user, rid)
    root.mainloop()