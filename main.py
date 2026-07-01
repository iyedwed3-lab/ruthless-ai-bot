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
# KEEP ALIVE (Render)
# =====================
app = Flask("")

@app.route("/")
def home():
    return "RUTHLESS AI Bot is alive!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run).start()

# =====================
# DISCORD SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =====================
# SERVER KNOWLEDGE
# =====================
SERVER_CONTEXT = """
RUTHLESS is a competitive Discord server.
Members earn points through challenges, missions, and activity.
The server has seasons that reset every 2 weeks.
"""

# =====================
# GEMINI FUNCTION (FIXED MODEL)
# =====================
def ask_gemini(user_input):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"""
You are the official assistant for a Discord server called RUTHLESS.

Rules:
- Always answer in English
- Be helpful and accurate
- If you don't know, say you don't know

Server info:
{SERVER_CONTEXT}

User question:
{user_input}
"""
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload)

        # Debug logs (important)
        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        data = response.json()

        if "error" in data:
            return f"API Error: {data['error']['message']}"

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
# START BOT
# =====================
keep_alive()
client.run(TOKEN)
