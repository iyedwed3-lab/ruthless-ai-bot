import discord
import os
import requests
import time
import numpy as np
from flask import Flask
from threading import Thread

# =====================
# ENV
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# =====================
# KEEP ALIVE
# =====================
app = Flask("")

@app.route("/")
def home():
    return "Vortex is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

# =====================
# DISCORD
# =====================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =====================
# SYSTEM PROMPT
# =====================
SYSTEM_PROMPT = """
You are Vortex AI.
Always respond in English.
Be helpful and short.
"""

# =====================
# AI CALL (FIXED)
# =====================
def ask_ai(text):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ruthless-ai-bot.onrender.com",
        "X-Title": "Vortex"
    }

    payload = {
        "model": "openai/gpt-4o-mini",  # ← هذا الأكثر استقراراً
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)

        print("STATUS:", r.status_code)
        print("RESPONSE:", r.text)

        data = r.json()

        if r.status_code != 200:
            return None

        if "error" in data:
            print("OPENROUTER ERROR:", data["error"])
            return None

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("REQUEST FAILED:", str(e))
        return None

# =====================
# FALLBACK
# =====================
def fallback():
    return "⚡ AI temporarily unavailable. Try again."

# =====================
# EVENTS
# =====================
@client.event
async def on_ready():
    print("Bot online:", client.user)

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != CHANNEL_ID:
        return

    text = message.content.strip()

    async with message.channel.typing():
        reply = ask_ai(text)

        if reply is None:
            reply = fallback()

        await message.reply(reply)

# =====================
# START
# =====================
keep_alive()
client.run(TOKEN)
