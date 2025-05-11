import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiosqlite
import os
import yfinance as yf

DB_PATH = "data/finance.db"
os.makedirs("data", exist_ok=True)

GUILD_ID = 857656646415024148

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS alerts (
            user_id TEXT,
            symbol TEXT,
            condition TEXT,
            target REAL
        )''')
        await db.commit()

class Alerts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(init_db())
        self.check_alerts.start()

    async def add_alert(self, user_id, symbol, condition, target):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO alerts VALUES (?, ?, ?, ?)", (user_id, symbol, condition, target))
            await db.commit()

    async def get_user_alerts(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT symbol, condition, target FROM alerts WHERE user_id = ?", (user_id,))
            return await cursor.fetchall()

    async def remove_alert(self, user_id, symbol, target):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute(
                "DELETE FROM alerts WHERE user_id = ? AND symbol = ? AND target = ?",
                (user_id, symbol, target)
            )
            await db.commit()
            return cursor.rowcount > 0

    async def clear_alerts(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM alerts WHERE user_id = ?", (user_id,))
            await db.commit()

    async def get_all_alerts(self):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT user_id, symbol, condition, target FROM alerts")
            return await cursor.fetchall()

    async def delete_alert_entry(self, user_id, symbol, target):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM alerts WHERE user_id = ? AND symbol = ? AND target = ?", (user_id, symbol, target))
            await db.commit()

    @app_commands.command(name="alert", description="Set a price alert for a stock or ETF.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def alert(self, interaction: discord.Interaction, symbol: str, condition: str, target: float):
        await interaction.response.defer(ephemeral=True)

        condition = condition.lower()
        if condition not in ["above", "below"]:
            await interaction.followup.send("❌ Condition must be `above` or `below`.", ephemeral=True)
            return

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if data.empty:
                raise ValueError("No data found")
        except Exception:
            await interaction.followup.send(f"❌ Could not validate `{symbol}`.", ephemeral=True)
            return

        await self.add_alert(str(interaction.user.id), symbol.upper(), condition, target)
        await interaction.followup.send(
            f"✅ Alert set: `{symbol.upper()}` {'>' if condition == 'above' else '<'} {target}",
            ephemeral=True
        )

    @app_commands.command(name="alert_list", description="View your active price alerts.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def alert_list(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        user_alerts = await self.get_user_alerts(user_id)

        if not user_alerts:
            await interaction.followup.send("📭 You have no active alerts.", ephemeral=True)
            return

        lines = [f"• `{symbol}` {'>' if condition == 'above' else '<'} {target}" for symbol, condition, target in user_alerts]
        await interaction.followup.send("📋 Your Alerts:\n" + "\n".join(lines), ephemeral=True)

    @app_commands.command(name="alert_remove", description="Remove a specific alert by symbol and target.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def alert_remove(self, interaction: discord.Interaction, symbol: str, target: float):
        await interaction.response.defer(ephemeral=True)
        success = await self.remove_alert(str(interaction.user.id), symbol.upper(), target)

        if success:
            await interaction.followup.send(
                f"🗑️ Removed alert for `{symbol.upper()}` at target {target}.",
                ephemeral=True
            )
        else:
            await interaction.followup.send("❌ No matching alert found.", ephemeral=True)

    @app_commands.command(name="clear_alerts", description="Remove all price alerts you’ve set.")
    @app_commands.guilds(discord.Object(id=GUILD_ID))
    async def clear_alerts_command(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        alerts = await self.get_user_alerts(user_id)
        if not alerts:
            await interaction.followup.send("📭 You have no active alerts to clear.", ephemeral=True)
            return

        await self.clear_alerts(user_id)
        await interaction.followup.send("🧹 All your alerts have been cleared.", ephemeral=True)

    @tasks.loop(minutes=5.0)
    async def check_alerts(self):
        all_alerts = await self.get_all_alerts()
        to_remove = []

        for user_id, symbol, condition, target in all_alerts:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period="1d")
                if data.empty:
                    continue
                current = data["Close"].iloc[-1]

                if (condition == "above" and current > target) or (condition == "below" and current < target):
                    user = await self.bot.fetch_user(int(user_id))
                    arrow = "📈" if condition == "above" else "📉"
                    await user.send(
                        f"{arrow} Alert: `{symbol}` is now at ${current:.2f} ({condition} {target})"
                    )
                    to_remove.append((user_id, symbol, target))
            except Exception:
                continue

        for user_id, symbol, target in to_remove:
            await self.delete_alert_entry(user_id, symbol, target)

    @check_alerts.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(Alerts(bot))
