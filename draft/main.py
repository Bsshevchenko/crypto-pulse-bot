import os
import aiohttp
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")

# Создание бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Получение текущих курсов валют с CoinGecko
async def get_crypto_prices():
    params = {
        'ids': 'bitcoin,ethereum,solana',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    conn = aiohttp.TCPConnector(ssl=False)  # Отключает проверку SSL!
    async with aiohttp.ClientSession(connector=conn) as session:
        async with session.get(API_URL, params=params) as response:
            return await response.json()


# Определение значка изменения
def get_change_icon(change):
    return "📈" if change >= 0 else "📉"

# Команда /price
@dp.message(Command("price"))
async def send_crypto_prices(message: Message):
    data = await get_crypto_prices()

    btc = data['bitcoin']
    eth = data['ethereum']
    sol = data['solana']
    time = datetime.utcnow().strftime('%d.%m.%Y %H:%M (UTC)')

    msg = (
        f"🚀 <b>Текущий курс криптовалют:</b>\n\n"
        f"💎 <b>Bitcoin (BTC)</b>\n"
        f"• ${btc['usd']:,} | {get_change_icon(btc['usd_24h_change'])} {btc['usd_24h_change']:.2f}% (24ч)\n\n"
        f"♦️ <b>Ethereum (ETH)</b>\n"
        f"• ${eth['usd']:,} | {get_change_icon(eth['usd_24h_change'])} {eth['usd_24h_change']:.2f}% (24ч)\n\n"
        f"🔷 <b>Solana (SOL)</b>\n"
        f"• ${sol['usd']:,} | {get_change_icon(sol['usd_24h_change'])} {sol['usd_24h_change']:.2f}% (24ч)\n\n"
        f"⏰ Обновлено: {time}"
    )

    await message.answer(msg)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        "👋 Привет! Я твой крипто-помощник.\n\n"
        "📌 Чтобы узнать текущий курс криптовалют (BTC, ETH, SOL), отправь команду /price"
    )
    await message.answer(welcome_text)


# Запуск бота
async def main():
    print("🤖 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
