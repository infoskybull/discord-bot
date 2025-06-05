import discord
from discord.ext import commands, tasks
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import os

# Lấy token từ biến môi trường
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Cấu hình intents cần thiết
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

# Khởi tạo bot
bot = commands.Bot(command_prefix="!", intents=intents)

# Hàm định dạng báo cáo
def format_report(user_stats):
    if not user_stats:
        return "No messages or reactions found in the given time range."

    sorted_stats = sorted(user_stats.items(), key=lambda item: item[1]['reactions'], reverse=True)
    lines = ["**📊 Weekly Reaction Leaderboard:**\n"]

    for i, (user, data) in enumerate(sorted_stats, 1):
        lines.append(f"**{i}.** {user} — 💬 Messages: {data['messages']} | ⭐ Reactions: {data['reactions']}")

    return "\n".join(lines)

# Hàm thu thập dữ liệu từ kênh
async def fetch_channel_messages(channel, days=7):
    after = datetime.now(timezone.utc) - timedelta(days=days)
    user_stats = defaultdict(lambda: {"messages": 0, "reactions": 0})
    
    async for message in channel.history(limit=None, after=after):
        if not message.author.bot:
            user_stats[message.author]["messages"] += 1

            for reaction in message.reactions:
                try:
                    users = await reaction.users().flatten()
                    for user in users:
                        if user != message.author:
                            user_stats[message.author]["reactions"] += 1
                except Exception:
                    continue
    return user_stats

# Lệnh thủ công để theo dõi
@bot.command(name="track")
async def track(ctx, channel: discord.TextChannel, days: int = 7):
    await ctx.send(f"🔍 Tracking messages and reactions from **{channel.mention}** in the last **{days} days**...")
    user_stats = await fetch_channel_messages(channel, days)
    report = format_report(user_stats)
    await ctx.send(report)

# Tự động gửi báo cáo mỗi thứ 7
@tasks.loop(hours=24)
async def weekly_report():
    now = datetime.now()
    if now.weekday() == 5:  # 5 = Thứ 7
        for guild in bot.guilds:
            for channel in guild.text_channels:
                if "general" in channel.name.lower():  # Tuỳ chỉnh nếu cần
                    try:
                        user_stats = await fetch_channel_messages(channel, 7)
                        report = format_report(user_stats)
                        await channel.send(report)
                    except:
                        continue

@bot.event
async def on_ready():
    print(f"✅ Bot is logged in as: {bot.user}")
    weekly_report.start()

# Khởi động bot
bot.run(TOKEN)
