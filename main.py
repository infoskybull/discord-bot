import discord
from discord.ext import tasks
from discord import app_commands
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.add_command(report_command)
        weekly_report.start()

bot = MyBot()

async def fetch_channel_messages(channel, days=7):
    after = datetime.now(timezone.utc) - timedelta(days=days)
    user_stats = defaultdict(lambda: {"messages": 0, "reactions": 0})

    async for message in channel.history(limit=None, after=after):
        if not message.author.bot:
            user_stats[message.author]["messages"] += 1
            for reaction in message.reactions:
                try:
                    users = await reaction.users().flatten()
                    for user in users:
                        if user != message.author:
                            user_stats[message.author]["reactions"] += 1
                except:
                    continue
    return user_stats

def generate_image_report(user_stats):
    sorted_stats = sorted(user_stats.items(), key=lambda item: item[1]['reactions'], reverse=True)
    width = 700
    row_height = 50
    height = max(150, row_height * (len(sorted_stats) + 2))
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    draw.text((10, 10), "📊 Weekly Reaction Leaderboard", fill="black", font=font)
    for i, (user, data) in enumerate(sorted_stats, start=1):
        line = f"{i}. {user.display_name} — Messages: {data['messages']} | Reactions: {data['reactions']}"
        draw.text((10, 10 + i * row_height), line, fill="black", font=font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return discord.File(buf, filename="report.png")

@bot.tree.command(name="report", description="Get leaderboard in current channel")
@app_commands.describe(days="Number of days to check (default 7)")
async def report_command(interaction: discord.Interaction, days: int = 7):
    await interaction.response.defer()
    user_stats = await fetch_channel_messages(interaction.channel, days)
    if not user_stats:
        await interaction.followup.send("No data available.")
    else:
        file = generate_image_report(user_stats)
        await interaction.followup.send(file=file)

@tasks.loop(hours=24)
async def weekly_report():
    now = datetime.now(timezone.utc)
    if now.weekday() == 5:  # Saturday
        for guild in bot.guilds:
            for channel in guild.text_channels:
                if "general" in channel.name.lower():
                    try:
                        stats = await fetch_channel_messages(channel, 7)
                        if stats:
                            img = generate_image_report(stats)
                            await channel.send(file=img)
                    except:
                        continue

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        await bot.tree.sync()
        print("✅ Slash commands synced.")
    except Exception as e:
        print("❌ Sync failed:", e)

bot.run(TOKEN)
