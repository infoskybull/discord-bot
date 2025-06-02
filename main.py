import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from replit import db

TOKEN = os.environ['DISCORD_BOT_TOKEN']
REPORT_CHANNEL_ID = 123456789012345678  # 🔁 Replace this with your Discord channel ID

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
    db["tracked_channel"] = channel.id
    await ctx.send(f"📌 Now tracking reactions in channel: {channel.mention}")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author.bot:
        return
    if db.get("tracked_channel") != message.channel.id:
        return

    day_key = datetime.utcnow().strftime('%Y-%m-%d')
    key = f"{day_key}_messages"
    data = db.get(key, {})
    author_id = str(message.author.id)
    data[author_id] = data.get(author_id, 0) + 1
    db[key] = data

@bot.event
async def on_raw_reaction_add(payload):
    if db.get("tracked_channel") != payload.channel_id:
        return

    channel = bot.get_channel(payload.channel_id)
    if channel is None:
        channe

