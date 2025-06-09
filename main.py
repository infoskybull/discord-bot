import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from dotenv import load_dotenv
import datetime

# Tải biến môi trường từ .env (nếu chạy local)
load_dotenv()

# Lấy token và các thông tin cấu hình từ biến môi trường
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

# Kiểm tra biến môi trường
assert TOKEN is not None and TOKEN != "", "❌ DISCORD_TOKEN is not set!"
assert GUILD_ID is not None, "❌ DISCORD_GUILD_ID is not set!"
assert CHANNEL_ID is not None, "❌ DISCORD_CHANNEL_ID is not set!"

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
        from report import generate_report_image  # Import tại thời điểm chạy
        channel = self.get_channel(CHANNEL_ID)
        if channel:
            image_path = generate_report_image()
            await channel.send("📊 Bảng tổng hợp tương tác hôm nay:", file=discord.File(image_path))
        else:
            print("❌ Không tìm thấy channel!")

    @auto_report.before_loop
    async def before_auto_report(self):
        await self.wait_until_ready()

# Khởi chạy bot
bot = MyBot()
bot.run(TOKEN)
