import sys
import tkinter as tk
from tkinter import messagebox
import pygame

from utils import check_admin, check_single_instance
from ui import SurpriseApp

if __name__ == "__main__":
    if not check_admin():
        tmp = tk.Tk()
        tmp.withdraw()
        messagebox.showwarning("警告", "请使用管理员身份运行该程序")
        tmp.destroy()
        sys.exit(0)

    if not check_single_instance():
        tmp = tk.Tk()
        tmp.withdraw()
        messagebox.showwarning("警告", "已经有一个程序在运行中")
        tmp.destroy()
        sys.exit(0)

    pygame.mixer.init()
    
    root = tk.Tk()
    app = SurpriseApp(root)
    root.mainloop()