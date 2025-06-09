import discord
from discord.ext import tasks
from discord import app_commands
import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 946311467362287636  # Thay bằng ID server của bạn

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True
intents.members = True

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.report_channel_id = None

    async def setup_hook(self):
        if not any(cmd.name == "report" for cmd in self.tree.get_commands()):
            self.tree.add_command(report_command)
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Slash commands synced for SKYBULL VIETNAM")

client = MyClient()

def get_report_content(messages_data, total_days):
    lines = [f"📊 Report for the last {total_days} day(s):"]
    sorted_users = sorted(messages_data.items(), key=lambda x: x[1]['reactions'], reverse=True)

    for i, (user, data) in enumerate(sorted_users, 1):
        lines.append(f"{i}. {user.display_name} — 📨 {data['messages']} msgs | ❤️ {data['reactions']} reacts")

    top3 = sorted_users[:3]
    if top3:
        lines.append("\n🏆 Top 3:")
        for i, (user, data) in enumerate(top3, 1):
            lines.append(f"#{i}: {user.display_name} — ❤️ {data['reactions']} reactions")
    return "\n".join(lines)

async def collect_data(channel, days):
    now = datetime.now(timezone.utc)
    after_time = now - timedelta(days=days)
    messages_data = defaultdict(lambda: {"messages": 0, "reactions": 0})

    async for msg in channel.history(after=after_time, limit=None):
        if msg.author.bot:
            continue
        messages_data[msg.author]["messages"] += 1
        if msg.reactions:
            for react in msg.reactions:
                try:
                    users = await react.users().flatten()
                    messages_data[msg.author]["reactions"] += len(users)
                except:
                    continue
    return messages_data

@client.tree.command(name="report", description="Generate a report for the last N days")
@app_commands.describe(days="Number of days (1-7)")
async def report_command(interaction: discord.Interaction, days: int = 7):
    if days < 1 or days > 7:
        await interaction.response.send_message("❌ Days must be between 1 and 7.", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)
    channel = interaction.channel
    data = await collect_data(channel, days)
    content = get_report_content(data, days)
    await interaction.followup.send(content)

# Tự động gửi report mỗi thứ 7 lúc 10h sáng GMT+7
@tasks.loop(minutes=1)
async def weekly_report_task():
    now = datetime.now(timezone(timedelta(hours=7)))
    if now.weekday() == 5 and now.hour == 10 and now.minute == 0:  # Saturday 10:00
        channel = client.get_channel(client.report_channel_id)
        if channel:
            data = await collect_data(channel, 7)
            content = get_report_content(data, 7)
            await channel.send("📥 Weekly Auto Report:\n" + content)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    client.report_channel_id = YOUR_TRACKED_CHANNEL_ID  # <-- Thay bằng ID channel thực tế
    weekly_report_task.start()

client.run(TOKEN)
