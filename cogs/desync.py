from discord.ext import commands

# This is a standalone command, not in a Cog class
@commands.command()
async def desync(ctx):
    """Clear all global slash commands manually."""
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("❌ You don’t have permission to run this.")
        return

    ctx.bot.tree.clear_commands(guild=None)
    await ctx.bot.tree.sync()
    await ctx.send("✅ Cleared and resynced global slash commands.")

# Manually register the command during setup_hook
def setup_legacy(bot):
    bot.add_command(desync)
