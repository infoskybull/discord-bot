import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
import pytz

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", "946311467362287636"))
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "YOUR_CHANNEL_ID"))  # Thay bằng ID thật

assert TOKEN is not None and TOKEN != "", "❌ DISCORD_TOKEN is not set!"

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.synced = False  # Để tránh sync nhiều lần
        self.guild = discord.Object(id=GUILD_ID)

    async def setup_hook(self):
        self.tree.add_command(report_command)
        self.auto_report.start()

    @tasks.loop(hours=24)
    async def auto_report(self):
        await self.wait_until_ready()
        now = datetime.now(pytz.timezone("Asia/Ho_Chi_Minh"))
        if now.hour == 10 and now.weekday() == 5:  # Thứ 7, 10h sáng
            channel = self.get_channel(CHANNEL_ID)
            if channel:
                await channel.send("📊 Báo cáo tự động lúc 10h sáng thứ 7 (GMT+7) đã được gửi!")

    async def on_ready(self):
        if not self.synced:
            await self.tree.sync(guild=self.guild)
            self.synced = True
        print(f"✅ Logged in as {self.user}")

bot = MyBot()

# Slash command /report
@app_commands.command(name="report", description="📊 Gửi báo cáo thủ công")
async def report_command(interaction: discord.Interaction):
    await interaction.response.send_message("📈 Đây là báo cáo của bạn!", ephemeral=True)

bot.run(TOKEN)
