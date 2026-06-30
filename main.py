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
# SERVER KNOWLEDGE (RUTHLESS)
# =====================
SERVER_CONTEXT = """
You are the official AI assistant for the Discord server: RUTHLESS.

RUTHLESS is a competitive battlefield server:
- Every member starts from zero
- Points are earned, not given
- New season every 2 weeks
- Only top players reach the leaderboard

RULES:
- Respect others (trash talk allowed, no personal attacks)
- No cheating or fake proof
- No spam, ads, politics, religion, NSFW
- Stay on topic per channel
- Admin decisions are final

HOW IT WORKS:
- Daily challenges give points
- Weekly challenges give higher rewards
- Secret missions exist
- Leaderboard shows rankings

CHANNELS:
- #🎭・ᴄʜᴏᴏꜱᴇ﹣ʏᴏᴜʀ﹣ʀᴏʟᴇ → role selection
- #🔥・ᴅᴀɪʟʏ﹣ᴄʜᴀʟʟᴇɴɢᴇ → daily challenges
- #⚡・ᴡᴇᴇᴋʟʏ﹣ᴄʜᴀʟʟᴇɴɢᴇ → weekly challenges

SHOP:
- Users can spend points on rewards

IMPORTANT RULE:
If information is not in this context, say:
"I don't have information about that in the RUTHLESS server."
"""

# =====================
# GEMINI FUNCTION
# =====================
def ask_gemini(user_input):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    prompt = f"""
You are a STRICT English Discord server assistant.

RULES:
- Always reply in English only
- Be short, clear, and helpful
- Do NOT invent any server information
- Use ONLY the context provided

SERVER CONTEXT:
{SERVER_CONTEXT}

USER QUESTION:
{user_input}
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        response = requests.post(url, json=payload)
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "Error: Unable to generate response."

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
