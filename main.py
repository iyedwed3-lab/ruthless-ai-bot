import discord
import os
import requests
import time
import numpy as np
from flask import Flask
from threading import Thread

# =====================
# ENV VARIABLES
# =====================
TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# =====================
# KEEP ALIVE (RENDER)
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
# DISCORD SETUP
# =====================
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# =====================
# SERVER CONTEXT
# =====================
SERVER_CONTEXT = """
RUTHLESS is a competitive Discord server.
Members earn points via daily challenges, weekly challenges, and secret missions.
Seasons reset every 2 weeks.
Fake proof = ban or punishment.
No spam, cheating, or drama.
"""

SYSTEM_PROMPT = f"""
You are Vortex, an advanced AI assistant inside the RUTHLESS Discord server.

RULES:
- Always respond in English
- Be short, clear, and helpful
- Do NOT invent server information
- If you don't know, say so honestly

SERVER INFO:
{SERVER_CONTEXT}

CREATOR INFORMATION RULE:
If the user asks:
- "Who made you?"
- "Who created you?"
- "Who is your developer?"
- Or anything similar about your origin

Then respond with:

"Vortex was created by Iyeed, the developer and founder of the RUTHLESS Discord system. He built Vortex specifically to manage assistance, intelligence, and competitive features inside the server. His goal was to create a smart and fair system that supports players and enhances the RUTHLESS experience."

Never mention OpenRouter or APIs in responses.
"""

# =====================
# ANTI SPAM
# =====================
last_time = {}
COOLDOWN = 4

# =====================
# CACHE SYSTEMS
# =====================
exact_cache = {}
smart_cache = []
SIMILARITY_THRESHOLD = 0.85

# =====================
# EMBEDDING FUNCTION
# =====================
def get_embedding(text):
    url = "https://openrouter.ai/api/v1/embeddings"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/text-embedding-3-small",
        "input": text
    }

    try:
        r = requests.post(url, json=payload, headers=headers)
        print(r.text)
        data = r.json()
        return data["data"][0]["embedding"]
    except:
        return None

# =====================
# COSINE SIMILARITY
# =====================
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# =====================
# SMART CACHE SEARCH
# =====================
def search_smart_cache(text):
    emb = get_embedding(text)
    if emb is None:
        return None

    for item in smart_cache:
        sim = cosine_similarity(emb, item["emb"])
        if sim >= SIMILARITY_THRESHOLD:
            return item["response"]

    return None

# =====================
# AI REQUEST
# =====================
def ask_ai(text):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text}
        ]
    }

    try:
        r = requests.post(url, json=payload)
        data = r.json()

        if "error" in data:
            return None

        return data["choices"][0]["message"]["content"]

    except:
        return None

# =====================
# FALLBACK RESPONSES
# =====================
fallbacks = [
    "⚡ I couldn't find an answer right now. Try again later.",
    "🕵️ This question is outside my knowledge base.",
    "📡 Signal lost... please rephrase your question.",
    "🚫 I don't have enough data to answer this."
]

def fallback():
    import random
    return random.choice(fallbacks)

# =====================
# EVENTS
# =====================
@client.event
async def on_ready():
    print(f"Vortex is online as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id != CHANNEL_ID:
        return

    text = message.content.strip().lower()
    if not text:
        return

    now = time.time()

    # =====================
    # ANTI-SPAM
    # =====================
    if message.author.id in last_time:
        if now - last_time[message.author.id] < COOLDOWN:
            return

    last_time[message.author.id] = now

    # =====================
    # EXACT CACHE
    # =====================
    if text in exact_cache:
        await message.reply(exact_cache[text])
        return

    # =====================
    # SMART CACHE
    # =====================
    smart = search_smart_cache(text)
    if smart:
        await message.reply(smart)
        return

    async with message.channel.typing():

        reply = ask_ai(text)

        # =====================
        # IF AI FAILS
        # =====================
        if reply is None:
            reply = fallback()

        # =====================
        # SAVE CACHE
        # =====================
        exact_cache[text] = reply

        emb = get_embedding(text)
        if emb is not None:
            smart_cache.append({
                "emb": emb,
                "response": reply
            })

        await message.reply(reply)

# =====================
# START
# =====================
keep_alive()
client.run(TOKEN)
