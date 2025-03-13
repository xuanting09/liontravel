import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class LoginApp:
    def __init__(self, on_successful_login):
        self.login_window = tk.Tk()
        self.login_window.title("雄獅旅遊 登入系統")
        self.login_window.geometry('300x200')  
        
        self.on_successful_login = on_successful_login
        
        self.login_window.columnconfigure(0, weight=1)
        self.login_window.columnconfigure(1, weight=2)
        
        # 使用者名稱
        ttk.Label(self.login_window, text="使用者名稱:").grid(column=0, row=0, padx=5, pady=5, sticky='e')
        self.username_entry = ttk.Entry(self.login_window)
        self.username_entry.grid(column=1, row=0, padx=5, pady=5, sticky='ew')
        
        # 密碼
        ttk.Label(self.login_window, text="密碼:").grid(column=0, row=1, padx=5, pady=5, sticky='e')
        self.password_entry = ttk.Entry(self.login_window, show="*")
        self.password_entry.grid(column=1, row=1, padx=5, pady=5, sticky='ew')
        
        # 按鈕框架
        button_frame = ttk.Frame(self.login_window)
        button_frame.grid(column=0, row=2, columnspan=2, pady=10)
        
        # 登入按鈕
        login_button = ttk.Button(button_frame, text="登入", command=self.login)
        login_button.pack(side=tk.LEFT, padx=5)
        
        # 註冊按鈕
        register_button = ttk.Button(button_frame, text="註冊新帳號", command=self.open_register)
        register_button.pack(side=tk.LEFT, padx=5)
        
        # 建立或載入使用者資料檔案
        self.users_file = 'users.json'
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
        
        self.login_window.mainloop()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        # 從檔案讀取使用者資料
        with open(self.users_file, 'r') as f:
            users = json.load(f)
        
        if username in users and users[username] == password:
            self.login_window.destroy()
            if self.on_successful_login:
                self.on_successful_login()
        else:
            messagebox.showerror("錯誤", "使用者名稱或密碼錯誤！")
    
    def open_register(self):
        RegisterWindow(self)

class RegisterWindow:
    def __init__(self, login_app):
        self.login_app = login_app
        self.register_window = tk.Toplevel()
        self.register_window.title("註冊新帳號")
        self.register_window.geometry('300x250')
        
        # 設定網格配置
        self.register_window.columnconfigure(0, weight=1)
        self.register_window.columnconfigure(1, weight=2)
        
        # 使用者名稱
        ttk.Label(self.register_window, text="使用者名稱:").grid(column=0, row=0, padx=5, pady=5, sticky='e')
        self.username_entry = ttk.Entry(self.register_window)
        self.username_entry.grid(column=1, row=0, padx=5, pady=5, sticky='ew')
        
        # 密碼
        ttk.Label(self.register_window, text="密碼:").grid(column=0, row=1, padx=5, pady=5, sticky='e')
        self.password_entry = ttk.Entry(self.register_window, show="*")
        self.password_entry.grid(column=1, row=1, padx=5, pady=5, sticky='ew')
        
        # 確認密碼
        ttk.Label(self.register_window, text="確認密碼:").grid(column=0, row=2, padx=5, pady=5, sticky='e')
        self.confirm_password_entry = ttk.Entry(self.register_window, show="*")
        self.confirm_password_entry.grid(column=1, row=2, padx=5, pady=5, sticky='ew')
        
        # 註冊按鈕
        register_button = ttk.Button(self.register_window, text="註冊", command=self.register)
        register_button.grid(column=0, row=3, columnspan=2, pady=20)
    
    def register(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()
        
        if not username or not password:
            messagebox.showerror("錯誤", "使用者名稱和密碼不能為空！")
            return
        
        if password != confirm_password:
            messagebox.showerror("錯誤", "兩次輸入的密碼不相同！")
            return
        
        # 從檔案讀取現有使用者資料
        with open(self.login_app.users_file, 'r') as f:
            users = json.load(f)
        
        # 檢查使用者名稱是否已存在
        if username in users:
            messagebox.showerror("錯誤", "此使用者名稱已被使用！")
            return
        
        # 儲存新使用者資料
        users[username] = password
        with open(self.login_app.users_file, 'w') as f:
            json.dump(users, f)
        
        messagebox.showinfo("成功", "註冊成功！")
        self.register_window.destroy()