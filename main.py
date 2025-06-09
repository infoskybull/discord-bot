import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.reactions = True
intents.guilds = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=None)
        await self.tree.sync()

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

@bot.tree.command(name="report")
@app_commands.describe(days="Số ngày cần báo cáo")
async def report(interaction: discord.Interaction, days: int):
    await interaction.response.defer(thinking=True)

    now = datetime.utcnow()
    since = now - timedelta(days=days)

    user_stats = {}  # {user_id: {"name": str, "messages": int, "reactions": int}}

    for channel in interaction.guild.text_channels:
        try:
            async for msg in channel.history(after=since, oldest_first=True, limit=None):
                if msg.author.bot:
                    continue

                user_id = msg.author.id
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        "name": msg.author.display_name,
                        "messages": 0,
                        "reactions": 0
                    }
                user_stats[user_id]["messages"] += 1
                user_stats[user_id]["reactions"] += sum(reaction.count for reaction in msg.reactions)
        except (discord.Forbidden, discord.HTTPException):
            continue

    if not user_stats:
        await interaction.followup.send("😿 Không có dữ liệu để thống kê.")
        return

    sorted_users = sorted(user_stats.values(), key=lambda x: x["reactions"], reverse=True)

    lines = ["📊 **Báo cáo tương tác**"]
    for i, user in enumerate(sorted_users, 1):
        lines.append(f"{i}. **{user['name']}** — 💬 {user['messages']} tin nhắn | 🧡 {user['reactions']} reaction")

    await interaction.followup.send("\n".join(lines))

TOKEN = os.getenv("DISCORD_TOKEN")
assert TOKEN is not None and TOKEN != "", "❌ DISCORD_TOKEN is not set!"

bot.run(TOKEN)
