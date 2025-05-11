import discord
from discord.ext import commands
from discord import app_commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show an overview of all FinancePal commands.")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📘 FinancePal Help",
            description="Here are the available slash commands:",
            color=0x1abc9c
        )
        embed.add_field(name="/add", value="Add a stock or ETF to your watchlist.", inline=False)
        embed.add_field(name="/list", value="View your watchlist (optionally as a chart).", inline=False)
        embed.add_field(name="/remove", value="Remove a stock from your watchlist.", inline=False)
        embed.add_field(name="/clear", value="Clear your entire watchlist.", inline=False)

        embed.add_field(name="/compare", value="Compare 2–5 stocks or ETFs over time.", inline=False)

        embed.add_field(name="/alert", value="Set a price alert.", inline=False)
        embed.add_field(name="/alert_list", value="View your active alerts.", inline=False)
        embed.add_field(name="/alert_remove", value="Remove a specific alert.", inline=False)
        embed.add_field(name="/clear_alerts", value="Remove all your alerts.", inline=False)

        embed.add_field(name="/settings", value="View your personal preferences.", inline=False)
        embed.add_field(name="/set_setting", value="Change one of your bot settings.", inline=False)

        embed.add_field(name="/info", value="Learn what FinancePal is and who made it.", inline=False)

        embed.set_footer(text="Use /info for more about this bot.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="info", description="Learn what FinancePal is and who made it.")
    async def info(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="ℹ️ About FinancePal",
            description=(
                "FinancePal is your personal finance assistant on Discord — built to help you track stocks and ETFs.\n\n"
                "• 📈 Watchlist tracking\n"
                "• 🔔 Price alerts\n"
                "• 📊 Performance comparisons\n"
                "• ⚙️ Customizable user settings\n\n"
                "Made with ❤️ by nevermiind — student, programmer, and aspiring neuroscientist."
            ),
            color=0x3498db
        )

        embed.add_field(
            name="➕ Invite FinancePal",
            value="[Add to Server](https://discord.com/oauth2/authorize?client_id=1370900483174174780&permissions=274878265344&scope=bot+applications.commands)",
            inline=False
        )
        embed.add_field(
            name="💻 GitHub",
            value="[View Source Code](https://github.com/Wellnevermiind/FinancePal)",
            inline=False
        )
        embed.add_field(
            name="📬 Support",
            value="DM nevermiind on Discord or open a GitHub issue.",
            inline=False
        )
        embed.set_footer(text="Thank you for using FinancePal!")

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Info(bot))
