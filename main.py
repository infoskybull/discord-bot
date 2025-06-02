import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import discord
from discord.ext import commands, tasks

TOKEN = os.environ['DISCORD_BOT_TOKEN']
REPORT_CHANNEL_ID = 123456789012345678  # 🔁 Replace with your real channel ID

# JSON DB setup
DB_PATH = Path("db.json")

def load_db():
    if DB_PATH.exists():
        with open(DB_PATH, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f)

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot is logged in as: {bot.user}")
    weekly_report.start()

@bot.command()
async def track(ctx, channel: discord.TextChannel):
    data = load_db()
    data["tracked_channel"] = channel.id
    save_db(data)
    await ctx.send(f"📌 Now tracking reactions in channel: {channel.mention}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return

    data = load_db()
    if data.get("tracked_channel") != message.channel.id:
        return

    day_key = datetime.utcnow().strftime('%Y-%m-%d')
    msg_key = f"{day_key}_messages"
    author_id = str(message.author.id)
    messages = data.get(msg_key, {})
    messages[author_id] = messages.get(author_id, 0) + 1
    data[msg_key] = messages
    save_db(data)

@bot.event
async def on_raw_reaction_add(payload):
    data = load_db()
    if data.get("tracked_channel") != payload.channel_id:
        return

    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        channel = await bot.fetch_channel(payload.channel_id)

    try:
        message = await channel.fetch_message(payload.message_id)
    except discord.NotFound:
        return

    author_id = str(message.author.id)
    day_key = datetime.utcnow().strftime('%Y-%m-%d')
    react_key = f"{day_key}_reactions"
    total_unique = 0
    for reaction in message.reactions:
        try:
            users = await reaction.users().flatten()
            total_unique += len(set(user.id for user in users if not user.bot))
        except:
            continue

    reactions = data.get(react_key, {})
    reactions[author_id] = reactions.get(author_id, 0) + total_unique
    data[react_key] = reactions
    save_db(data)

@bot.command()
async def report(ctx, day_offset: int = 0):
    data = load_db()
    target_day = datetime.utcnow() - timedelta(days=day_offset)
    day_str = target_day.strftime('%Y-%m-%d')
    msg_key = f"{day_str}_messages"
    react_key = f"{day_str}_reactions"

    msg_data = data.get(msg_key, {})
    react_data = data.get(react_key, {})
    all_users = set(msg_data.keys()) | set(react_data.keys())

    if not all_users:
        await ctx.send(f"❌ No data found for `{day_str}`.")
        return

    lines = []
    for uid in all_users:
        msg_count = msg_data.get(uid, 0)
        react_count = react_data.get(uid, 0)
        lines.append(f"<@{uid}> – 📝 {msg_count} messages, 💖 {react_count} reactions")

    await ctx.send(f"📊 **Reaction Report for `{day_str}`**\n" + "\n".join(lines))

@tasks.loop(hours=24)
async def weekly_report():
    await bot.wait_until_ready()

    data = load_db()
    today = datetime.utcnow()
    if today.weekday() != 5:  # Saturday
        return

    combined_msgs = {}
    combined_reacts = {}

    for i in range(7):
        day = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        msg_key = f"{day}_messages"
        react_key = f"{day}_reactions"

        for uid, cnt in data.get(msg_key, {}).items():
            combined_msgs[uid] = combined_msgs.get(uid, 0) + cnt
        for uid, cnt in data.get(react_key, {}).items():
            combined_reacts[uid] = combined_reacts.get(uid, 0) + cnt

    all_users = set(combined_msgs.keys()) | set(combined_reacts.keys())
    if not all_users:
        return

    lines = []
    for uid in all_users:
        msg_count = combined_msgs.get(uid, 0)
        react_count = combined_reacts.get(uid, 0)
        lines.append(f"<@{uid}> – 📝 {msg_count} messages, 💖 {react_count} reactions")

    channel = bot.get_channel(REPORT_CHANNEL_ID)
    await channel.send("📊 **Weekly Reaction Report**\n" + "\n".join(lines))

bot.run(TOKEN)
