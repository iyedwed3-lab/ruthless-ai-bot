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
# MEMORY SYSTEMS
# =====================
user_memory = {}      # ذاكرة لكل مستخدم
chat_history = {}     # آخر محادثات

MAX_HISTORY = 6

# =====================
# SERVER RULES (LOCKED AI)
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

SYSTEM_PROMPT = f"""
You are Vortex AI inside the RUTHLESS Discord server.

STRICT RULES:
- You MUST ONLY use SERVER INFO below
- If answer is not inside SERVER INFO, say:
"I don't have enough information about that in the RUTHLESS system."

- Do NOT give general internet explanations.

SERVER INFO:
{SERVER_CONTEXT}
"""

# =====================
# AI CALL
# =====================
def ask_ai(user_id, text):
    url = "https://openrouter.ai/api/v1/chat/completions"

    # =====================
    # BUILD MEMORY CONTEXT
    # =====================
    memory = user_memory.get(user_id, "")

    history = chat_history.get(user_id, [])

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # إضافة ذاكرة المستخدم
    if memory:
        messages.append({"role": "system", "content": f"User memory: {memory}"})

    # إضافة آخر المحادثات
    for msg in history:
        messages.append(msg)

    # الرسالة الحالية
    messages.append({"role": "user", "content": text})

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ruthless-ai-bot.onrender.com",
        "X-Title": "Vortex"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages
    }

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)

        data = r.json()

        if r.status_code != 200:
            return None

        if "choices" not in data:
            return None

        reply = data["choices"][0]["message"]["content"]

        # =====================
        # SAVE MEMORY
        # =====================
        chat_history.setdefault(user_id, []).append(
            {"role": "user", "content": text}
        )
        chat_history[user_id].append(
            {"role": "assistant", "content": reply}
        )

        # limit history
        if len(chat_history[user_id]) > MAX_HISTORY:
            chat_history[user_id] = chat_history[user_id][-MAX_HISTORY:]

        # simple memory update
        user_memory[user_id] = f"User recently talked about: {text}"

        return reply

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

        reply = ask_ai(message.author.id, text)

        if reply is None:
            reply = fallback()

        await message.reply(reply)

# =====================
# START
# =====================
keep_alive()
client.run(TOKEN)
