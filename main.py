import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import aiosqlite
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = 1370900483174174780  # your real App ID

intents = discord.Intents.default()
intents.message_content = True

DB_PATH = "data/finance.db"
os.makedirs("data", exist_ok=True)

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
        await self.load_extension("cogs.info")
        print("✅ All cogs loaded.")

        # Create seen_users table for onboarding tracking
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS seen_users (
                    user_id TEXT PRIMARY KEY
                )
            ''')
            await db.commit()

        # Sync slash commands globally (takes up to 1 hour to appear)
        await self.tree.sync()
        print("✅ Synced global slash commands")

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.user and not interaction.user.bot:
            user_id = str(interaction.user.id)
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute("SELECT 1 FROM seen_users WHERE user_id = ?", (user_id,))
                seen = await cursor.fetchone()

                if not seen:
                    try:
                        await interaction.user.send(
                            "**👋 Welcome to FinancePal!**\n\n"
                            "Thanks for trying out the bot. Use `/help` to view available commands and `/settings` to personalize your experience.\n\n"
                            "Need help? Use `/info` or contact the developer!"
                        )
                    except discord.Forbidden:
                        pass  # User has DMs closed

                    await db.execute("INSERT INTO seen_users (user_id) VALUES (?)", (user_id,))
                    await db.commit()

        await commands.Bot.on_interaction(self, interaction)

bot = FinancePal()

@bot.event
async def on_ready():
    print(f"✅ FinancePal is online as {bot.user}")
    print(f"Cogs loaded: {list(bot.extensions.keys())}")

bot.run(TOKEN)
