import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.reactions = True
intents.message_content = True

TOKEN = os.getenv("DISCORD_TOKEN")
assert TOKEN is not None and TOKEN != "", "❌ DISCORD_TOKEN is not set!"

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="/", intents=intents, application_id=None)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")

@bot.tree.command(name="report", description="Tạo báo cáo reaction trong N ngày qua")
@app_commands.describe(days="Số ngày cần báo cáo")
async def report(interaction: discord.Interaction, days: int):
    await interaction.response.defer(thinking=True)

    now = datetime.utcnow()
    since = now - timedelta(days=days)

    channel = interaction.channel
    assert isinstance(channel, discord.TextChannel)

    messages = []
    async for message in channel.history(limit=None, after=since):
        total_reactions = sum(reaction.count for reaction in message.reactions)
        if total_reactions > 0:
            messages.append((message, total_reactions))

    if not messages:
        await interaction.followup.send("Không có tin nhắn nào có reaction trong khoảng thời gian đó.")
        return

    messages.sort(key=lambda x: x[1], reverse=True)
    lines = []
    for msg, total in messages:
        content = msg.content[:50].replace('\n', ' ')
        author = msg.author.display_name
        lines.append(f"{author}: '{content}' → ❤️ {total}")

    report_text = "\n".join(lines[:10])
    await interaction.followup.send(f"📊 **Top phản ứng trong {days} ngày qua**:\n{report_text}")

bot.run(TOKEN)
