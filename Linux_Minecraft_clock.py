import tkinter as tk
from PIL import Image, ImageTk
import datetime
import os
import sys

IS_WINDOWS = sys.platform.startswith("win")

if IS_WINDOWS:
    import ctypes
    import win32gui
    import win32con

TOTAL_IMAGES = 63
IMAGES_PATH = "frames"
ICON_FILENAME = "icon.png"  # Use a PNG icon for cross-platform support

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def set_win_taskbar_icon(window, icon_path):
    """Force taskbar + Alt+Tab icon (replaces feather) using WinAPI"""
    hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
    if os.path.exists(icon_path):
        hicon = ctypes.windll.user32.LoadImageW(
            0, icon_path, 1, 0, 0, 0x00000010  # IMAGE_ICON, LR_LOADFROMFILE
        )
        if hicon:
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 1, hicon)  # small icon
            ctypes.windll.user32.SendMessageW(hwnd, 0x80, 0, hicon)  # big icon

def minutes_since_noon(hour, minute):
    if hour < 12:
        hour += 24
    return (hour - 12) * 60 + minute

def get_image_index(hour, minute):
    minutes = minutes_since_noon(hour, minute)
    index = int(minutes // (720 / (TOTAL_IMAGES / 2))) % TOTAL_IMAGES
    return index

class MinecraftClockApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure window
        self.geometry("300x300+100+100")
        self.title("Minecraft Clock")
        self.configure(bg="white")
        self.wm_attributes("-topmost", True)

        if IS_WINDOWS:
            # Windows-specific settings
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"minecraft.clock.app")
            icon_path = resource_path(ICON_FILENAME)
            set_win_taskbar_icon(self, icon_path)
            self.wm_attributes("-transparentcolor", "white")
            self.after(100, self.set_taskbar_window)
        else:
            # Linux/Mac icon setting
            icon_path = resource_path(ICON_FILENAME)
            if os.path.exists(icon_path):
                try:
                    icon_img = tk.PhotoImage(file=icon_path)
                    self.iconphoto(False, icon_img)
                except Exception as e:
                    print(f"Failed to load icon: {e}")

        # Label to show image
        self.label = tk.Label(self, bg="white")
        self.label.pack(fill="both", expand=True)

        # Enable dragging
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)

        # Right-click to exit
        self.bind("<Button-3>", lambda e: self.destroy())

        # Load image and update regularly
        self.update_image()
        self.after(10000, self.periodic_update)

    def set_taskbar_window(self):
        if not IS_WINDOWS:
            return
        hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        style &= ~win32con.WS_OVERLAPPEDWINDOW
        style |= win32con.WS_POPUP | win32con.WS_VISIBLE
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)

        exStyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        exStyle |= win32con.WS_EX_APPWINDOW
        exStyle &= ~win32con.WS_EX_TOOLWINDOW
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, exStyle)

        win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 100, 100, 300, 300,
                              win32con.SWP_FRAMECHANGED | win32con.SWP_SHOWWINDOW)

    def update_image(self):
        now = datetime.datetime.now()
        idx = get_image_index(now.hour, now.minute)
        frame_path = resource_path(os.path.join(IMAGES_PATH, f"frame_{idx}.png"))

        if os.path.exists(frame_path):
            img = Image.open(frame_path).resize((300, 300), Image.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            self.label.configure(image=self.tk_img)
        else:
            self.label.configure(text=f"Missing frame_{idx}.png", image='', bg='white')

    def periodic_update(self):
        self.update_image()
        self.after(10000, self.periodic_update)

    def start_move(self, event):
        self._x = event.x
        self._y = event.y

    def do_move(self, event):
        x = self.winfo_pointerx() - self._x
        y = self.winfo_pointery() - self._y
        self.geometry(f"+{x}+{y}")

if __name__ == "__main__":
    app = MinecraftClockApp()
    app.mainloop()
