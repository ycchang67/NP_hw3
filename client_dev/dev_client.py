import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import socket
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.protocol import send_json, recv_json, send_file

HOST = 'linux3.cs.nycu.edu.tw'
PORT = 12131

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
            'role': 'dev',
            'username': username,
            'password': password
        })

    def register(self, username, password):
        return self._send_command({
            'command': 'register',
            'role': 'dev',
            'username': username,
            'password': password
        })

    def get_my_games(self, username):
        response = self._send_command({'command': 'list_games'})
        if response and response['status'] == 'success':
            my_games = []
            for game in response['data']:
                if game['author'] == username:
                    my_games.append(game)
            return my_games
        return []

    def delete_game(self, game_id):
        return self._send_command({'command': 'remove_game', 'game_id': game_id})

    def get_game_reviews(self, game_id):
        return self._send_command({'command': 'get_game_details', 'game_id': game_id})

    def upload_game(self, metadata, file_path):
        response = self._send_command({'command': 'upload_game', 'meta': metadata})
        
        if response and response['status'] == 'ready':
            if send_file(self.socket, file_path):
                return recv_json(self.socket) 
            else:
                return {'status': 'fail', 'msg': 'File transfer failed'}
        
        return response

# ====UI ==============================
COLORS = {
    "bg_dark": "#2c3e50", "bg_light": "#ecf0f1", "primary": "#2980b9",
    "success": "#27ae60", "danger": "#c0392b", "text": "#2c3e50", "white": "#ffffff"
}

class DeveloperApp:
    def __init__(self, root_window):
        self.root = root_window
        self.root.title("Game Store - Developer Studio")
        self.root.geometry("1000x650")
        self.root.config(cursor="left_ptr")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_styles()
        self.service = GameStoreService()
        self.username = None
        
        self.init_login_ui()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background=COLORS["bg_light"])
        self.style.configure("TLabel", background=COLORS["bg_light"], foreground=COLORS["text"], font=("Arial", 11))
        self.style.configure("Header.TLabel", font=("Helvetica", 24, "bold"), background=COLORS["bg_light"], foreground=COLORS["bg_dark"])
        self.style.configure("SubHeader.TLabel", font=("Helvetica", 12, "bold"), background=COLORS["white"], foreground=COLORS["text"])
        self.style.configure("Treeview", rowheight=30, font=('Arial', 10), background="white", fieldbackground="white")
        self.style.configure("Treeview.Heading", font=('Arial', 11, 'bold'), background="#bdc3c7", foreground=COLORS["text"])
        self.style.map("Treeview", background=[('selected', COLORS["primary"])])
        self.style.configure("TButton", font=("Arial", 10, "bold"), padding=8, borderwidth=0)
        self.style.map("TButton", background=[('active', '#3498db')])
        self.style.configure("Action.TButton", background=COLORS["primary"], foreground="white")
        self.style.configure("Success.TButton", background=COLORS["success"], foreground="white")
        self.style.configure("Danger.TButton", background=COLORS["danger"], foreground="white")

    def safe_alert(self, alert_type, title, message):
        try:
            if not self.root.winfo_exists(): 
                return
            if alert_type == "error": 
                messagebox.showerror(title, message)
            elif alert_type == "warning": 
                messagebox.showwarning(title, message)
            elif alert_type == "info": 
                messagebox.showinfo(title, message)
            elif alert_type == "askyesno": 
                return messagebox.askyesno(title, message)
        except: pass

    def on_close(self):
        self.service.close()
        try: 
            self.root.destroy()
        except: 
            pass
    # login ====== page 1 =========
    def init_login_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        self.root.configure(bg = COLORS["bg_dark"])

        frame = tk.Frame(self.root, bg = "white", padx = 50, pady = 50)
        frame.place(relx = 0.5, rely = 0.5, anchor="center")
        tk.Label(frame, text="Developer Studio", font=("Helvetica", 24, "bold"), bg="white", fg=COLORS["bg_dark"]).pack(pady=(0, 30))
        tk.Label(frame, text="Username", bg="white", anchor="w").pack(fill="x")
        self.entry_user = ttk.Entry(frame, width=30, font=("Arial", 12))
        self.entry_user.pack(fill="x", pady=(5, 15))
        
        tk.Label(frame, text="Password", bg="white", anchor="w").pack(fill="x")
        self.entry_pass = ttk.Entry(frame, width=30, font=("Arial", 12), show="*")
        self.entry_pass.pack(fill="x", pady=(5, 20))

        ttk.Button(frame, text="LOGIN", style="Action.TButton", command=self.handle_login).pack(fill="x", pady=5)
        ttk.Button(frame, text="REGISTER", command=self.handle_register).pack(fill="x")

    def handle_login(self):
        if not self.service.connect():
            return self.safe_alert("error", "Error", "Cannot connect to server")
            
        resp = self.service.login(self.entry_user.get(), self.entry_pass.get())
        if resp and resp['status'] == 'success':
            self.username = self.entry_user.get()
            self.init_main_ui()
        else:
            msg = resp['msg'] if resp else "Login failed"
            self.safe_alert("error", "Error", msg)
            self.service.close()

    def handle_register(self):
        if not self.service.connect():
            return self.safe_alert("error", "Error", "Cannot connect to server")
            
        resp = self.service.register(self.entry_user.get(), self.entry_pass.get())
        if resp and resp['status'] == 'success':
            self.safe_alert("info", "Success", "Registered! Please login.")
        else:
            msg = resp['msg'] if resp else "Register Failed"
            self.safe_alert("error", "Error", msg)
        self.service.close()

    # pure UI
    # --- Main Dashboard ---
    def init_main_ui(self):
        for w in self.root.winfo_children(): w.destroy()
        self.root.configure(bg=COLORS["bg_light"])

        # Sidebar
        sidebar = tk.Frame(self.root, bg=COLORS["bg_dark"], width=240)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        tk.Label(sidebar, text="DEV PORTAL", bg=COLORS["bg_dark"], fg="white", font=("Helvetica", 20, "bold")).pack(pady=(40, 10))
        tk.Label(sidebar, text=f"User: {self.username}", bg=COLORS["bg_dark"], fg="#95a5a6", font=("Arial", 10)).pack(pady=(0, 40))
        
        def nav(txt, cmd, col=COLORS["bg_dark"]): # navagation make darker
            tk.Button(sidebar, text=txt, command=cmd, bg=col, fg="white", font=("Arial", 12), bd=0, pady=12, anchor="w", padx=20).pack(fill="x", pady=1)
            
        nav("My Games", self.view_my_games)
        nav("Upload New Game", self.view_upload_new)
        
        tk.Frame(sidebar, bg=COLORS["bg_dark"]).pack(fill="y", expand=True)
        nav("Logout", lambda: [self.service.close(), self.init_login_ui()], "#c0392b")

        # Content
        self.content = ttk.Frame(self.root, style="TFrame")
        self.content.pack(side="right", fill="both", expand=True, padx=40, pady=40)
        self.view_my_games()
    # clear
    def clear_content(self):
        for w in self.content.winfo_children(): w.destroy()


    # After Login === page 2 =======
    # --- view my hames ---
    def view_my_games(self):
        self.clear_content()
        
        head = ttk.Frame(self.content)
        head.pack(fill="x", pady=(0, 20))
        ttk.Label(head, text="My Games Library", style="Header.TLabel").pack(side="left")
        ttk.Button(head, text="Refresh", command=lambda: self.refresh_table(tree)).pack(side="right")

        cols = ("ID", "Name", "Ver", "Type", "Rating", "Desc")
        tree = ttk.Treeview(self.content, columns=cols, show="headings", height=12)
        
        tree.heading("ID", text="ID"); tree.column("ID", width=50, anchor="center")
        tree.heading("Name", text="Name"); tree.column("Name", width=180)
        tree.heading("Ver", text="Ver"); tree.column("Ver", width=50, anchor="center")
        tree.heading("Type", text="Type"); tree.column("Type", width=80, anchor="center")
        tree.heading("Rating", text="Rating"); tree.column("Rating", width=60, anchor="center")
        tree.heading("Desc", text="Description"); tree.column("Desc", width=250)
        tree.pack(fill="both", expand=True)
        
        actions = ttk.Frame(self.content)
        actions.pack(fill="x", pady=20)
        
        def check_sel():
            sel = tree.selection()
            if not sel: 
                self.safe_alert("warning", "Select Game", "Please select a game first.")
                return None
            return tree.item(sel[0])['values']

        def on_update():
            item = check_sel()
            if item: self.open_update_window(item)

        def on_review():
            item = check_sel()
            if item: self.open_reviews_window(item[0], item[1])

        def on_delete():
            item = check_sel()
            if item:
                gid = item[0]
                if self.safe_alert("askyesno", "Confirm", f"Delete Game ID {gid}?"):
                    resp = self.service.delete_game(gid)
                    if resp: self.safe_alert("info", "Info", resp.get('msg'))
                    self.refresh_table(tree)

        ttk.Button(actions, text="View Reviews", style="Action.TButton", command=on_review).pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="Update Version", style="Success.TButton", command=on_update).pack(side="left", padx=(0, 10))
        ttk.Button(actions, text="Delete Game", style="Danger.TButton", command=on_delete).pack(side="right")

        self.refresh_table(tree)

    # refresh 
    def refresh_table(self, tree):
        for item in tree.get_children(): tree.delete(item)
        
        games = self.service.get_my_games(self.username)
        for g in games:
            tree.insert("", "end", values=(g['id'], g['name'], g['version'], g['type'], g.get('rating', 0.0), g['description']))

    # --- upload / new ---
    def view_upload_new(self):
        self.clear_content()
        ttk.Label(self.content, text="Upload New Game", style="Header.TLabel").pack(anchor="w", pady=(0, 30))
        self.render_upload_form(self.content, is_update=False)

    def open_update_window(self, item):
        gid, name, ver, gtype, rate, desc = item
        try:
            win = tk.Toplevel(self.root)
            win.title(f"Update: {name}")
            win.geometry("500x450")
            win.configure(bg="white")
            
            tk.Label(win, text="Update Game Version", font=("Helvetica", 16, "bold"), bg="white", fg=COLORS["primary"]).pack(pady=20)
            self.render_upload_form(win, is_update=True, default_name=name, default_desc=desc, default_type=gtype, old_ver=ver)
        except: pass

    def render_upload_form(self, parent, is_update=False, default_name="", default_desc="", default_type="GUI", old_ver=0):
        form = tk.Frame(parent, bg="white" if is_update else COLORS["bg_light"], padx=20)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Game Name", font=("bold")).pack(anchor="w")
        ent_name = ttk.Entry(form, width=40)
        ent_name.insert(0, default_name)
        if is_update: 
            ent_name.config(state="disabled")
        ent_name.pack(anchor="w", pady=(0, 15))

        tk.Label(form, text="Description", font=("bold")).pack(anchor="w")
        ent_desc = ttk.Entry(form, width=40)
        ent_desc.insert(0, default_desc)
        ent_desc.pack(anchor="w", pady=(0, 15))

        tk.Label(form, text="Type", font=("bold")).pack(anchor="w")
        cbox = ttk.Combobox(form, values=["GUI", "CLI"], state="readonly")
        cbox.set(default_type)
        cbox.pack(anchor="w", pady=(0, 15))

        tk.Label(form, text="Game File (.py)", font=("bold")).pack(anchor="w")
        
        file_area = tk.Frame(form)
        file_area.pack(fill="x", pady=(0, 20))
        lbl_file = tk.Label(file_area, text="No file selected", bg="#ecf0f1", width=30, anchor="w", relief="sunken")
        lbl_file.pack(side="left", ipady=5, fill="x", expand=True)
        
        path_var = tk.StringVar()

        # browse 
        def browse():
            f = filedialog.askopenfilename(filetypes=[("Python", "*.py")])
            if f:
                path_var.set(f)
                lbl_file.config(text=os.path.basename(f))

        ttk.Button(file_area, text="Browse", command=browse).pack(side="left", padx=5)


        # summit
        def submit():
            if not path_var.get() or not ent_name.get():
                self.safe_alert("warning", "Incomplete", "Please fill all fields.")
                return
            
            meta = {"name": ent_name.get(), "description": ent_desc.get(), "type": cbox.get()}
            resp = self.service.upload_game(meta, path_var.get())
            
            if resp and resp.get('status') == 'success':
                if is_update:
                    msg = f"Updated to v{old_ver+1}" 
                else :
                    msg = "Upload complete"

                self.safe_alert("info", "Success", msg)
                if is_update: 
                    parent.master.destroy() # Close popup
                    self.refresh_table(self.content.winfo_children()[1]) # Refresh list if possible
                else:
                    self.view_my_games()
            else:
                self.safe_alert("error", "Error", resp.get('msg', 'Failed'))

        btn_txt = "Confirm Update" if is_update else "Publish to Store"
        btn_style = "Success.TButton" if is_update else "Action.TButton"
        ttk.Button(form, text=btn_txt, style=btn_style, command=submit).pack(fill="x", pady=10)

    # --- Reviews ---
    def open_reviews_window(self, gid, name):
        resp = self.service.get_game_reviews(gid)
        if not resp or resp['status'] != 'success': return
        
        reviews = resp.get('reviews', [])
        
        try:
            win = tk.Toplevel(self.root)
            win.title(f"Reviews: {name}")
            win.geometry("500x600")
            win.configure(bg="white")
            
            tk.Label(win, text=f"{name}", font=("Helvetica", 18, "bold"), bg="white").pack(pady=20)
            
            avg = 0
            if reviews: avg = sum(r['rating'] for r in reviews) / len(reviews)
            tk.Label(win, text=f"Rating: {avg:.1f} / 5.0  ({len(reviews)} reviews)", fg="#f39c12", bg="white", font=("Arial", 12)).pack()
            
            list_frame = tk.Frame(win)
            list_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            if not reviews:
                tk.Label(list_frame, text="No reviews yet.").pack()
            else:
                for r in reviews:
                    card = tk.Frame(list_frame, bd=1, relief="solid", padx=10, pady=5)
                    card.pack(fill="x", pady=5)
                    tk.Label(card, text=f"{r['user']} ({r['rating']}★)", font=("bold")).pack(anchor="w")
                    tk.Label(card, text=r['comment'], fg="gray", anchor="w").pack(fill="x")
        except: pass

if __name__ == "__main__":
    root = tk.Tk()
    app = DeveloperApp(root)
    root.mainloop()