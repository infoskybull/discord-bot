import os
import discord
from discord.ext import tasks, commands
from discord import app_commands
from datetime import datetime, timedelta
import pytz
import asyncio

TOKEN = os.getenv("DISCORD_TOKEN")

# Check token existence
assert TOKEN is not None and TOKEN != "", "❌ DISCORD_TOKEN is not set!"

# Channel ID bạn muốn bot gửi báo cáo tự động
TRACK_CHANNEL_ID = 946311467362287636

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False

    async def setup_hook(self):
        if not self.synced:
            await self.tree.sync()
            self.synced = True
        self.auto_report.start()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

@bot.tree.command(name="report", description="Generate engagement report (last 1-7 days)")
@app_commands.describe(days="Number of days to report (1-7)")
async def report(interaction: discord.Interaction, days: int = 1):
    if not (1 <= days <= 7):
        await interaction.response.send_message("❌ Please choose days between 1 and 7.", ephemeral=True)
        return

    await interaction.response.defer()
    await send_report(interaction.channel, days)
    await interaction.followup.send("✅ Report generated!", ephemeral=True)

async def send_report(channel, days):
    now = datetime.now(pytz.utc)
    since = now - timedelta(days=days)

    message_counts = {}
    reaction_counts = {}

    async for message in channel.history(limit=None, after=since):
        if message.author.bot:
            continue

        user_id = message.author.id
        message_counts[user_id] = message_counts.get(user_id, 0) + 1

        reactors = set()
        for reaction in message.reactions:
            async for user in reaction.users():
                if user.id != message.author.id and not user.bot:
                    reactors.add(user.id)
        for user_id in reactors:
            reaction_counts[user_id] = reaction_counts.get(user_id, 0) + 1

    users = set(message_counts.keys()) | set(reaction_counts.keys())
    if not users:
        await channel.send("📉 No activity during this period.")
        return

    lines = ["📊 **Activity Report**"]
    for user_id in users:
        member = await channel.guild.fetch_member(user_id)
        name = member.display_name
        msg = message_counts.get(user_id, 0)
        react = reaction_counts.get(user_id, 0)
        lines.append(f"• **{name}** — {msg} msg, {react} reacts")

    top3 = sorted(users, key=lambda uid: (message_counts.get(uid, 0) + reaction_counts.get(uid, 0)), reverse=True)[:3]
    top_lines = ["🏆 **Top 3**"]
    for i, uid in enumerate(top3, 1):
        member = await channel.guild.fetch_member(uid)
        score = message_counts.get(uid, 0) + reaction_counts.get(uid, 0)
        top_lines.append(f"{i}. **{member.display_name}** - {score} pts")

    await channel.send("\n".join(lines + ["\n"] + top_lines))

@tasks.loop(minutes=1)
async def auto_report():
    now = datetime.now(pytz.timezone("Asia/Bangkok"))
    if now.weekday() == 5 and now.hour == 10 and now.minute == 0:
        channel = bot.get_channel(TRACK_CHANNEL_ID)
        if channel:
            await send_report(channel, 7)

bot.run(TOKEN)
