import discord
from discord.ext import commands
from discord import app_commands

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @bot.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.CommandOnCooldown):
                await interaction.response.send_message(
                    f"⏳ This command is on cooldown. Try again in {round(error.retry_after)} seconds.",
                    ephemeral=True
                )

            elif isinstance(error, app_commands.MissingPermissions):
                await interaction.response.send_message(
                    "🚫 You don't have permission to use this command.",
                    ephemeral=True
                )

            elif isinstance(error, app_commands.BotMissingPermissions):
                await interaction.response.send_message(
                    "⚠️ I’m missing permissions to do that. Please check my role and channel settings.",
                    ephemeral=True
                )

            elif isinstance(error, app_commands.CommandInvokeError):
                original = error.original
                print(f"CommandInvokeError: {original}")
                await interaction.response.send_message(
                    "❌ Something went wrong while running that command. Try again later.",
                    ephemeral=True
                )

            else:
                print(f"Unhandled error: {error}")
                await interaction.response.send_message(
                    "⚠️ An unknown error occurred. Let the developer know if this keeps happening.",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
