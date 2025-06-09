import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.tree.command(name="report", description="Tổng hợp số reaction mỗi người trong X ngày gần nhất")
@app_commands.describe(days="Số ngày cần thống kê")
async def report(interaction: discord.Interaction, days: int):
    await interaction.response.defer(thinking=True)

    channel = interaction.channel
    after_time = datetime.utcnow() - timedelta(days=days)

    user_data = defaultdict(lambda: {"messages": 0, "reactions": 0})

    async for message in channel.history(after=after_time, limit=None):
        if message.author.bot:
            continue

        user_data[message.author]["messages"] += 1
        for reaction in message.reactions:
            user_data[message.author]["reactions"] += reaction.count

    if not user_data:
        await interaction.followup.send("Không có dữ liệu nào trong khoảng thời gian đã chọn.")
        return

    sorted_data = sorted(user_data.items(), key=lambda x: x[1]["reactions"], reverse=True)

    report_lines = []
    for i, (user, data) in enumerate(sorted_data, start=1):
        report_lines.append(f"{i}. {user.display_name}: {data['messages']} msg, {data['reactions']} react")

    report_text = "**📊 BÁO CÁO REACTION:**\n\n" + "\n".join(report_lines)
    await interaction.followup.send(report_text)

bot.run(TOKEN)
