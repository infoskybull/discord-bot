import discord
from discord.ext import commands
from discord import app_commands
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import os

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 946311467362287636  # Thay bằng server ID của bạn

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        print("✅ Slash commands synced.")

bot = MyBot()

# ✅ Không cần dùng self.tree.add_command nữa, dùng @bot.tree.command thay thế
@bot.tree.command(name="report", description="📊 Xếp hạng người nhận nhiều reaction nhất (7 ngày qua)")
async def report(interaction: discord.Interaction):
    await interaction.response.defer()
    channel = interaction.channel
    after_time = datetime.now(timezone.utc) - timedelta(days=7)

    reaction_counts = defaultdict(int)

    async for msg in channel.history(after=after_time, limit=None):
        if msg.author.bot:
            continue
        for reaction in msg.reactions:
            try:
                users = await reaction.users().flatten()
                reaction_counts[msg.author] += len(users)
            except:
                pass

    if not reaction_counts:
        await interaction.followup.send("⚠️ Không có dữ liệu reaction trong 7 ngày qua.")
        return

    sorted_users = sorted(reaction_counts.items(), key=lambda x: x[1], reverse=True)

    lines = ["🏆 **Top người nhận reaction nhiều nhất:**\n"]
    for i, (user, count) in enumerate(sorted_users, 1):
        lines.append(f"#{i}: {user.display_name} — ❤️ {count} reactions")

    await interaction.followup.send("\n".join(lines))

bot.run(TOKEN)
