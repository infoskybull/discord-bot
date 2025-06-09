import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime, timedelta

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.messages = True
intents.guilds = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        @self.tree.command(name="report", description="Report reaction count in the past N days")
        @app_commands.describe(days="How many days back to count reactions")
        async def report(interaction: discord.Interaction, days: int):
            await interaction.response.defer(thinking=True)
            after = datetime.utcnow() - timedelta(days=days)
            channel = interaction.channel

            summary = []
            async for msg in channel.history(limit=None, after=after):
                total = sum(reaction.count for reaction in msg.reactions)
                if total > 0:
                    summary.append((msg, total))

            if not summary:
                await interaction.followup.send("❌ Không có tin nhắn nào có reaction trong khoảng thời gian này.")
                return

            summary.sort(key=lambda x: x[1], reverse=True)
            response = "\n".join([f"{i+1}. {msg.author.display_name}: {count} reaction(s)" for i, (msg, count) in enumerate(summary[:10])])
            await interaction.followup.send(f"📊 Top tin nhắn có reaction trong {days} ngày qua:\n{response}")

        await self.tree.sync()

bot = MyBot()
if TOKEN is None or TOKEN == "":
    raise ValueError("❌ DISCORD_TOKEN is not set!")

bot.run(TOKEN)
