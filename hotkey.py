import ctypes
from ctypes import wintypes

def hotkey_listener(callback):
    user32 = ctypes.windll.user32
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    VK_CAPITAL = 0x14
    HOTKEY_ID = 1

    if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_CAPITAL):
        return

    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == 0x0312:
            callback()
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))