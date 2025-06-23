from discord.ext import commands

class Desync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("✅ Desync cog loaded")

    @commands.command()
    async def desync(self, ctx):
        """Clear all slash commands manually"""
        if ctx.author.id != ctx.guild.owner_id:
            await ctx.send("❌ You don’t have permission to run this.")
            return

        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()
        await ctx.send("✅ Cleared and resynced global slash commands.")

async def setup(bot):
    await bot.add_cog(Desync(bot))

# Legacy manual registration
def setup_legacy(bot):
    bot.add_command(Desync(bot).desync)
