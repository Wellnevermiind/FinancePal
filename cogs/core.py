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

    @app_commands.command(name="help", description="Show help for FinancePal.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📘 FinancePal Help",
            description="Here are some useful commands:",
            color=0x00ff99
        )
        embed.add_field(name="/setup", value="Intro + quickstart guide", inline=False)
        embed.add_field(name="/add", value="Add an asset to your watchlist", inline=False)
        embed.add_field(name="/list", value="View your watchlist", inline=False)
        embed.add_field(name="/remove", value="Remove an asset from your watchlist", inline=False)
        embed.set_footer(text="More features are on the way!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
