import discord
from discord.ext import commands, tasks
import os
import json
from datetime import datetime, timedelta
from pathlib import Path

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

DB_PATH = Path("db.json")

def load_db():
    if DB_PATH.exists():
        with open(DB_PATH, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f)

@bot.event
async def on_ready():
    print(f"✅ Bot is logged in as: {bot.user}")
    weekly_report.start()

@bot.command()
async def track(ctx, channel: discord.TextChannel):
    data = load_db()
    data["tracked_channel"] = channel.id
    save_db(data)
    await ctx.send(f"🔍 Now tracking reactions and messages in {channel.mention}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_db()
    if data.get("tracked_channel") != message.channel.id:
        return

    author_id = str(message.author.id)
    day_key = datetime.utcnow().strftime('%Y-%m-%d')
    msg_key = f"{day_key}_messages"

    data[msg_key] = data.get(msg_key, {})
    data[msg_key][author_id] = data[msg_key].get(author_id, 0) + 1

    save_db(data)
    await bot.process_commands(message)

@bot.event
async def on_raw_reaction_add(payload):
    data = load_db()

    if data.get("tracked_channel") != payload.channel_id:
        return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        channel = await bot.fetch_channel(payload.channel_id)

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return

    author_id = str(message.author.id)
    day_key = datetime.utcnow().strftime('%Y-%m-%d')
    react_key = f"{day_key}_reactions"

    unique_reactors = set()
    for reaction in message.reactions:
        async for user in reaction.users():
            if not user.bot:
                unique_reactors.add((reaction.emoji, user.id))

    data[react_key] = data.get(react_key, {})
    data[react_key][author_id] = data[react_key].get(author_id, 0) + len(unique_reactors)

    save_db(data)

@bot.command()
async def report(ctx):
    today = datetime.utcnow()
    day_key = today.strftime('%Y-%m-%d')
    data = load_db()

    msg_counts = data.get(f"{day_key}_messages", {})
    react_counts = data.get(f"{day_key}_reactions", {})

    if not msg_counts and not react_counts:
        await ctx.send("No data collected today.")
        return

    report_lines = [f"📊 Reaction Report for {day_key}"]
    user_ids = set(msg_counts.keys()) | set(react_counts.keys())
    for uid in user_ids:
        msg = msg_counts.get(uid, 0)
        react = react_counts.get(uid, 0)
        report_lines.append(f"<@{uid}> – 📝 {msg} messages, 💖 {react} reactions")

    await ctx.send("\n".join(report_lines))

@tasks.loop(hours=24)
async def weekly_report():
    now = datetime.utcnow()
    if now.weekday() != 5:  # Only run on Saturday UTC
        return

    data = load_db()
    all_msg, all_react = {}, {}

    for i in range(7):
        day = (now - timedelta(days=i)).strftime('%Y-%m-%d')
        for uid, count in data.get(f"{day}_messages", {}).items():
            all_msg[uid] = all_msg.get(uid, 0) + count
        for uid, count in data.get(f"{day}_reactions", {}).items():
            all_react[uid] = all_react.get(uid, 0) + count

    if not all_msg and not all_react:
        return

    report_lines = ["📊 Weekly Reaction Report"]
    user_ids = set(all_msg.keys()) | set(all_react.keys())
    for uid in user_ids:
        msg = all_msg.get(uid, 0)
        react = all_react.get(uid, 0)
        report_lines.append(f"<@{uid}> – 📝 {msg} messages, 💖 {react} reactions")

    channel_id = 946311467848855555  # fixed tracked channel
    channel = bot.get_channel(channel_id)
    if not channel:
        channel = await bot.fetch_channel(channel_id)
    await channel.send("\n".join(report_lines))

bot.run(TOKEN)
