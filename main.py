# bot.py
import os
import asyncio
import logging
import urllib.parse

import discord
from discord.ext import commands
from discord import app_commands

# ──────────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────────
TOKEN = os.getenv("DISCORD_TOKEN") or "PUT_YOUR_TOKEN_HERE"

GUILD_IDS = [
    857656646415024148,  # Lounge
    1168450739044093953, # PS dev wallet tracker
    1204840433780269056, # FTBF
    1254567153449828442, # For Sell 1
    1372954937436147712, # FPS Legends
    1380605052552609915, # grow a garden
]

BOT_PERMISSIONS = (
    discord.Permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        use_external_emojis=True,
    ).value
)

# Build static discord.Object list for @app_commands.guilds()
GUILDS = [discord.Object(id=g) for g in GUILD_IDS]

# ──────────────────────────────────────────────────────────────────────────────
# LOGGING / BOT
# ──────────────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("financepal")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def build_invite_url(application_id: int) -> str:
    base = "https://discord.com/api/oauth2/authorize"
    params = {
        "client_id": str(application_id),
        "scope": "bot applications.commands",
        "permissions": str(BOT_PERMISSIONS),
        # You can pin a server for safety:
        # "guild_id": "857656646415024148",
        # "disable_guild_select": "true",
    }
    return f"{base}?{urllib.parse.urlencode(params)}"

# ──────────────────────────────────────────────────────────────────────────────
# COGS + a guaranteed /ping (guild-scoped)
# ──────────────────────────────────────────────────────────────────────────────
class CoreHealthcheck(commands.Cog):
    def __init__(self, bot_: commands.Bot):
        self.bot = bot_

    # Make /ping a *guild command* so it shows quickly and unambiguously
    @app_commands.guilds(*GUILDS)
    @app_commands.command(name="ping", description="Health check")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"pong · app={interaction.client.application_id} · guild={interaction.guild_id}"
        )

async def load_cogs():
    exts = [
        "cogs.core",
        "cogs.watchlist",
        "cogs.compare",
        "cogs.settings",
        "cogs.alerts",
        "cogs.info",
        "cogs.errors",
    ]
    for ext in exts:
        try:
            await bot.load_extension(ext)
            log.info("Loaded cog: %s", ext)
        except Exception as e:
            log.exception("Failed to load cog %s: %s", ext, e)

async def print_guild_commands(phase: str):
    for gid in GUILD_IDS:
        try:
            cmds = await bot.tree.fetch_commands(guild=discord.Object(id=gid))
            log.info("[%s] Guild %s commands: %s", phase, gid, [f"{c.name}({c.id})" for c in cmds])
        except Exception as e:
            log.error("[%s] fetch guild %s commands failed: %s", phase, gid, e)

async def sync_guilds():
    # Ensure /ping is present (avoids duplicate registration)
    if not any(isinstance(c, CoreHealthcheck) for c in bot.cogs.values()):
        await bot.add_cog(CoreHealthcheck(bot))

    await print_guild_commands("pre-sync")

    # Sync only to the listed guilds (fast)
    for gid in GUILD_IDS:
        gobj = discord.Object(id=gid)
        cmds = await bot.tree.sync(guild=gobj)
        log.info("✅ Synced to guild %s -> %s", gid, [f"{c.name}({c.id})" for c in cmds])

    await print_guild_commands("post-sync")

@bot.event
async def on_ready():
    app_id = bot.application_id
    log.info("✅ Logged in as %s (user id: %s)", bot.user, bot.user.id if bot.user else "unknown")
    log.info("application_id: %s", app_id)
    log.info("🔗 Invite THIS app with: %s", build_invite_url(app_id))
    # Start sync
    asyncio.create_task(sync_guilds())

async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
