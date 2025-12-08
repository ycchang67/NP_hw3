import sys
import os
import random
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

try:
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from common.protocol import send_json, recv_json
except ImportError:
    print("Error: Cannot find 'common.protocol'.")
    sys.exit(1)


HOST = 'linux3.cs.nycu.edu.tw'
PORT = 12131

class BingoGame:
    def __init__(self, username, room_id):
        self.username = username
        self.room_id = int(room_id)
        self.sock = None
        self.running = True
 
        self.board = []       # 5x5 Grid
        self.marked = []      # 5x5 Boolean
        self.used_numbers = set()
        self.my_turn = False
        self.opponent_name = "Unknown"
        self.game_over = False

        self.initialize_board()

    def connect_server(self):
        try:
            import socket
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            send_json(self.sock, {'command': 'game_join', 'room_id': self.room_id, 'username': self.username})
            return True
        except Exception as e:
            print(f"[Error] Connection failed: {e}")
            return False

    def initialize_board(self):
        numbers = list(range(1, 76))
        random.shuffle(numbers)
        
        self.board = [[0]*5 for _ in range(5)]
        self.marked = [[False]*5 for _ in range(5)]
        
        idx = 0
        for i in range(5):
            for j in range(5):
                self.board[i][j] = numbers[idx]
                idx += 1
        

        self.marked[2][2] = True
        self.used_numbers.add(self.board[2][2])

    def print_board(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"\n=== BINGO Board ({self.username}) ===")
        print(f"Room: {self.room_id} | Opponent: {self.opponent_name}")
        print("-------------------------------------")
        print("  B   I   N   G   O")
        print("-------------------------------------")
        
        for i in range(5):
            row_str = ""
            for j in range(5):
                num = self.board[i][j]
                if self.marked[i][j]:
                    row_str += f"[{num:2}] "
                else:
                    row_str += f" {num:2}  "
            print(row_str)
        print("-------------------------------------")
        print(f"Lines: {self.count_lines()}")
        if self.my_turn and not self.game_over:
            print("\n[YOUR TURN] Enter a number to call (1-75): ", end='', flush=True)
        elif not self.game_over:
            print(f"\n[WAITING] Waiting for {self.opponent_name}...", flush=True)

    def mark_number(self, num):
        found = False
        for i in range(5):
            for j in range(5):
                if self.board[i][j] == num:
                    self.marked[i][j] = True
                    found = True
        return found

    def count_lines(self):
        lines = 0
        # Rows & Cols
        for i in range(5):
            if all(self.marked[i][j] for j in range(5)): lines += 1
            if all(self.marked[j][i] for j in range(5)): lines += 1
        
        # Diagonals
        if all(self.marked[i][i] for i in range(5)): lines += 1
        if all(self.marked[i][4-i] for i in range(5)): lines += 1
        
        return lines

    def send_action(self, number):
        try:

            lines = self.count_lines()
            is_win = (lines >= 3) 
            
            payload = {
                'command': 'game_move',
                'room_id': self.room_id,
                'index': number,    
                'symbol': 'WIN' if is_win else 'NEXT'
            }
            send_json(self.sock, payload)
            
            if is_win:
                self.game_over = True
                print(f"\n\n*** BINGO! You WIN with {lines} lines! ***")
                self.running = False
                
        except Exception as e:
            print(f"Send Error: {e}")

    def network_loop(self):
        while self.running:
            try:
                msg = recv_json(self.sock)
                if not msg: 
                    print("\nDisconnected from server.")
                    self.running = False
                    break
                
                mtype = msg.get('type')

                if mtype == 'game_start':
                    self.my_turn = msg['turn']
                    self.opponent_name = msg['opponent']
                    self.print_board()

                elif mtype == 'opponent_move':
                    num = msg['index']
                    status = msg['symbol'] # WIN or NEXT
                    
                    print(f"\nOpponent called: {num}")
                    self.mark_number(num)
                    self.used_numbers.add(num)
                    
                    if status == 'WIN':
                        self.print_board()
                        print("\n\n[GAME OVER] Opponent Wins! Better luck next time.")
                        self.game_over = True
                        self.running = False
                        break
                    
                    if self.count_lines() >= 3:
                        self.print_board()
                        print("\n\n*** BINGO! You also WIN! It's a DRAW! ***")

                        self.send_action(0) # Dummy
                        self.game_over = True
                        self.running = False
                        break

                    self.my_turn = True
                    self.print_board()

                elif mtype == 'opponent_left':
                    print("\n\nOpponent left the game.")
                    self.running = False
                    break

            except Exception as e:
                # print(f"Net Loop Err: {e}")
                break
        
        if self.sock: self.sock.close()
        print("\nGame session ended. Press Enter to exit.")

    def input_loop(self):
        while self.running:
            if self.my_turn and not self.game_over:
                try:
                    user_input = sys.stdin.readline().strip()
                    if not user_input: continue
                    
                    if not user_input.isdigit():
                        print("Invalid input! Enter number 1-75: ", end='', flush=True)
                        continue
                        
                    num = int(user_input)
                    if num < 1 or num > 75:
                        print("Out of range (1-75): ", end='', flush=True)
                        continue
                        
                    if num in self.used_numbers:
                        print("Number already used! Try again: ", end='', flush=True)
                        continue

                    self.mark_number(num)
                    self.used_numbers.add(num)
                    self.my_turn = False
                    self.print_board()
                    self.send_action(num)
                    
                except ValueError:
                    pass
            else:
                import time
                time.sleep(0.1)

    def start(self):
        if not self.connect_server(): return
        
        t = threading.Thread(target=self.network_loop, daemon=True)
        t.start()
        
        print("Waiting for game start...")
        
        try:
            self.input_loop()
        except KeyboardInterrupt:
            self.running = False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python bingo.py <username> <room_id>")
    else:
        game = BingoGame(sys.argv[1], sys.argv[2])
        game.start()