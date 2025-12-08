import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import socket
import os
import subprocess
import sys
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.protocol import send_json, recv_json, recv_file

HOST = 'linux2.cs.nycu.edu.tw'
PORT = 12131
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, 'downloads')

# =====logic code ===================
class GameStoreService:
    def __init__(self):
        self.socket = None

    def connect(self):
        try:
            if self.socket:
                self.socket.close()
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)
            self.socket.connect((HOST, PORT))
            self.socket.settimeout(None)
            return True
        except Exception as error:
            print(f"[Service] Connection Error: {error}")
            return False

    def close(self):
        if self.socket:
            self.socket.close()

    def _send_command(self, data):
        if not self.socket:
            return None
        try:
            if send_json(self.socket, data):
                return recv_json(self.socket)
        except Exception:
            return None
        return None

    def login(self, username, password):
        return self._send_command({
            'command': 'login',
            'role': 'player',
            'username': username,
            'password': password
        })

    def register(self, username, password):
        return self._send_command({
            'command': 'register',
            'role': 'player',
            'username': username,
            'password': password
        })

    def get_game_list(self):
        return self._send_command({'command': 'list_games'})

    def get_room_list(self):
        return self._send_command({'command': 'list_rooms'})

    def get_game_details(self, game_id):
        return self._send_command({'command': 'get_game_details', 'game_id': game_id})

    def download_game(self, game_id, save_path):
        response = self._send_command({'command': 'download_game', 'game_id': game_id})
        
        if response and response['status'] == 'success':
            server_version = response['version']
            
            game_file_path = os.path.join(save_path, 'game.py')
            version_file_path = os.path.join(save_path, 'version.txt')
            
            if recv_file(self.socket, game_file_path):
                with open(version_file_path, 'w') as f:
                    f.write(str(server_version))
                return True
        
        return False

    def create_room(self, game_id):
        return self._send_command({'command': 'create_room', 'game_id': game_id})

    def join_room(self, room_id):
        return self._send_command({'command': 'join_room', 'room_id': room_id})

    def leave_room(self, room_id):
        return self._send_command({'command': 'leave_room', 'room_id': room_id})

    def get_room_info(self, room_id):
        return self._send_command({'command': 'get_room_info', 'room_id': room_id})

    def start_game(self, room_id):
        return self._send_command({'command': 'start_game', 'room_id': room_id})

    def submit_review(self, game_id, rating, comment):
        return self._send_command({
            'command': 'submit_review', 
            'game_id': game_id, 
            'rating': rating, 
            'comment': comment
        })

# ===UI ============
class PlayerApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Game Store - Player")
        self.root.geometry("1000x700")
        self.root.config(cursor="left_ptr")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.setup_styles()
        self.service = GameStoreService()
        self.username = None
        self.room_cache = {}
        
        self.init_login_ui()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("Card.TFrame", background="white", relief="raised")
        self.style.configure("TButton", font=('Arial', 10), padding=5)
        self.style.configure("Nav.TButton", font=('Arial', 11, 'bold'), padding=10, background="#2196F3", foreground="white")
        self.style.map("Nav.TButton", background=[('active', '#1976D2')])
        self.style.configure("Update.TButton", background="#FF9800", foreground="white")
        self.style.map("Update.TButton", background=[('active', '#F57C00')])

    def on_close(self):
        self.service.close()
        try: self.root.destroy()
        except: pass

    # --- Login ---
    def init_login_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        self.root.configure(bg="#e0e0e0")
        
        frame = tk.Frame(self.root, bg="#e0e0e0", pady=50)
        frame.pack(expand=True, fill="both")
        
        box = tk.Frame(frame, bg="white", padx=40, pady=40, relief="ridge", bd=2)
        box.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(box, text="Player Login", font=("Arial", 20, "bold"), bg="white").pack(pady=20)
        
        tk.Label(box, text="Username:", bg="white").pack(anchor="w")
        self.entry_user = ttk.Entry(box, width=30)
        self.entry_user.pack(pady=(0,10))
        
        tk.Label(box, text="Password:", bg="white").pack(anchor="w")
        self.entry_pass = ttk.Entry(box, width=30, show="*")
        self.entry_pass.pack(pady=(0,15))
        
        ttk.Button(box, text="Login", command=self.handle_login).pack(fill="x", pady=5)
        ttk.Button(box, text="Register", command=self.handle_register).pack(fill="x")

    def handle_login(self):
        if not self.service.connect():
            messagebox.showerror("Error", "Server not available")
            return
            
        resp = self.service.login(self.entry_user.get(), self.entry_pass.get())
        if resp and resp['status'] == 'success':
            self.username = self.entry_user.get()
            self.init_main_ui()
        else:
            msg = resp['msg'] if resp else "Login failed"
            messagebox.showerror("Failed", msg)
            self.service.close()

    def handle_register(self):
        if not self.service.connect():
            messagebox.showerror("Error", "Server not available")
            return
            
        resp = self.service.register(self.entry_user.get(), self.entry_pass.get())
        if resp and resp['status'] == 'success':
            messagebox.showinfo("Success", "Registered!")
        else:
            msg = resp['msg'] if resp else "Register Failed"
            messagebox.showerror("Failed", msg)
        self.service.close()
    # pure UI ==== page 1 ========
    # --- Main Dashboard ---
    def init_main_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        
        nav = tk.Frame(self.root, bg="#2196F3", height=60)
        nav.pack(fill="x")
        
        tk.Label(nav, text="GameStore", bg="#2196F3", fg="white", font=("Arial", 18, "bold")).pack(side="left", padx=20)
        tk.Label(nav, text=f"User: {self.username}", bg="#2196F3", fg="#BBDEFB").pack(side="right", padx=20)
        
        btn_frame = tk.Frame(nav, bg="#2196F3")
        btn_frame.pack(side="right", padx=20)
        
        ttk.Button(btn_frame, text="Store", style="Nav.TButton", command=self.view_store).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Library", style="Nav.TButton", command=self.view_library).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Lobby", style="Nav.TButton", command=self.view_lobby).pack(side="left", padx=2)

        self.content = tk.Frame(self.root, bg="#f5f5f5")
        self.content.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.view_store()
     # clear
    def clear_content(self):
        for w in self.content.winfo_children(): w.destroy()

    # --- Store ---
    def view_store(self):
        self.clear_content()
        tk.Label(self.content, text="Game Store", font=("Arial", 20, "bold"), bg="#f5f5f5").pack(anchor="w", pady=10)
        
        resp = self.service.get_game_list()
        games = resp.get('data', []) if resp and resp.get('status') == 'success' else []
        
        container = tk.Frame(self.content, bg="#f5f5f5")
        container.pack(fill="both", expand=True)
        
        for i, game in enumerate(games):
            card = tk.Frame(container, bg="white", relief="raised", bd=1, padx=15, pady=15)
            card.grid(row=i//3, column=i%3, padx=10, pady=10, sticky="nsew")
            
            tk.Label(card, text=game['name'], font=("Arial", 14, "bold"), bg="white").pack(anchor="w")
            tk.Label(card, text=f"Type: {game['type']} | Rating: {game['rating']}", bg="white", fg="gray").pack(anchor="w")
            tk.Label(card, text=game['description'][:40]+"...", bg="white", wraplength=200).pack(fill="x", pady=10)
            
            ttk.Button(card, text="Details / Download", command=lambda g=game: self.show_details_window(g)).pack(fill="x")

    # --- Library ---
    def view_library(self):
        self.clear_content()
        tk.Label(self.content, text="My Library", font=("Arial", 20, "bold"), bg="#f5f5f5").pack(anchor="w", pady=10)
        
        user_path = os.path.join(DOWNLOAD_DIR, self.username)
        if not os.path.exists(user_path):
            tk.Label(self.content, text="No games downloaded yet.", bg="#f5f5f5").pack(pady=20)
            return
        # get list game  ==== return socket
        resp = self.service.get_game_list()
        server_available = True
        server_games = []
        
        if not resp or resp.get('status') != 'success':
            tk.Label(self.content, text="Offline Mode", fg="red", bg="#f5f5f5").pack()
            server_available = False
        else:
            server_games = resp.get('data', [])
        
        for dir_name in os.listdir(user_path):
            try:
                game_id = int(dir_name)
            except: continue

            game_dir = os.path.join(user_path, dir_name)
            version_file = os.path.join(game_dir, 'version.txt')
            if not os.path.exists(version_file): continue
            
            with open(version_file) as f: 
                local_ver = int(f.read().strip())
            
            # Sync 
            if server_available:
                matching_game = None
                for g in server_games:
                    if g['id'] == game_id:
                        matching_game = g
                        break
                
                if not matching_game:
                    try: shutil.rmtree(game_dir)
                    except: pass
                    continue
            else:
                matching_game = None

            # Render
            if matching_game:
                name = matching_game['name']
                is_outdated = local_ver < matching_game['version']
            else:
                name = f"Game {game_id} (Offline)"
                is_outdated = False
            
            row = tk.Frame(self.content, bg="white", padx=15, pady=10, relief="flat")
            row.pack(fill="x", pady=5)
            
            tk.Label(row, text=name, font=("Arial", 12, "bold"), bg="white", width=20, anchor="w").pack(side="left")
            tk.Label(row, text=f"v{local_ver}", bg="white", width=10).pack(side="left")
            
            # if not newest => update : create room
            if is_outdated:
                tk.Label(row, text="(Update Available)", fg="orange", bg="white").pack(side="left", padx=5)
                ttk.Button(row, text="Update Now", style="Update.TButton", 
                           command=lambda g=matching_game: self.show_details_window(g)).pack(side="right")
            else:
                ttk.Button(row, text="Create Room", command=lambda gid=game_id: self.handle_create_room(gid)).pack(side="right")

    # --- Lobby ---
    def view_lobby(self):
        self.clear_content()
        head = tk.Frame(self.content, bg="#f5f5f5")
        head.pack(fill="x")
        tk.Label(head, text="Game Lobby", font=("Arial", 20, "bold"), bg="#f5f5f5").pack(side="left")
        ttk.Button(head, text="Refresh", command=self.view_lobby).pack(side="right")
        
        cols = ("ID", "Game", "Host", "Status")
        tree = ttk.Treeview(self.content, columns=cols, show="headings", height=15)
        for c in cols: 
            tree.heading(c, text=c)
        tree.column("ID", width=60, anchor="center")
        tree.column("Status", width=100, anchor="center")
        tree.pack(fill="both", expand=True, pady=10)
        
        tree.bind("<Double-1>", lambda e: self.handle_join_check(tree))
        
        resp = self.service.get_room_list()
        self.room_cache = {} 
        
        if resp and resp.get('status') == 'success':
            for room in resp.get('data', []):
                self.room_cache[room['id']] = room
                tree.insert("", "end", values=(room['id'], room['game_name'], room['host'], room['status']))

    # --- Join Room ---
    def handle_join_check(self, tree):
        sel = tree.selection()
        if not sel: return
        room_id = int(tree.item(sel)['values'][0])
        
        room_info = self.room_cache.get(room_id)
        if not room_info: return
        
        game_id = room_info['game_id']
        game_name = room_info['game_name']
        
        game_path = os.path.join(DOWNLOAD_DIR, self.username, str(game_id))
        version_file = os.path.join(game_path, 'version.txt')
        
        # download check: not download => force download
        if not os.path.exists(game_path) or not os.path.exists(version_file):
            ans = messagebox.askyesno("Missing Game", f"Download '{game_name}' to join?")
            if ans:
                if self.service.download_game(game_id, game_path):
                    self.perform_join(room_id)
            return

        # version check: not newest => force update
        try:
            with open(version_file, 'r') as f:
                local_ver = int(f.read().strip())

            resp = self.service.get_game_details(game_id)
            if resp and resp['status'] == 'success':
                server_ver = resp['game']['version']
                if local_ver < server_ver:
                    ans = messagebox.askyesno("Update Required", "Version outdated. Update now?")
                    if ans:
                        if self.service.download_game(game_id, game_path):
                            self.perform_join(room_id)
                    return
        except:
            return
        # all pass => success join
        self.perform_join(room_id)
    
    # need to check handle before join room
    def perform_join(self, room_id):
        resp = self.service.join_room(room_id)
        if resp and resp['status'] == 'success':
            self.open_waiting_room(room_id, resp['game_id'], is_host=False)
        else:
            messagebox.showerror("Error", resp.get('msg', 'Full or Error'))

    def handle_create_room(self, game_id):
        resp = self.service.create_room(game_id)
        if resp and resp['status'] == 'success':
            self.open_waiting_room(resp['room_id'], game_id, is_host=True)
        else:
            messagebox.showerror("Error", "Create room failed")

    # --- Details Window ---
    def show_details_window(self, basic_info):
        resp = self.service.get_game_details(basic_info['id'])
        
        if resp and resp['status'] == 'success':
            game = resp['game']
            reviews = resp['reviews']
        else:
            game = basic_info
            reviews = []

        win = tk.Toplevel(self.root)
        win.title(game['name'])
        win.geometry("400x650")
        
        tk.Label(win, text=game['name'], font=("Arial", 18, "bold")).pack(pady=15)
        tk.Label(win, text=f"Version {game['version']} | {game['type']}", fg="gray").pack()
        tk.Message(win, text=game['description'], width=350).pack(pady=20)
        
        def do_download():
            path = os.path.join(DOWNLOAD_DIR, self.username, str(game['id']))
            if self.service.download_game(game['id'], path):
                win.destroy()
                self.view_library()
            else:
                messagebox.showerror("Error", "Download failed")

        ttk.Button(win, text="Download / Update", command=do_download).pack(pady=10)
        
        # Reviews
        tk.Label(win, text="Reviews:", font=("bold")).pack(anchor="w", padx=20, pady=(20, 5))
        review_frame = tk.Frame(win)
        review_frame.pack(fill="both", expand=True, padx=20)
        
        if not reviews:
            tk.Label(review_frame, text="No reviews yet.", fg="gray").pack()
        else:
            for r in reviews[-3:]: 
                f = tk.Frame(review_frame, pady=2)
                f.pack(fill="x")
                tk.Label(f, text=f"{r['user']} ({r['rating']}★):", font=("bold")).pack(anchor="w")
                tk.Label(f, text=r['comment'], wraplength=350, justify="left").pack(anchor="w")

        # Submit Review and review setting
        tk.Label(win, text="Write Review:", font=("bold")).pack(pady=(10,5))
        input_frame = tk.Frame(win)
        input_frame.pack(fill="x", padx=20)
        
        tk.Label(input_frame, text="Score:").pack(side="left")
        cbox = ttk.Combobox(input_frame, values=[1, 2, 3, 4, 5], width=3, state="readonly")
        cbox.set(5)
        cbox.pack(side="left", padx=5)
        
        entry = tk.Entry(input_frame)
        entry.pack(side="left", fill="x", expand=True)
        
        def do_review():
            try:
                score = int(cbox.get())
                resp = self.service.submit_review(game['id'], score, entry.get())
                if resp and resp['status'] == 'success':
                    messagebox.showinfo("Done", "Review submitted")
                    win.destroy()
                else:
                    msg = resp.get('msg', 'Error') if resp else 'Error'
                    messagebox.showerror("Error", msg)
            except: pass
            
        ttk.Button(win, text="Submit", command=do_review).pack(pady=10)

    # --- Waiting Room ---
    def open_waiting_room(self, room_id, game_id, is_host):
        win = tk.Toplevel(self.root)
        win.title(f"Room {room_id}")
        win.geometry("300x400")
        
        tk.Label(win, text=f"Room {room_id}", font=("Arial", 16, "bold")).pack(pady=10)
        lbl_status = tk.Label(win, text="Status: Waiting...", fg="blue")
        lbl_status.pack()
        
        lst = tk.Listbox(win)
        lst.pack(fill="both", expand=True, padx=20, pady=10)
        
        btn_start = ttk.Button(win, text="Start Game", state="disabled", command=lambda: self.service.start_game(room_id))
        if is_host: btn_start.pack(pady=5)
        
        def leave():
            self.service.leave_room(room_id)
            win.destroy()
            self.view_lobby()
        
        ttk.Button(win, text="Leave Room", command=leave).pack(pady=5)
        
        def poll():
            try:
                resp = self.service.get_room_info(room_id)
                if not resp or resp['status'] == 'fail': 
                    win.destroy()
                    return
                
                data = resp['data']
                lbl_status.config(text=f"Status: {data['status']}")
                lst.delete(0, tk.END)
                for p in data['players']: lst.insert(tk.END, p)
                
                if data['status'] == 'playing':
                    win.destroy()
                    self.launch_game_process(game_id, room_id)
                    return
                
                if is_host and len(data['players']) >= 2: 
                    btn_start.config(state="normal")
            except: pass
            
            if win.winfo_exists(): win.after(1000, poll)
        
        poll()

    def launch_game_process(self, game_id, room_id):
        path = os.path.join(DOWNLOAD_DIR, self.username, str(game_id))
        env = os.environ.copy()
        root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        env["PYTHONPATH"] = root_path + os.pathsep + env.get("PYTHONPATH", "")
        
        script_path = 'game.py'
        
        if sys.platform == "win32":
            cmd = f'start cmd /k "{sys.executable} {script_path} {self.username} {room_id}"'
            subprocess.Popen(cmd, cwd=path, env=env, shell=True)
        elif sys.platform == "darwin": 
            cmd = f'''osascript -e 'tell app "Terminal" to do script "{sys.executable} {os.path.join(path, script_path)} {self.username} {room_id}"' '''
            subprocess.Popen(cmd, cwd=path, env=env, shell=True)
        else: 
            cmd = [sys.executable, script_path, self.username, str(room_id)]
            try:
                subprocess.Popen(['x-terminal-emulator', '-e'] + cmd, cwd=path, env=env)
            except:
                try:
                    subprocess.Popen(['gnome-terminal', '--'] + cmd, cwd=path, env=env)
                except:
                    subprocess.Popen(cmd, cwd=path, env=env)

if __name__ == "__main__":
    root = tk.Tk()
    PlayerApp(root)
    root.mainloop()