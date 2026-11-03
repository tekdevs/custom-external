import tkinter as tk
from tkinter import scrolledtext
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
import api

class SimpleEditor:
    def __init__(self):
        self.win = tk.Tk()
        self.win.title("Tutorial - Not Attached")
        self.win.geometry("700x500")
        self.win.resizable(False, False)
        self.win.configure(bg="#1e1e1e")
        
        self.pm = None
        self.funcs = None
        
        editor_frame = tk.Frame(self.win, bg="#1e1e1e")
        editor_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.editor = scrolledtext.ScrolledText(
            editor_frame,
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff",
            font=("Consolas", 10),
            padx=5,
            pady=5,
            relief="flat",
            bd=0,
            undo=True
        )
        self.editor.pack(fill="both", expand=True)
        
        button_frame = tk.Frame(self.win, bg="#1e1e1e")
        button_frame.pack(fill="x", padx=5, pady=(0, 5))
        
        btn_style = {
            "bg": "#2d2d2d",
            "fg": "#cccccc",
            "font": ("Consolas", 10),
            "relief": "flat",
            "width": 10
        }
        
        tk.Button(button_frame, text="Execute", command=self.execute, **btn_style).pack(side="left", padx=2)
        tk.Button(button_frame, text="Kill", command=self.kill_roblox, **btn_style).pack(side="left", padx=2)
        tk.Button(button_frame, text="Clear", command=self.clear, **btn_style).pack(side="left", padx=2)
        
        self.console = tk.Text(
            self.win,
            height=6,
            bg="#2d2d2d",
            fg="#888888",
            font=("Consolas", 9),
            relief="flat",
            padx=5,
            pady=5,
            state='disabled'
        )
        self.console.pack(fill="x", padx=5, pady=(0, 5))
        
        self.console.tag_configure("normal", foreground="#888888")
        self.console.tag_configure("error", foreground="#ff4444")
        self.console.tag_configure("success", foreground="#4ec9b0")
        
        self.attach()
    
    def log(self, msg, msg_type="normal"):
        self.console.config(state='normal')
        self.console.insert(tk.END, msg + "\n", msg_type)
        self.console.see(tk.END)
        self.console.config(state='disabled')
    
    def attach(self):
        try:
            self.pm = api.attach_to_roblox()
            self.funcs = api.MemFunctions(self.pm)
            self.log(f"Attached to Roblox (Base: 0x{self.pm.base_address:X})", "success")
            self.win.title("Tutorial - Attached")
        except Exception as e:
            self.log(f"Not attached: {str(e)}", "error")
    
    def execute(self):
        if not self.pm:
            self.log("Not attached to Roblox!", "error")
            return
        
        code = self.editor.get("1.0", tk.END).strip()
        if not code:
            return
        
        try:
            namespace = {
                "speed": self.funcs.speed,
                "noclip": self.funcs.noclip,
                "fov": self.funcs.fov,
                "gravity": self.funcs.gravity,
                "fullbright": self.funcs.fullbright,
                "gethealth": self.funcs.gethealth,
                "getpos": self.funcs.getpos,
                "userid": self.funcs.userid,
                "accountage": self.funcs.accountage,
                "print": lambda *args: self.log(" ".join(map(str, args)), "normal")
            }
            
            exec(code, namespace)
        except Exception as e:
            self.log(f"Error: {str(e)}", "error")
    
    def kill_roblox(self):
        try:
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "RobloxPlayerBeta.exe"], capture_output=True)
            self.log("Killed Roblox", "normal")
            self.win.title("Tutorial - Not Attached")
            self.pm = None
            self.funcs = None
        except Exception as e:
            self.log(f"Kill error: {str(e)}", "error")
    
    def clear(self):
        self.editor.delete("1.0", tk.END)
    
    def start(self):
        self.win.mainloop()

if __name__ == "__main__":
    app = SimpleEditor()
    app.start()
