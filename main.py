import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from typing import Literal
import aiosqlite

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
APP_ID = 1370900483174174780

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
        self._synced_once = False  # guard to avoid duplicate syncs on reconnects

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


bot = FinancePal()

@bot.listen("on_app_command_completion")
async def welcome_after_first_command(interaction: discord.Interaction, command: app_commands.Command):
    """Send a welcome DM the first time a user runs any app command."""
    if interaction.user and not interaction.user.bot:
        user_id = str(interaction.user.id)
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT 1 FROM seen_users WHERE user_id = ?", (user_id,))
            seen = await cur.fetchone()

            if not seen:
                try:
                    await interaction.user.send(
                        "**👋 Welcome to FinancePal!**\n\n"
                        "Use `/help` to view commands and `/settings` to personalize your experience.\n"
                        "Need help? Try `/info`."
                    )
                except discord.Forbidden:
                    pass  # DMs closed
                await db.execute("INSERT INTO seen_users (user_id) VALUES (?)", (user_id,))
                await db.commit()

@bot.event
async def on_ready():
    print(f"✅ FinancePal is online as {bot.user} (ID: {bot.user.id})")
    print(f"Cogs loaded: {list(bot.extensions.keys())}")

    if not bot._synced_once:
        bot.tree.clear_commands()   # clear local GLOBAL cache
        await bot.tree.sync()       # push GLOBAL commands
        print("🌍 Synced global commands")
        bot._synced_once = True

@bot.tree.command(name="sync", description="Resync slash commands. Defaults to global.")
@app_commands.checks.has_permissions(administrator=True)
async def sync_cmd(
    interaction: discord.Interaction,
    scope: Literal["global", "here"] = "global",
    purge_guild_first: bool = True,
):
    # Keep the interaction alive while we sync
    await interaction.response.defer(ephemeral=True, thinking=True)

    if scope == "here" and interaction.guild:
        guild = discord.Object(id=interaction.guild.id)
        if purge_guild_first:
            bot.tree.clear_commands(guild=guild)  # remove GUILD commands so only global remain
        await bot.tree.sync(guild=guild)          # (re)sync this guild scope
        await interaction.followup.send("🔁 Synced commands to **this guild**.", ephemeral=True)
    else:
        bot.tree.clear_commands()                 # clear local GLOBAL cache
        await bot.tree.sync()                     # push GLOBAL set
        await interaction.followup.send("🌍 Synced **global** commands.", ephemeral=True)

bot.run(TOKEN)
