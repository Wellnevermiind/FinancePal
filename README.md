<p align="center">
  <img src="https://media.discordapp.net/attachments/859845219163176961/1370943923714916496/FinancePal_Logo_Final.png?ex=68215686&is=68200506&hm=06425e7cb7d662bbfab4c4ecac7d3ff0af2659652c349e5f7e65aa85675da4cd&=&format=webp&quality=lossless&width=1008&height=1008" width="240" />
</p>

<h1 align="center">FinancePal</h1>

<p align="center">
  🤖 Your AI-powered finance assistant for Discord — track stocks, set price alerts, and compare tickers with ease.
</p>

---

## ✨ Features

- 📈 Personal watchlist tracking (`/add`, `/list`, `/remove`)
- 🔔 Smart price alerts with automatic DMs
- 📊 Clean comparison charts for up to 5 tickers
- ⚙️ User settings to personalize your experience
- 💬 Friendly slash commands (no spam, no clutter)

---

## 🚀 Get Started

> Click to invite the bot to your server:

[![Invite FinancePal](https://img.shields.io/badge/Invite-FinancePal-745fed?style=for-the-badge&logo=discord)](https://discord.com/oauth2/authorize?client_id=1370900483174174780&permissions=274878265344&scope=bot+applications.commands)

---

## 💡 Example Commands

| Command          | Description                                   |
|------------------|-----------------------------------------------|
| `/add AAPL`      | Add Apple to your personal watchlist          |
| `/list`          | Show current prices (or `/list chart`)        |
| `/compare`       | Compare 2–5 tickers on a price chart          |
| `/alert`         | Set a price alert (e.g. TSLA above 800)       |
| `/settings`      | View your preferences                         |
| `/update_setting`| Change chart days, currency, etc.             |

---

## 🧠 About

FinancePal is a lightweight, privacy-conscious bot built with:
- `discord.py` 2.x
- `yfinance`, `matplotlib`, `aiosqlite`

Created with ❤️ by [nevermiind](https://github.com/Wellnevermiind) — student and programmer.

## DISCLAIMER
FinancePal provides stock and financial data for informational purposes only. The information, tools, and features provided by the bot, including stock prices, charts, and comparisons, are not intended as investment advice or recommendations.

FinancePal does not guarantee the accuracy, completeness, or timeliness of the data provided. Users should perform their own research or consult a licensed financial advisor before making any investment decisions.

Data Sources: FinancePal sources financial data from publicly available APIs (such as Yahoo Finance, Alpha Vantage, etc.). These data sources may have restrictions on their commercial use. By using this bot, you agree to comply with the terms of service of the respective data providers.

Limitation of Liability: FinancePal, its developers, and contributors are not responsible for any financial losses or damages arising from the use of this bot. All decisions made based on the information provided by FinancePal are solely the responsibility of the user.

---

## 🛠️ Developer Setup

```bash
git clone https://github.com/Wellnevermiind/FinancePal.git
cd FinancePal
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt'''
