import discord
from discord.ext import commands
from discord import app_commands

class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Set up FinancePal for your server.")
    async def setup(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="👋 Welcome to **FinancePal**!",
            description=(
                "FinancePal is here to help you track assets, set price alerts, and compare stock performance."
                "By using FinancePal, you agree to our [Terms of Service](https://pastebin.com/3815p2Mq) and [Privacy Policy](https://pastebin.com/fWjwdehp)."
                "Use `/add` to track assets, `/alert` for price pings, and `/aiadvisor` to ask about investing."
                "Try `/help` for more.",
            ),
            color=0x745fed
        )
        embed.set_footer(text="Thank you for using FinancePal!")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="sync", description="Force command sync")
    async def sync(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        synced = await self.bot.tree.sync()
        await interaction.followup.send(f"🔁 Synced {len(synced)} global commands.")

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
