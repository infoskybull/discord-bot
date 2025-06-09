import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime

# Lấy thông tin từ biến môi trường Railway
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# Kiểm tra biến môi trường bắt buộc
assert TOKEN, "❌ DISCORD_TOKEN is not set!"
assert GUILD_ID, "❌ DISCORD_GUILD_ID is not set!"
assert CHANNEL_ID, "❌ DISCORD_CHANNEL_ID is not set!"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.reactions = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        self.auto_report.start()

    @tasks.loop(time=datetime.time(hour=10, tzinfo=datetime.timezone(datetime.timedelta(hours=7))))
    async def auto_report(self):
        channel = self.get_channel(CHANNEL_ID)
        if channel:
            await channel.send("📊 Báo cáo hàng tuần: Mọi thứ vẫn hoạt động tốt!")
        else:
            print("❌ Không tìm thấy channel!")

    @auto_report.before_loop
    async def before_auto_report(self):
        await self.wait_until_ready()

bot = MyBot()
bot.run(TOKEN)
