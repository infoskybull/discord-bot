import os
import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.messages = True
INTENTS.reactions = True
INTENTS.guilds = True
INTENTS.members = True

bot = commands.Bot(command_prefix="!", intents=INTENTS)
report_channels = {}  # Guild ID -> channel to send weekly reports


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    for guild in bot.guilds:
        await bot.tree.sync(guild=guild)
        print(f"✅ Slash commands synced for {guild.name}")
    weekly_report_loop.start()


def generate_leaderboard_image(data, top_n=3):
    width, row_height = 700, 50
    display_data = data[:top_n]
    height = max(200, row_height * (len(display_data) + 1) + 50)

    img = Image.new("RGB", (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    draw.text((20, 20), f"🏆 Top {top_n} Leaderboard", fill=(255, 255, 255), font=font)

    for i, (name, stats) in enumerate(display_data, start=1):
        line = f"{i}. {name} - Messages: {stats['messages']}, Reactions: {stats['reactions']}"
        draw.text((20, 20 + i * row_height), line, fill=(200, 200, 200), font=font)

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


async def generate_report(channel, days: int = 7):
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    user_messages = defaultdict(lambda: {"messages": 0, "reactions": 0})

    async for message in channel.history(after=since, oldest_first=True, limit=None):
        if message.author.bot:
            continue

        user = message.author.display_name
        user_messages[user]["messages"] += 1

        unique_reactors = set()
        for reaction in message.reactions:
            try:
                users = await reaction.users().flatten()
                for u in users:
                    if u != message.author:
                        unique_reactors.add((reaction.emoji, u.id))
            except:
                pass
        user_messages[user]["reactions"] += len(unique_reactors)

    sorted_data = sorted(user_messages.items(), key=lambda x: (x[1]["reactions"], x[1]["messages"]), reverse=True)

    if not sorted_data:
        await channel.send("No data found for this period.")
        return

    # Summary
    total_msg = sum(entry["messages"] for _, entry in sorted_data)
    total_react = sum(entry["reactions"] for _, entry in sorted_data)
    await channel.send(f"📊 Weekly Report (Last {days} Days)\nTotal Messages: {total_msg}\nTotal Reactions: {total_react}")

    # Top 3 image
    image = generate_leaderboard_image(sorted_data, top_n=3)
    await channel.send(file=discord.File(image, filename="weekly_leaderboard.png"))


@bot.tree.command(name="report", description="Generate a leaderboard report")
@app_commands.describe(days="Number of days to include in the report (1–7)")
async def report_command(interaction: discord.Interaction, days: int = 7):
    await interaction.response.defer()

    if days < 1 or days > 7:
        await interaction.followup.send("Please choose between 1 and 7 days.")
        return

    # Save current channel for scheduled reports
    report_channels[interaction.guild.id] = interaction.channel
    await generate_report(interaction.channel, days)


@tasks.loop(minutes=1)
async def weekly_report_loop():
    now = datetime.now(timezone(timedelta(hours=7)))  # UTC+7
    if now.weekday() == 5 and now.hour == 10 and now.minute == 0:  # Saturday 10:00
        print("📤 Sending scheduled weekly reports...")
        for guild_id, channel in report_channels.items():
            try:
                await generate_report(channel)
            except Exception as e:
                print(f"❌ Failed to send report to guild {guild_id}:", e)


@weekly_report_loop.before_loop
async def before_weekly_report():
    await bot.wait_until_ready()


if __name__ == "__main__":
    bot.run(TOKEN)
