import discord
from discord.ext import commands
from discord import app_commands

class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Set up FinancePal for your server.")
    async def setup(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "👋 Welcome to **FinancePal**!\nUse `/add` to track assets, `/alert` for price pings, and `/aiadvisor` to ask about investing.\nTry `/help` for more.",
            ephemeral=True
        )

    @app_commands.command(name="sync", description="Force command sync")
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        synced = await self.bot.tree.sync()
        await interaction.followup.send(f"🔁 Synced {len(synced)} global commands.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
