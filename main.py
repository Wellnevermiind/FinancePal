import os
import sys
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from typing import Literal
import aiosqlite
import os, sys
import base64

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
parts = TOKEN.split(".")
if len(parts) != 3:
    print(f"❌ Token format unexpected: got {len(parts)} segments (expected 3). Re-copy from Bot tab.")
    sys.exit(1)

seg0 = parts[0]
pad = "=" * (-len(seg0) % 4)
try:
    decoded_id = base64.urlsafe_b64decode(seg0 + pad).decode("ascii")
except Exception as e:
    print(f"❌ Couldn't decode token segment0: {e}")
    sys.exit(1)

env_app_id = os.getenv("APP_ID", "").strip()
print(f"🔎 Token decodes to ID: {decoded_id}")
if env_app_id and decoded_id != env_app_id:
    print(f"❌ Token belongs to a DIFFERENT application (token ID {decoded_id} != APP_ID {env_app_id}).")
    print("   Use the Bot token from the *same* app you’re deploying, or update APP_ID to match.")
    sys.exit(1)
if not TOKEN:
    print(f"ℹ️ CWD: {os.getcwd()}")
    print(f"ℹ️ .env path tried: {os.path.join(os.path.dirname(__file__), '.env')}")
    print(f"ℹ️ DISCORD_TOKEN present in env? {'yes' if 'DISCORD_TOKEN' in os.environ else 'no'}")
    print("❌ DISCORD_TOKEN missing.")
    sys.exit(1)

if any(c in TOKEN for c in ['"', "'", "\n", "\r"]) or " " in TOKEN or len(TOKEN) < 50:
    print("❌ DISCORD_TOKEN malformed (quotes/newlines/spaces/too short). Paste exactly the Bot token.")
    print("🔍 Raw char summary:", {"len": len(TOKEN),
                                   "has_quote": any(c in TOKEN for c in ['"', "'"]),
                                   "has_newline": any(c in TOKEN for c in ['\n', '\r']),
                                   "has_space": " " in TOKEN})
    sys.exit(1)
if len(TOKEN) < 50 or " " in TOKEN:
    print("❌ DISCORD_TOKEN looks malformed (too short or contains spaces). Re-copy it from the Bot tab.")
    sys.exit(1)

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
    print(f"✅ FinancePal is online as {bot.user} (ID: {bot.user.id})")
    print(f"application_id: {bot.application_id}")
    print(f"Cogs loaded: {list(bot.extensions.keys())}")

    env_app_id = os.getenv("APP_ID")
    if env_app_id and int(env_app_id) != (bot.application_id or 0):
        print("❌ APP_ID mismatch: env APP_ID doesn't match the logged-in application's ID.")
        await bot.close()
        sys.exit(1)

    if not bot._synced_once:
        # 1️⃣ Push clean GLOBAL commands first
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()
        print("🌍 Synced global commands")

        # 2️⃣ Immediately overwrite per-guild registry to point to the new commands
        for g in bot.guilds:
            try:
                bot.tree.clear_commands(guild=g)
                await bot.tree.sync(guild=g)
                print(f"🔁 Synced commands to guild: {g.name} ({g.id})")
            except Exception as e:
                print(f"⚠️ Guild sync failed for {g.name} ({g.id}): {e}")

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

print("🔍 Token preview (masked):", f"{TOKEN[:8]}...{TOKEN[-6:]} (len={len(TOKEN)})")
bot.run(TOKEN)
