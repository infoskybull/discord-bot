import discord
from discord.ext import tasks
from discord import app_commands
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import os
import asyncio

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.message_content = True
intents.members = True

report_channels = {}  # guild_id -> channel_id

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.add_command(report_command)
        await self.tree.sync()
        print("✅ Slash commands synced")

bot = MyClient()

async def collect_stats(channel: discord.TextChannel, days: int = 7):
    after = datetime.now(timezone.utc) - timedelta(days=days)
    stats = defaultdict(lambda: {'messages': 0, 'reactions': 0})

    async for msg in channel.history(limit=None, after=after):
        if msg.author.bot:
            continue
        stats[msg.author.display_name]['messages'] += 1
        unique_reactors = set()
        for reaction in msg.reactions:
            async for user in reaction.users():
                if user != msg.author:
                    unique_reactors.add((reaction.emoji, user.id))
        stats[msg.author.display_name]['reactions'] += len(unique_reactors)

    sorted_stats = sorted(stats.items(), key=lambda x: x[1]['reactions'], reverse=True)
    return sorted_stats

@bot.tree.command(name="report", description="Generate reaction leaderboard (1–7 days)")
@app_commands.describe(days="Number of days to analyze (1–7)")
async def report_command(interaction: discord.Interaction, days: int = 7):
    if not (1 <= days <= 7):
        await interaction.response.send_message("Please choose between 1 and 7 days.", ephemeral=True)
        return

    report_channels[interaction.guild_id] = interaction.channel_id
    await interaction.response.send_message(f"Tracking this channel and generating report for past {days} day(s)...", ephemeral=True)

    channel = interaction.channel
    stats = await collect_stats(channel, days)

    if not stats:
        await channel.send("No data to display.")
        return

    lines = [f"📊 **Leaderboard for past {days} day(s):**"]
    for i, (name, data) in enumerate(stats[:10], 1):
        lines.append(f"{i}. **{name}** — 💬 {data['messages']} msgs, 💖 {data['reactions']} reactions")

    await channel.send("\n".join(lines))

@tasks.loop(minutes=1)
async def scheduled_report():
    now = datetime.now(timezone(timedelta(hours=7)))  # GMT+7
    if now.weekday() == 5 and now.hour == 10 and now.minute == 0:
        for guild_id, channel_id in report_channels.items():
            guild = bot.get_guild(guild_id)
            if not guild:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            stats = await collect_stats(channel, 7)
            if not stats:
                await channel.send("📊 No data collected this week.")
                continue

            lines = ["📊 **Weekly Leaderboard (7 days):**"]
            for i, (name, data) in enumerate(stats[:10], 1):
                lines.append(f"{i}. **{name}** — 💬 {data['messages']} msgs, 💖 {data['reactions']} reactions")

            await channel.send("\n".join(lines))

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    scheduled_report.start()

bot.run(TOKEN)
