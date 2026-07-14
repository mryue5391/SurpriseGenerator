import os
import time
import wave
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pygame
from mutagen.mp3 import MP3
from PIL import Image, ImageTk

from utils import get_resource_path
from hotkey import hotkey_listener

class SurpriseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Surprise 产生器v1.3 - created by MrYue_5391")
        self.root.resizable(False, False)
        
        self.style = ttk.Style()
        if "vista" in self.style.theme_names():
            self.style.theme_use("vista")
        elif "clam" in self.style.theme_names():
            self.style.theme_use("clam")

        self.img_path = ""
        self.snd_path = ""
        self.is_scheduled = False
        self.is_playing = False
        self.trigger_time = 0.0
        
        self.active_toasts = []

        self.setup_ui()

        self.hotkey_thread = threading.Thread(target=hotkey_listener, args=(self.on_hotkey_pressed,), daemon=True)
        self.hotkey_thread.start()

        self.root.after(50, self.tick_timer)

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.grid(row=0, column=0, sticky="nsew")

        group_settings = ttk.LabelFrame(main_frame, text=" 触发设定 ", padding="15 15 15 15")
        group_settings.grid(row=0, column=0, sticky="ew", pady=(0, 15))

        ttk.Label(group_settings, text="选项一 (图片):").grid(row=0, column=0, sticky='e', padx=(0, 10), pady=8)
        self.lbl_img_path = ttk.Label(group_settings, text="未选择任何图片", width=35, background="#f9f9f9", relief="sunken", padding=3)
        self.lbl_img_path.grid(row=0, column=1, sticky='w', pady=8)
        self.btn_img = ttk.Button(group_settings, text="浏览...", width=8, command=self.select_image)
        self.btn_img.grid(row=0, column=2, padx=(10, 0), pady=8)

        ttk.Label(group_settings, text="选项二 (声音):").grid(row=1, column=0, sticky='e', padx=(0, 10), pady=8)
        self.lbl_snd_path = ttk.Label(group_settings, text="未选择任何声音", width=35, background="#f9f9f9", relief="sunken", padding=3)
        self.lbl_snd_path.grid(row=1, column=1, sticky='w', pady=8)
        self.btn_snd = ttk.Button(group_settings, text="浏览...", width=8, command=self.select_sound)
        self.btn_snd.grid(row=1, column=2, padx=(10, 0), pady=8)

        ttk.Label(group_settings, text="触发延迟 (秒):").grid(row=2, column=0, sticky='e', padx=(0, 10), pady=8)
        delay_frame = ttk.Frame(group_settings)
        delay_frame.grid(row=2, column=1, columnspan=2, sticky='w', pady=8)
        self.entry_delay = ttk.Entry(delay_frame, width=15)
        self.entry_delay.pack(side='left')
        ttk.Label(delay_frame, text=" (最多两位小数)", foreground="gray").pack(side='left', padx=(5, 0))

        group_actions = ttk.Frame(main_frame)
        group_actions.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        self.btn_schedule = ttk.Button(group_actions, text="开始安排", width=15, command=self.schedule)
        self.btn_schedule.pack(side='left', padx=(0, 10))
        
        self.btn_cancel = ttk.Button(group_actions, text="取消安排", width=15, state='disabled', command=self.cancel)
        self.btn_cancel.pack(side='left', padx=(0, 10))

        self.btn_hide = ttk.Button(group_actions, text="隐藏至后台", command=self.hide_window)
        self.btn_hide.pack(side='right')

        ttk.Label(main_frame, text="提示: 隐藏后可随时按下 Ctrl + Shift + CapsLock 呼叫窗口", foreground="#888888", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=(0, 15))

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=3, column=0, sticky="ew")
        
        icon_path = get_resource_path(os.path.join("img", "icon.png"))
        try:
            img_icon = Image.open(icon_path).resize((32, 32))
            self.photo_icon = ImageTk.PhotoImage(img_icon)
            tk.Label(bottom_frame, image=self.photo_icon, borderwidth=0).pack(side='left')
        except Exception:
            pass

        self.lbl_countdown = ttk.Label(bottom_frame, text="剩余时间: -", font=("Arial", 14, "bold"), foreground="#333333")
        self.lbl_countdown.pack(side='right', pady=(5, 0))

    def show_toast(self, message):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.config(bg="#444444")
        
        lbl = tk.Label(toast, text=message, fg="white", bg="#444444", font=("Microsoft JhengHei", 10), padx=20, pady=10)
        lbl.pack()
        
        toast.update_idletasks()
        self.active_toasts.append(toast)
        self.reposition_toasts()
        
        def destroy_toast():
            if toast in self.active_toasts:
                self.active_toasts.remove(toast)
            if toast.winfo_exists():
                toast.destroy()
            self.reposition_toasts()
            
        toast.after(3000, destroy_toast)

    def reposition_toasts(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        base_y = screen_h - 80
        
        for i, toast in enumerate(reversed(self.active_toasts)):
            if toast.winfo_exists():
                w = toast.winfo_width()
                h = toast.winfo_height()
                x = screen_w - w - 20
                y = base_y - i * (h + 10) - h
                toast.geometry(f"+{x}+{y}")

    def select_image(self):
        path = filedialog.askopenfilename(title="选择图片", filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if not path: return
        if not path.lower().endswith(('.png', '.jpg', '.jpeg')):
            messagebox.showerror("错误", "仅支持 PNG 或 JPG/JPEG 格式")
            return
        self.img_path = path
        display_text = os.path.basename(path) if len(path) > 35 else path
        self.lbl_img_path.config(text=display_text)

    def select_sound(self):
        path = filedialog.askopenfilename(title="选择声音", filetypes=[("Audio", "*.wav *.mp3")])
        if not path: return
        ext = path.lower()
        if not (ext.endswith('.wav') or ext.endswith('.mp3')):
            messagebox.showerror("错误", "格式错误")
            return
        
        try:
            length = 0
            if ext.endswith('.mp3'):
                audio = MP3(path)
                length = audio.info.length
            else:
                with wave.open(path, 'r') as w:
                    length = w.getnframes() / float(w.getframerate())
            
            if length > 30:
                messagebox.showwarning("警告", "长度超过限制(最高30秒)")
                return
            
            self.snd_path = path
            display_text = os.path.basename(path) if len(path) > 35 else path
            self.lbl_snd_path.config(text=display_text)
        except Exception:
            messagebox.showerror("错误", "格式错误或无法解析此档案")

    def hide_window(self):
        self.root.withdraw()

    def on_hotkey_pressed(self):
        self.root.after_idle(self.show_window)

    def show_window(self):
        self.root.deiconify()
        self.root.attributes("-topmost", True)
        self.root.attributes("-topmost", False)

    def schedule(self):
        if not self.img_path and not self.snd_path:
            messagebox.showinfo("提示", "请至少选择一项")
            return
        
        delay_str = self.entry_delay.get().strip()
        if not delay_str:
            messagebox.showwarning("警告", "未填写延迟时间")
            return
        try:
            delay = float(delay_str)
            if delay < 0:
                raise ValueError
            if '.' in delay_str and len(delay_str.split('.')[1]) > 2:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "时间格式不正确")
            return

        self.set_ui_state('disabled')
        self.btn_schedule.config(state='disabled')
        self.btn_cancel.config(state='normal')
        
        self.trigger_time = time.time() + delay
        self.is_scheduled = True

        self.show_toast("已成功安排 Surprise")

    def cancel(self):
        self.is_scheduled = False
        self.lbl_countdown.config(text="剩余时间: -")
        
        self.set_ui_state('normal')
        self.btn_schedule.config(state='normal')
        self.btn_cancel.config(state='disabled')

        self.show_toast("计划的安排已取消")

    def set_ui_state(self, state):
        self.entry_delay.config(state=state)
        self.btn_img.config(state=state)
        self.btn_snd.config(state=state)

    def tick_timer(self):
        if self.is_scheduled and not self.is_playing:
            rem = self.trigger_time - time.time()
            if rem <= 0:
                self.lbl_countdown.config(text="剩余时间: 0.00 秒")
                self.is_scheduled = False
                self.trigger_surprise()
            else:
                self.lbl_countdown.config(text=f"剩余时间: {rem:.2f} 秒")
        self.root.after(50, self.tick_timer)

    def trigger_surprise(self):
        self.is_playing = True
        self.btn_cancel.config(state='disabled')

        has_img = bool(self.img_path)
        has_snd = bool(self.snd_path)

        if has_snd:
            try:
                pygame.mixer.music.load(self.snd_path)
                pygame.mixer.music.play()
            except Exception:
                pass

        if has_img:
            self.sw = tk.Toplevel(self.root)
            x, y = self.root.winfo_pointerx(), self.root.winfo_pointery()
            self.sw.geometry(f"+{x}+{y}")
            self.sw.attributes("-fullscreen", True)
            self.sw.attributes("-topmost", True)
            self.sw.config(bg='black')
            
            self.sw.update_idletasks()
            w, h = self.sw.winfo_width(), self.sw.winfo_height()
            if w <= 1:
                w, h = self.sw.winfo_screenwidth(), self.sw.winfo_screenheight()

            try:
                img = Image.open(self.img_path).resize((w, h), Image.Resampling.LANCZOS)
                self.photo_surprise = ImageTk.PhotoImage(img)
                
                canvas = tk.Canvas(self.sw, width=w, height=h, highlightthickness=0, bg='black')
                canvas.pack(fill='both', expand=True)
                canvas.create_image(w//2, h//2, image=self.photo_surprise, anchor='center')
                
                btn_close = tk.Button(self.sw, text="X", font=("Arial", 16, "bold"), fg="#1e1e1e", bg="#eeeeee", activebackground="#ff4444", activeforeground="white", borderwidth=0, command=self.end_surprise)
                btn_close.place(relx=1.0, rely=0.0, anchor='ne')
            except Exception:
                self.sw.destroy()
                self.sw = None
                has_img = False

        if has_snd:
            self.check_playback()
        elif has_img and not has_snd:
            self.root.after(5000, self.end_surprise)
        else:
            self.end_surprise()

    def check_playback(self):
        if not self.is_playing: return
        if not pygame.mixer.music.get_busy():
            self.end_surprise()
        else:
            self.root.after(100, self.check_playback)

    def end_surprise(self):
        if not self.is_playing: return
        self.is_playing = False
        
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            
        if hasattr(self, 'sw') and self.sw is not None:
            if self.sw.winfo_exists():
                self.sw.destroy()
            self.sw = None

        self.set_ui_state('normal')
        self.btn_schedule.config(state='normal')
        self.lbl_countdown.config(text="剩余时间: -")
