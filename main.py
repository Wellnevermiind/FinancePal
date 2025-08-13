# bot.py
import os
import asyncio
import logging
import discord
from discord.ext import commands
from discord import app_commands

###############################################################################
# CONFIG
###############################################################################
TOKEN = os.getenv("DISCORD_TOKEN") or "PUT_YOUR_TOKEN_HERE"

# Add your test guild(s) here for instant command availability
GUILD_IDS = [
    857656646415024148,  # Lounge
    1168450739044093953, # PS dev wallet tracker
    1204840433780269056, # FTBF
    1254567153449828442, # For Sell 1
    1372954937436147712, # FPS Legends
    1380605052552609915, # grow a garden
]

# Set to True for the FIRST RUN to clear stale global commands,
# then set to False afterwards.
NUKE_GLOBALS_ON_START = True

# List your cogs to load
COGS = [
    "cogs.core",
    "cogs.watchlist",
    "cogs.compare",
    "cogs.settings",
    "cogs.alerts",
    "cogs.info",
    "cogs.errors",
]

###############################################################################
# BOT SETUP
###############################################################################
logging.basicConfig(level=logging.INFO)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

class CoreHealthcheck(commands.Cog):
    def __init__(self, bot_: commands.Bot):
        self.bot = bot_

    @app_commands.command(name="ping", description="Health check")
    @app_commands.allowed_installs(guilds=True, users=False)
    @app_commands.allowed_contexts(guilds=True, dms=False, private_channels=False)
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"pong · app={interaction.client.application_id} · guild={interaction.guild_id}"
        )

async def load_cogs():
    for ext in COGS:
        try:
            await bot.load_extension(ext)
            logging.info("Loaded cog: %s", ext)
        except Exception as e:
            logging.exception("Failed to load cog %s: %s", ext, e)

async def hard_resync():
    """
    One-time 'nuke & repopulate' to fix Unknown Integration / missing commands.
    - Clears GLOBAL commands (once)
    - Syncs per-guild for instant visibility
    - Rebuilds globals
    """
    logging.info("🔧 Hard resync starting…")

    # Ensure /ping exists (avoid duplicates)
    tree_cmd_names = [c.name for c in bot.tree.get_commands()]
    if "ping" not in tree_cmd_names:
        await bot.add_cog(CoreHealthcheck(bot))

    if NUKE_GLOBALS_ON_START:
        logging.info("🌍 Current GLOBAL commands (pre-clear): %s", tree_cmd_names)
        bot.tree.clear_commands(guild=None)
        await bot.tree.sync()  # push empty global set
        logging.info("🧨 Cleared GLOBAL commands.")

    # Per-guild sync for fast availability
    for gid in GUILD_IDS:
        gobj = discord.Object(id=gid)
        cmds = await bot.tree.sync(guild=gobj)
        logging.info("✅ Synced to guild %s -> %s", gid, [f"{c.name}({c.id})" for c in cmds])

    # Rebuild globals from the current tree
    gcmds = await bot.tree.sync()
    logging.info("🌍 Globals after rebuild: %s", [f"{c.name}({c.id})" for c in gcmds])

    logging.info("🔧 Hard resync done.")

@bot.event
async def on_ready():
    # Print basic identity to avoid mixing up apps / client_ids
    app_id = bot.application_id
    logging.info("✅ %s is online as %s (ID: %s)", bot.user, bot.user, bot.user.id if bot.user else "unknown")
    logging.info("application_id: %s", app_id)

async def main():
    async with bot:
        # Load cogs first so their commands are present before we sync
        await load_cogs()

        # Do the resync routine to ensure commands appear and route correctly
        bot.loop.create_task(hard_resync())

        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
