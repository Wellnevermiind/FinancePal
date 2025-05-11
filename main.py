import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 857656646415024148
APP_ID = 1370900483174174780  # your real App ID

intents = discord.Intents.default()
intents.message_content = True

class FinancePal(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=APP_ID
        )

    async def setup_hook(self):
        # Load all cogs
        print("🔄 Loading cogs...")
        await self.load_extension("cogs.core")
        await self.load_extension("cogs.watchlist")
        await self.load_extension("cogs.compare")
        await self.load_extension("cogs.settings")
        await self.load_extension("cogs.alerts")
        print("✅ All cogs loaded.")

        # Sync slash commands to your dev server
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced slash commands to guild {GUILD_ID}")

bot = FinancePal()

@bot.event
async def on_ready():
    print(f"✅ FinancePal is online as {bot.user}")
    print(f"Cogs loaded: {list(bot.extensions.keys())}")

bot.run(TOKEN)
