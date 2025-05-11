import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 857656646415024148  # your server
APP_ID = 1370900483174174780   # your app id from Discord Dev Portal

intents = discord.Intents.default()
intents.message_content = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=APP_ID,
        )

    async def setup_hook(self):
        # Register slash command
        @self.tree.command(name="hello", description="Test command", guild=discord.Object(id=GUILD_ID))
        async def hello(interaction: discord.Interaction):
            await interaction.response.send_message("👋 Hello from discord.py!", ephemeral=True)


        # Sync instantly to your test server
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"✅ Synced commands to guild {GUILD_ID}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

bot.run(TOKEN)
