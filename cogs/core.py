import discord
from discord.ext import commands
from discord import app_commands

class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Set up FinancePal for your server.")
    async def setup_cmd(self, interaction: discord.Interaction):
        description = (
            "FinancePal helps you track assets, set price alerts, and compare performance.\n\n"
            "[Terms of Service](https://pastebin.com/3815p2Mq) • "
            "[Privacy Policy](https://pastebin.com/fWjwdehp)\n\n"
            "Try: `/add` to track assets, `/alert` for price pings, `/aiadvisor` to ask about investing, "
            "and `/help` for the full list."
        )

        embed = discord.Embed(
            title="👋 Welcome to **FinancePal**!",
            description=description,
            color=0x745fed
        )
        embed.set_footer(text="Thank you for using FinancePal!")

        # Optional: buttons for quick access
        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Terms of Service", url="https://pastebin.com/3815p2Mq"))
        view.add_item(discord.ui.Button(label="Privacy Policy", url="https://pastebin.com/fWjwdehp"))

        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
