import discord
import os
import requests
import time
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
# SERVER CONTEXT
# =====================
SERVER_CONTEXT = """
RUTHLESS is a competitive Discord server.

POINT SYSTEM:
- Daily challenges give points
- Weekly missions give bonus points
- Special events give rare points

Seasons reset every 2 weeks.
Fake proof = ban or punishment.
No spam, cheating, or drama.
"""

# =====================
# SYSTEM PROMPT (BALANCED)
# =====================
SYSTEM_PROMPT = f"""
You are Vortex, a smart AI assistant inside the RUTHLESS Discord server.

PERSONALITY:
- Friendly, natural, and helpful
- Can answer normal greetings and casual chat freely
- Can explain who you are when asked

RULES:
- Use SERVER INFO only for server-specific questions (points, rules, seasons)
- If question is about RUTHLESS and not in SERVER INFO, say:
"I don't have enough information about that in the RUTHLESS system."

- Do NOT invent server features

SERVER INFO:
{SERVER_CONTEXT}

ABOUT YOU:
- You were created by Iyeed
- You are a smart assistant for the server and its members
- You help users with server-related and general questions
"""

# =====================
# SIMPLE QUICK RESPONSES (IMPORTANT)
# =====================
def quick_reply(text):
    t = text.lower()

    # greetings (كل أنواع الترحيب)
    greetings = ["hi", "hello", "hey", "yo", "sup", "good morning", "good evening"]
    if any(g in t for g in greetings):
        return "Hello! 👋 I'm Vortex, your assistant for the RUTHLESS server. How can I help you?"

    # identity questions
    if "who are you" in t or "what are you" in t or "what do you do" in t:
        return (
            "I'm Vortex, a smart AI assistant created by Iyeed for the RUTHLESS Discord server.\n"
            "I help members with server info, points, and general questions."
        )

    return None

# =====================
# AI CALL
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
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        data = r.json()

        if r.status_code != 200:
            return None

        if "choices" not in data:
            return None

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        print("ERROR:", str(e))
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
    if not text:
        return

    async with message.channel.typing():

        # =====================
        # 1. QUICK RESPONSES FIRST
        # =====================
        quick = quick_reply(text)
        if quick:
            await message.reply(quick)
            return

        # =====================
        # 2. AI IF NOT QUICK
        # =====================
        reply = ask_ai(text)

        if reply is None:
            reply = fallback()

        await message.reply(reply)

# =====================
# START
# =====================
keep_alive()
client.run(TOKEN)
