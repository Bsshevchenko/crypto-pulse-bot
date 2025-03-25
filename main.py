import os
import asyncio
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from database import init_db, add_user, set_language, set_user_coins

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_coins = {}
user_pages = {}


top_100_cache = []

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
            top_100_cache = data if isinstance(data, list) else []
            return top_100_cache


async def get_crypto_prices(coin_ids):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(coin_ids), "vs_currencies": "usd", "include_24hr_change": "true"}
    conn = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(url, params=params) as response:
            return await response.json()


def build_price_message(data):
    message_parts = ["🚀 <b>Текущий курс криптовалют:</b>\n"]
    for coin, values in data.items():
        emoji = "🔸"
        price = values.get('usd', 'N/A')
        change = values.get('usd_24h_change', 0.0)  # Устанавливаем значение по умолчанию
        change_icon = "📈" if change >= 0 else "📉"
        message_parts.append(
            f"{emoji} <b>{coin.title()}</b>\n• ${price:,} | {change_icon} {change:.2f}% (24ч)\n"
        )
    time = datetime.utcnow().strftime('%d.%m.%Y %H:%M (UTC)')
    message_parts.append(f"⏰ Обновлено: {time}")
    return '\n'.join(message_parts)



async def coins_keyboard(page=0, per_page=15, selected_coins=None):
    if selected_coins is None:
        selected_coins = set()

    coins_data = await get_top_100_coins()

    total_coins = len(coins_data)
    total_pages = (total_coins - 1) // per_page

    # Корректное ограничение страницы
    page = max(0, min(page, total_pages))

    start = page * per_page
    end = min(start + per_page, total_coins)

    keyboard_buttons = []
    row = []

    for coin in coins_data[start:end]:
        coin_id = coin['id']
        symbol = coin['symbol'].upper()
        prefix = "✅" if coin_id in selected_coins else "🔸"
        row.append(InlineKeyboardButton(
            text=f"{prefix} {symbol}",
            callback_data=f"coin_{coin_id}_{page}")
        )
        if len(row) == 3:
            keyboard_buttons.append(row)
            row = []
    if row:
        keyboard_buttons.append(row)

    # Чёткая логика навигации по страницам
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(InlineKeyboardButton(text="← Назад", callback_data=f"page_{page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton(text="Вперед →", callback_data=f"page_{page + 1}"))
    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await add_user(message.from_user.id, message.from_user.username)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
    ])

    await message.answer("Please, choose your language:\nПожалуйста, выберите язык:", reply_markup=keyboard)


@dp.callback_query(lambda c: c.data.startswith('lang_'))
async def set_user_language(callback: CallbackQuery):
    lang = callback.data.split("_")[1]
    await set_language(callback.from_user.id, lang)

    text = "✅ Language set to English. Choose coins to monitor (up to 3):" if lang == 'en' else \
        "✅ Язык установлен на русский. Выберите монеты для мониторинга (до 3):"

    user_pages[callback.from_user.id] = 0
    keyboard = await coins_keyboard(page=0)
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('coin_'))
async def set_coins(callback: CallbackQuery):
    parts = callback.data.split("_")
    coin = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0

    user_id = callback.from_user.id
    user_coins.setdefault(user_id, set())
    user_pages[user_id] = page

    if coin in user_coins[user_id]:
        user_coins[user_id].remove(coin)
    else:
        if len(user_coins[user_id]) >= 3:
            await callback.answer("⚠️ Maximum 3 coins selected!", show_alert=True)
            return
        user_coins[user_id].add(coin)

    keyboard = await coins_keyboard(page=page, selected_coins=user_coins[user_id])
    await callback.message.edit_reply_markup(reply_markup=keyboard)

    if len(user_coins[user_id]) == 3:
        await set_user_coins(user_id, list(user_coins[user_id]))
        prices = await get_crypto_prices(user_coins[user_id])
        msg = build_price_message(prices)
        await callback.message.answer(msg)

    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith('page_'))
async def paginate_coins(callback: CallbackQuery):
    page = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    user_pages[user_id] = page
    selected = user_coins.get(user_id, set())
    keyboard = await coins_keyboard(page=page, selected_coins=selected)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


async def main():
    print("🤖 Bot started!")
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
