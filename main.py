import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict, Counter

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents, application_id=os.getenv("DISCORD_APP_ID"))

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@bot.tree.command(name="report", description="Tạo báo cáo số lượng reactions trên các tin nhắn trong X ngày qua")
@app_commands.describe(days="Số ngày cần báo cáo")
async def report(interaction: discord.Interaction, days: int):
    await interaction.response.defer()
    now = datetime.utcnow()
    since = now - timedelta(days=days)

    channel = interaction.channel
    messages = [msg async for msg in channel.history(limit=None, after=since)]

    user_data = defaultdict(lambda: {"msg_count": 0, "reactions": Counter()})

    for msg in messages:
        if msg.author.bot:
            continue
        user = msg.author.display_name
        user_data[user]["msg_count"] += 1
        for reaction in msg.reactions:
            if reaction.count:
                user_data[user]["reactions"][str(reaction.emoji)] += reaction.count

    if not user_data:
        await interaction.followup.send("Không có dữ liệu nào trong khoảng thời gian này.")
        return

    report_lines = []
    for user, data in user_data.items():
        emoji_counts = ", ".join(f"{emoji}x{count}" for emoji, count in data["reactions"].items())
        total = sum(data["reactions"].values())
        report_lines.append(f"{user} - {data['msg_count']} messages - {emoji_counts} - total {total} reactions")

    report_text = "\n".join(report_lines)
    await interaction.followup.send(f"📊 **Reaction Report for last {days} day(s):**\n\n{report_text}")

if __name__ == "__main__":
    import asyncio
    TOKEN = os.getenv("DISCORD_TOKEN")
    assert TOKEN, "❌ DISCORD_TOKEN is not set!"
    bot.run(TOKEN)
