import os
import sys
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from typing import Literal
import aiosqlite

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

DB_PATH = "data/finance.db"
os.makedirs("data", exist_ok=True)

class FinancePal(commands.Bot):
    def __init__(self):
        # IMPORTANT: don't pass application_id; let discord.py fetch it from the token
        super().__init__(command_prefix="!", intents=intents)
        self._synced_once = False  # guard to avoid duplicate syncs on reconnects

    async def setup_hook(self):
        print("🔄 Loading cogs...")
        # Cogs must NOT call tree.sync() themselves.
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
    # Sanity: after login, discord.py sets bot.application_id
    print(f"✅ FinancePal is online as {bot.user} (ID: {bot.user.id})")
    print(f"application_id: {bot.application_id}")
    print(f"Cogs loaded: {list(bot.extensions.keys())}")

    # Optional hard guard: if you still keep APP_ID in env, verify match
    env_app_id = os.getenv("APP_ID")
    if env_app_id and int(env_app_id) != (bot.application_id or 0):
        print("❌ APP_ID mismatch: env APP_ID doesn't match the logged-in application's ID.")
        await bot.close()
        sys.exit(1)

    if not bot._synced_once:
        # Clear local GLOBAL cache and publish GLOBAL commands
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("🌍 Synced global commands")
        bot._synced_once = True

# Simple responsiveness check
@bot.tree.command(name="ping", description="Check if the bot is responsive.")
async def ping_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!", ephemeral=True)

@bot.tree.command(name="sync", description="Resync slash commands. Defaults to global.")
@app_commands.checks.has_permissions(administrator=True)
async def sync_cmd(
    interaction: discord.Interaction,
    scope: Literal["global", "here", "purge_all"] = "global",
    purge_guild_first: bool = True,
):
    """Resync commands.
    - global: publish global registry
    - here: clear & sync just this guild
    - purge_all: clear every joined guild registry, then publish global
    """
    await interaction.response.defer(ephemeral=True, thinking=True)

    try:
        if scope == "here" and interaction.guild:
            guild = discord.Object(id=interaction.guild.id)
            if purge_guild_first:
                bot.tree.clear_commands(guild=guild)
            await bot.tree.sync(guild=guild)
            await interaction.followup.send("🔁 Synced commands to **this guild**.", ephemeral=True)

        elif scope == "purge_all":
            # Remove guild-scoped registries everywhere to get rid of stale dev copies
            purged = 0
            for g in bot.guilds:
                bot.tree.clear_commands(guild=g)
                await bot.tree.sync(guild=g)
                purged += 1
            # Re-publish global
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
            await interaction.followup.send(f"🧹 Purged {purged} guild registries and synced **global**.", ephemeral=True)

        else:
            # Global default
            bot.tree.clear_commands(guild=None)
            await bot.tree.sync()
            await interaction.followup.send("🌍 Synced **global** commands.", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"⚠️ Sync failed: `{type(e).__name__}: {e}`", ephemeral=True)

bot.run(TOKEN)
