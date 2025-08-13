import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import aiosqlite

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = 1370900483174174780  # your real App ID
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID")  # set to a guild ID string during dev, or leave unset for global

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
        self._synced_once = False  # guard against duplicate syncs on reconnects

    async def setup_hook(self):
        print("🔄 Loading cogs...")
        # Important: cogs must NOT call tree.sync() themselves.
        await self.load_extension("cogs.core")
        await self.load_extension("cogs.watchlist")
        await self.load_extension("cogs.compare")
        await self.load_extension("cogs.settings")
        await self.load_extension("cogs.alerts")
        await self.load_extension("cogs.info")
        await self.load_extension("cogs.errors")
        print("✅ All cogs loaded.")

        # Create seen_users table
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS seen_users (
                    user_id TEXT PRIMARY KEY
                )
            ''')
            await db.commit()

        # Do NOT sync here — wait until on_ready once.

    async def on_interaction(self, interaction: discord.Interaction):
        # Welcome DM on first interaction
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

        # Let discord.py process slash commands as usual
        await super().on_interaction(interaction)

bot = FinancePal()

@bot.event
async def on_ready():
    print(f"✅ FinancePal is online as {bot.user} (ID: {bot.user.id})")
    print(f"Cogs loaded: {list(bot.extensions.keys())}")

    # One-time controlled sync to avoid duplicates
    if not bot._synced_once:
        if DEV_GUILD_ID:
            guild = discord.Object(id=int(DEV_GUILD_ID))
            # Clear local cache for that guild scope and sync only there (fast)
            bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"🔁 Synced commands to DEV guild {DEV_GUILD_ID}")
        else:
            # Global sync (slow to propagate; use only when ready)
            bot.tree.clear_commands()
            await bot.tree.sync()
            print("🌍 Synced global commands")
        bot._synced_once = True

# Admin-only resync command
@bot.tree.command(name="sync", description="Force-resync slash commands here.")
@app_commands.checks.has_permissions(administrator=True)
async def sync_cmd(interaction: discord.Interaction):
    if interaction.guild:
        guild = discord.Object(id=interaction.guild.id)
        bot.tree.clear_commands(guild=guild)
        await bot.tree.sync(guild=guild)
        await interaction.response.send_message("✅ Synced commands to this guild.", ephemeral=True)
    else:
        bot.tree.clear_commands()
        await bot.tree.sync()
        await interaction.response.send_message("✅ Synced global commands.", ephemeral=True)

bot.run(TOKEN)
