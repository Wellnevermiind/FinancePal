import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import os

DB_PATH = "data/finance.db"
os.makedirs("data", exist_ok=True)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id TEXT PRIMARY KEY,
                currency TEXT DEFAULT 'USD',
                chart_days INTEGER DEFAULT 30,
                show_percentages INTEGER DEFAULT 1,
                watchlist_limit INTEGER DEFAULT 10
            )
        ''')
        await db.commit()

# Define the grouped commands
class SettingsGroup(app_commands.Group):
    def __init__(self, parent_cog):
        super().__init__(name="settings", description="Manage your FinancePal settings.")
        self.parent_cog = parent_cog

    @app_commands.command(name="view", description="View your FinancePal settings.")
    async def view(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        settings = await self.parent_cog.get_settings(user_id)

        if not settings:
            settings = {
                "currency": "USD",
                "chart_days": 30,
                "show_percentages": 1,
                "watchlist_limit": 10
            }

        embed = discord.Embed(
            title="⚙️ Your FinancePal Settings",
            description="Here are your current preferences:",
            color=0x3498db
        )
        embed.add_field(name="Currency", value=settings["currency"], inline=True)
        embed.add_field(name="Chart Days", value=settings["chart_days"], inline=True)
        embed.add_field(name="Show %", value="Yes" if settings["show_percentages"] else "No", inline=True)
        embed.add_field(name="Chart Ticker Limit", value=settings["watchlist_limit"], inline=True)
        embed.set_footer(text="Use /settings set to change these values.")

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="set", description="Change a FinancePal setting.")
    @app_commands.describe(
        field="Setting to change: currency, chart_days, show_percentages, watchlist_limit",
        value="New value for the setting (e.g., EUR, 30, true, or 5)"
    )
    async def set(self, interaction: discord.Interaction, field: str, value: str):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        valid_fields = {
            "currency": str,
            "chart_days": int,
            "show_percentages": lambda v: v.lower() in ("true", "1", "yes"),
            "watchlist_limit": int
        }

        if field not in valid_fields:
            await interaction.followup.send(
                "❌ Invalid setting. Valid options: currency, chart_days, show_percentages, watchlist_limit",
                ephemeral=True
            )
            return

        try:
            parser = valid_fields[field]
            parsed_value = parser(value)
        except Exception:
            await interaction.followup.send("❌ Invalid value for this setting.", ephemeral=True)
            return

        await self.parent_cog.save_setting(user_id, field, parsed_value)
        await interaction.followup.send(f"✅ `{field}` updated to `{value}`.", ephemeral=True)

# Main Cog
class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.tree.add_command(SettingsGroup(self))
        bot.loop.create_task(init_db())

    async def save_setting(self, user_id, field, value):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(f'''
                INSERT INTO user_settings (user_id, {field})
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET {field} = excluded.{field}
            ''', (user_id, value))
            await db.commit()

    async def get_settings(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT * FROM user_settings WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            if row:
                keys = [column[0] for column in cursor.description]
                return dict(zip(keys, row))
            return None

async def setup(bot):
    await bot.add_cog(Settings(bot))
