import os
import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 946311467362287636  # Thay bằng guild ID thực tế

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.message_log = defaultdict(list)
        self.reaction_log = defaultdict(lambda: defaultdict(int))

    async def setup_hook(self):
        # Sync slash commands cho guild cụ thể (tránh delay toàn cầu)
        guild = discord.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("✅ Slash commands synced for guild.")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    weekly_report.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    bot.message_log[message.author.id].append((message.channel.id, message.created_at))

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    bot.reaction_log[user.id][reaction.message.id] += 1

@bot.tree.command(name="report", description="Xem báo cáo top tương tác trong X ngày gần nhất (1-7)")
@app_commands.describe(days="Số ngày gần nhất (1-7)")
async def report_command(interaction: discord.Interaction, days: int = 7):
    if days < 1 or days > 7:
        await interaction.response.send_message("❌ Vui lòng chọn số ngày từ 1 đến 7.", ephemeral=True)
        return

    await interaction.response.defer()

    cutoff = datetime.utcnow() - timedelta(days=days)
    message_count = defaultdict(int)
    reaction_count = defaultdict(int)

    for user_id, messages in bot.message_log.items():
        for _, created_at in messages:
            if created_at >= cutoff:
                message_count[user_id] += 1

    for user_id, reactions in bot.reaction_log.items():
        for msg_id, count in reactions.items():
            reaction_count[user_id] += count

    all_user_ids = set(message_count) | set(reaction_count)
    result_lines = ["📊 **Báo cáo tương tác 7 ngày gần nhất:**\n"]

    leaderboard = []
    for uid in all_user_ids:
        msg = message_count.get(uid, 0)
        react = reaction_count.get(uid, 0)
        total = msg + react
        leaderboard.append((uid, msg, react, total))

    leaderboard.sort(key=lambda x: x[3], reverse=True)

    for rank, (uid, msg, react, total) in enumerate(leaderboard, start=1):
        user = await bot.fetch_user(uid)
        result_lines.append(f"**#{rank}** {user.display_name} - 💬 `{msg}` | ❤️ `{react}` | ⭐ Tổng: `{total}`")

    await interaction.followup.send("\n".join(result_lines[:10]))  # top 10

@tasks.loop(minutes=1)
async def weekly_report():
    now = datetime.now()
    if now.weekday() == 5 and now.hour == 10 and now.minute == 0:  # 10h sáng thứ 7 GMT+7
        for guild in bot.guilds:
            for channel in guild.text_channels:
                try:
                    perms = channel.permissions_for(guild.me)
                    if perms.send_messages:
                        class FakeInteraction:
                            async def response(self): pass
                            async def followup(self): pass
                        await report_command.callback(FakeInteraction(), 7)
                        break
                except:
                    continue

bot.run(TOKEN)
