import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import os
import yfinance as yf
import matplotlib.pyplot as plt
import io
import asyncio

DB_PATH = "data/finance.db"
os.makedirs("data", exist_ok=True)

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS watchlists (
                user_id TEXT,
                symbol TEXT
            )
        ''')
        await db.commit()

# ✅ Autocomplete setup
COMMON_TICKERS = [
    "AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "NVDA", "META",
    "VOO", "SPY", "QQQ", "QDV5.DE", "IE00BKM4GZ66"
]

async def autocomplete_ticker(interaction: discord.Interaction, current: str):
    current = current.upper()
    return [
        app_commands.Choice(name=ticker, value=ticker)
        for ticker in COMMON_TICKERS if current in ticker
    ][:10]

class Watchlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(init_db())

    async def get_watchlist(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute("SELECT symbol FROM watchlists WHERE user_id = ?", (user_id,))
            return [r[0] for r in await cursor.fetchall()]

    async def add_to_watchlist(self, user_id, symbol):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO watchlists (user_id, symbol) VALUES (?, ?)", (user_id, symbol))
            await db.commit()

    async def remove_from_watchlist(self, user_id, symbol):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM watchlists WHERE user_id = ? AND symbol = ?", (user_id, symbol))
            await db.commit()

    async def clear_watchlist(self, user_id):
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM watchlists WHERE user_id = ?", (user_id,))
            await db.commit()

    async def validate_ticker(self, stock):
        try:
            ticker = yf.Ticker(stock)
            hist = ticker.history(period="1d")
            if hist.empty and "." not in stock:
                alt_stock = stock + ".DE"
                alt_hist = yf.Ticker(alt_stock).history(period="1d")
                if not alt_hist.empty:
                    return alt_stock
            elif not hist.empty:
                return stock
        except Exception:
            pass
        return None

    async def format_price_line(self, symbol):
        try:
            hist = yf.Ticker(symbol).history(period="2d")
            if len(hist) >= 2:
                latest = hist["Close"].iloc[-1]
                prev = hist["Close"].iloc[-2]
                change = ((latest - prev) / prev) * 100
                return f"\u2022 `{symbol}` — ${latest:.2f} ({change:+.2f}%)"
        except Exception:
            pass
        return f"\u2022 `{symbol}` — \u26a0\ufe0f price unavailable"

    async def generate_chart(self, watchlist):
        plt.figure(figsize=(10, 6))
        success = False
        for symbol in watchlist[:10]:
            try:
                hist = yf.Ticker(symbol).history(period="30d")
                if not hist.empty:
                    plt.plot(hist.index, hist["Close"], label=symbol)
                    success = True
            except Exception:
                continue

        if not success:
            return None

        plt.title("Watchlist Performance (30d)")
        plt.xlabel("Date")
        plt.ylabel("Close Price")
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()
        return discord.File(buf, filename="watchlist_chart.png")

    @app_commands.command(name="add", description="Add a stock or ETF to your watchlist.")
    @app_commands.describe(stock="Stock or ETF symbol (e.g., AAPL, VOO, QDV5.DE)")
    @app_commands.autocomplete(stock=autocomplete_ticker)
    async def add(self, interaction: discord.Interaction, stock: str):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        stock = stock.upper()

        if len(stock) == 12 and stock[:2].isalpha() and stock[2:].isdigit():
            await interaction.followup.send(
                f"\u26a0\ufe0f `{stock}` looks like an ISIN. Use a stock symbol like `AAPL`, `MSFT`, or `QDV5.DE`.",
                ephemeral=True
            )
            return

        valid_stock = await self.validate_ticker(stock)
        if not valid_stock:
            await interaction.followup.send(f"\u274c Could not validate `{stock}`.", ephemeral=True)
            return

        watchlist = await self.get_watchlist(user_id)
        if valid_stock in watchlist:
            await interaction.followup.send(f"\u26a0\ufe0f `{valid_stock}` is already in your watchlist.", ephemeral=True)
            return

        await self.add_to_watchlist(user_id, valid_stock)
        await interaction.followup.send(f"\u2705 Added `{valid_stock}` to your watchlist.", ephemeral=True)

    @app_commands.command(name="list", description="View your watchlist with current prices or a performance chart.")
    async def list(self, interaction: discord.Interaction, chart: bool = False):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        watchlist = await self.get_watchlist(user_id)

        if not watchlist:
            await interaction.followup.send("\ud83d\udccd Your watchlist is empty.", ephemeral=True)
            return

        if chart:
            chart_file = await self.generate_chart(watchlist)
            if chart_file:
                await interaction.followup.send("\ud83d\udcca Here's your watchlist performance chart:", file=chart_file)
            else:
                await interaction.followup.send("\u274c Could not generate chart — no valid price data.", ephemeral=True)
            return

        rows = await asyncio.gather(*(self.format_price_line(symbol) for symbol in watchlist))
        await interaction.followup.send("\ud83d\udcc8 Your Watchlist:\n" + "\n".join(rows), ephemeral=True)

    @app_commands.command(name="remove", description="Remove a stock or ETF from your watchlist.")
    async def remove(self, interaction: discord.Interaction, stock: str):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        stock = stock.upper()

        watchlist = await self.get_watchlist(user_id)
        if stock not in watchlist:
            await interaction.followup.send(f"\u274c `{stock}` is not in your watchlist.", ephemeral=True)
            return

        await self.remove_from_watchlist(user_id, stock)
        await interaction.followup.send(f"\ud83d\uddd1\ufe0f Removed `{stock}` from your watchlist.", ephemeral=True)

    @app_commands.command(name="clear", description="Remove all assets from your watchlist.")
    async def clear(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)

        watchlist = await self.get_watchlist(user_id)
        if not watchlist:
            await interaction.followup.send("\ud83d\udc6d Your watchlist is already empty.", ephemeral=True)
            return

        await self.clear_watchlist(user_id)
        await interaction.followup.send("\ud83e\ude91 Your watchlist has been cleared.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Watchlist(bot))
