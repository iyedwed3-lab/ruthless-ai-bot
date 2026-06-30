import discord
import os
import requests
from flask import Flask
from threading import Thread

# =====================
# ENV VARIABLES
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# =====================
# FLASK KEEP ALIVE (Render)
# =====================
app = Flask("")

@app.route("/")
def home():
    return "RUTHLESS AI Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# =====================
# DISCORD BOT SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =====================
# SERVER CONTEXT
# =====================
SERVER_CONTEXT = """
You are the official AI assistant for the Discord server: RUTHLESS.

Rules:
- Answer only in English
- Use only provided server information
- If unknown, say you don't know
"""

# =====================
# GEMINI FUNCTION (FIXED)
# =====================
def ask_gemini(user_input):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
You are a strict Discord server assistant.

SERVER INFO:
{SERVER_CONTEXT}

User question:
{user_input}
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload)

        # 🔴 DEBUG (IMPORTANT)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        data = response.json()

        # ❌ If API returns error
        if "error" in data:
            return f"API Error: {data['error']['message']}"

        # ✅ Normal response
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except Exception as e:
        return f"Request failed: {str(e)}"

# =====================
# EVENTS
# =====================
@client.event
async def on_ready():
    print(f"Bot is online as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != CHANNEL_ID:
        return

    async with message.channel.typing():
        reply = ask_gemini(message.content)
        await message.reply(reply)

# =====================
# START EVERYTHING
# =====================
keep_alive()
client.run(TOKEN)
