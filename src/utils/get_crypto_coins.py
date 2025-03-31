import aiohttp
from datetime import datetime
from src.constants.locales import LEXICON
from src.constants.states import top_100_cache


# ------------------------ CoinGecko ------------------------
async def get_top_100_coins():
    global top_100_cache
    if top_100_cache:
        return top_100_cache
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {"vs_currency": "usd", "order": "market_cap_desc", "per_page": 100}
    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            if isinstance(data, list):
                top_100_cache = data
            else:
                top_100_cache = []
            return top_100_cache

async def get_crypto_prices(coin_ids):
    if not coin_ids:
        return {}
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(coin_ids),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(url, params=params) as response:
            return await response.json()

def build_price_message(data, language: str):
    if not data:
        return LEXICON[language]["no_data"]
    header = LEXICON[language]["current_prices_header"]
    updated_label = LEXICON[language]["updated_time"]
    message_parts = [f"{header}\n"]
    for coin, values in data.items():
        emoji = "🔸"
        price = values.get('usd', 'N/A')
        change = values.get('usd_24h_change', 0.0)
        change_icon = "📈" if change >= 0 else "📉"
        message_parts.append(
            f"{emoji} <b>{coin.title()}</b>\n"
            f"• ${price:,} | {change_icon} {change:.2f}% (24h)\n"
        )
    time_str = datetime.utcnow().strftime('%d.%m.%Y %H:%M (UTC)')
    message_parts.append(f"{updated_label} {time_str}")
    return "\n".join(message_parts)