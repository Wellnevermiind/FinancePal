import discord
from discord.ext import commands
from discord import app_commands
import yfinance as yf
import matplotlib.pyplot as plt
import io

# Shared autocomplete list
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

class Compare(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="compare",
        description="Compare up to 5 stocks/ETFs on a custom time chart."
    )
    @app_commands.describe(
        symbol1="Required first ticker",
        symbol2="Required second ticker",
        symbol3="Optional third ticker",
        symbol4="Optional fourth ticker",
        symbol5="Optional fifth ticker",
        period="Period (e.g., 7d, 1mo, 3mo, 1y)"
    )
    @app_commands.autocomplete(
        symbol1=autocomplete_ticker,
        symbol2=autocomplete_ticker,
        symbol3=autocomplete_ticker,
        symbol4=autocomplete_ticker,
        symbol5=autocomplete_ticker
    )
    async def compare(
        self,
        interaction: discord.Interaction,
        symbol1: str,
        symbol2: str,
        symbol3: str = None,
        symbol4: str = None,
        symbol5: str = None,
        period: str = "30d"
    ):
        await interaction.response.defer(ephemeral=True)

        tickers = [s for s in [symbol1, symbol2, symbol3, symbol4, symbol5] if s]
        if len(tickers) < 2 or len(tickers) > 5:
            await interaction.followup.send("❌ Please provide between 2 and 5 symbols.", ephemeral=True)
            return

        plt.figure(figsize=(10, 6))
        success = False

        for original_symbol in tickers:
            symbol = original_symbol
            try:
                data = yf.Ticker(symbol).history(period=period)

                if data.empty and "." not in symbol:
                    alt_symbol = symbol + ".DE"
                    alt_data = yf.Ticker(alt_symbol).history(period=period)
                    if not alt_data.empty:
                        symbol = alt_symbol
                        data = alt_data

                if not data.empty:
                    plt.plot(data.index, data["Close"], label=original_symbol)
                    success = True
            except Exception:
                continue

        if not success:
            await interaction.followup.send(
                "❌ Couldn't fetch valid price data for any of the provided symbols.",
                ephemeral=True
            )
            return

        plt.title(f"Price Comparison ({period})")
        plt.xlabel("Date")
        plt.ylabel("Close Price (USD or Local Currency)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close()

        chart_file = discord.File(buf, filename="comparison.png")
        await interaction.followup.send("Here's your comparison chart:", file=chart_file)

async def setup(bot):
    await bot.add_cog(Compare(bot))
