import os
import asyncio
import aiohttp
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from database import init_db, add_user, set_language, set_user_coins, count_users
from constants.admins import ADMINS

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Память в рантайме: для хранения выбранных пользователями монет и текущих страниц
user_coins = {}   # user_id -> set(['btc', 'eth', ...])
user_pages = {}   # user_id -> int (номер текущей страницы)
top_100_cache = []  # Кэш для списка монет (обновляется при первом запросе)

# Клавиатура для быстрого доступа к некоторым командам
menu_buttons = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="/price"),
            KeyboardButton(text="/choice_coin"),
            KeyboardButton(text="/menu")
        ]
    ],
    resize_keyboard=True
)

# ======================== Функции для работы с CoinGecko ========================

async def get_top_100_coins():
    """Получаем топ-100 монет с CoinGecko (кэшируем результат)."""
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
    """Получаем цены для списка монет по ID."""
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

def build_price_message(data):
    """Формируем сообщение со списком монет и их ценами."""
    if not data:
        return "Нет данных по выбранным монетам."
    message_parts = ["🚀 <b>Текущий курс криптовалют:</b>\n"]
    for coin, values in data.items():
        emoji = "🔸"
        price = values.get('usd', 'N/A')
        change = values.get('usd_24h_change', 0.0)
        change_icon = "📈" if change >= 0 else "📉"
        message_parts.append(
            f"{emoji} <b>{coin.title()}</b>\n"
            f"• ${price:,} | {change_icon} {change:.2f}% (24ч)\n"
        )
    time = datetime.utcnow().strftime('%d.%m.%Y %H:%M (UTC)')
    message_parts.append(f"⏰ Обновлено: {time}")
    return '\n'.join(message_parts)

# ======================== Клавиатура выбора монет ========================

async def coins_keyboard(page=0, per_page=15, selected_coins=None):
    """
    Создаём InlineKeyboard для выбора монет:
      - 15 монет на странице.
      - Переход по страницам (назад-вперёд).
      - Кнопка сбросить выбор.
      - Кнопка подтвердить выбор (сохранение и генерация цены).
    """
    if selected_coins is None:
        selected_coins = set()

    coins_data = await get_top_100_coins()
    total_coins = len(coins_data)
    total_pages = (total_coins - 1) // per_page if total_coins else 0

    # Убедимся, что страница не выходит за границы
    page = max(0, min(page, total_pages))
    start = page * per_page
    end = min(start + per_page, total_coins)

    keyboard_buttons = []
    row = []

    # Формируем кнопки для монет
    for coin in coins_data[start:end]:
        coin_id = coin['id']
        symbol = coin['symbol'].upper()
        prefix = "✅" if coin_id in selected_coins else "🔸"
        row.append(InlineKeyboardButton(
            text=f"{prefix} {symbol}",
            callback_data=f"coin_{coin_id}_{page}"
        ))
        if len(row) == 3:
            keyboard_buttons.append(row)
            row = []

    if row:
        keyboard_buttons.append(row)

    # Кнопки навигации по страницам
    navigation_buttons = []
    if page > 0:
        navigation_buttons.append(
            InlineKeyboardButton(text="← Назад", callback_data=f"page_{page - 1}")
        )
    if page < total_pages:
        navigation_buttons.append(
            InlineKeyboardButton(text="Вперед →", callback_data=f"page_{page + 1}")
        )
    if navigation_buttons:
        keyboard_buttons.append(navigation_buttons)

    # Кнопки управления
    control_buttons = []
    if selected_coins:
        control_buttons.append(
            InlineKeyboardButton(text="🔄 Сбросить выбор", callback_data="reset_selection")
        )
        control_buttons.append(
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_selection")
        )
    if control_buttons:
        keyboard_buttons.append(control_buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

# ======================== Обработчики команд ========================

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """
    Команда /start:
      - Добавляем пользователя в БД,
      - Просим выбрать язык,
      - Даём меню для удобства.
    """
    await add_user(message.from_user.id, message.from_user.username)

    # Предлагаем выбрать язык
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
            ]
        ]
    )
    await message.answer(
        "Please, choose your language:\nПожалуйста, выберите язык:",
        reply_markup=keyboard
    )

    # Предлагаем меню
    await message.answer(
        "Используйте меню ниже для быстрого доступа к командам.",
        reply_markup=menu_buttons
    )

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    """
    Команда /menu: краткая справка по командам.
    """
    commands = [
        "/start - Начать работу с ботом",
        "/choice_coin - Выбрать/изменить выбор монет",
        "/price - Посмотреть цену на выбранные монеты",
        "/userStats - Статистика по пользователям (для админов)"
    ]
    await message.answer(
        "📋 Доступные команды:\n" + "\n".join(commands),
        reply_markup=menu_buttons
    )

@dp.message(Command("choice_coin"))
async def choice_coin(message: Message):
    """
    Команда /choice_coin: открываем панель выбора монет.
    """
    user_id = message.from_user.id
    # Если у пользователя уже есть выбор, оставим его. Если нет, то создадим пустой.
    if user_id not in user_coins:
        user_coins[user_id] = set()
    # Текущая страница — 0 (начинаем с первой)
    user_pages[user_id] = 0

    keyboard = await coins_keyboard(page=0, selected_coins=user_coins[user_id])
    await message.answer(
        "🔸 Выберите монеты для мониторинга (до 3-х). Потом нажмите «Подтвердить».",
        reply_markup=keyboard
    )

@dp.message(Command("price"))
async def price_command(message: Message):
    """
    Команда /price: показываем текущую цену по сохранённым монетам пользователя.
    """
    user_id = message.from_user.id
    selected = user_coins.get(user_id)

    # Если монеты не выбраны, просим выбрать
    if not selected:
        await message.answer(
            "⚠️ Сначала выберите монеты с помощью /choice_coin.",
            reply_markup=menu_buttons
        )
        return

    prices = await get_crypto_prices(selected)
    msg = build_price_message(prices)
    await message.answer(msg, reply_markup=menu_buttons)

@dp.message(Command("userStats"))
async def cmd_user_stats(message: Message):
    """
    Команда /userStats: показывает количество пользователей бота.
    Дополнительно можно проверять, является ли пользователь админом.
    """
    if str(message.from_user.id) not in ADMINS:
        # Если пользователь не админ, отказываем
        await message.reply("🚫 Доступ запрещён")
        return

    count = await count_users()
    await message.answer(f"📊 Количество пользователей бота: <b>{count}</b>")

# ======================== Обработчики CallbackQuery ========================

@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_user_language(callback: CallbackQuery):
    """
    Выбор языка в CallbackQuery.
    """
    lang = callback.data.split("_", 1)[1]
    await set_language(callback.from_user.id, lang)

    if lang == 'en':
        text = (
            "✅ Language set to English. "
            "Use /choice_coin to pick coins (up to 3)."
        )
    else:
        text = (
            "✅ Язык установлен на русский. "
            "Воспользуйтесь /choice_coin для выбора монет (до 3)."
        )

    await callback.message.answer(text, reply_markup=menu_buttons)
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("coin_"))
async def select_coin_callback(callback: CallbackQuery):
    """
    При нажатии на монетку в списке.
    Добавляем/удаляем её из выбора, но НЕ показываем цены сразу.
    """
    parts = callback.data.split("_")
    coin_id = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0

    user_id = callback.from_user.id
    user_coins.setdefault(user_id, set())
    user_pages[user_id] = page

    # Если монета уже выбрана, убираем из набора
    if coin_id in user_coins[user_id]:
        user_coins[user_id].remove(coin_id)
    else:
        # Максимум 3 монеты
        if len(user_coins[user_id]) >= 3:
            await callback.answer("⚠️ Maximum 3 coins selected!", show_alert=True)
            return
        user_coins[user_id].add(coin_id)

    # Обновляем inline-клавиатуру, показывая текущее состояние выбора
    keyboard = await coins_keyboard(
        page=page,
        selected_coins=user_coins[user_id]
    )
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "reset_selection")
async def reset_selection(callback: CallbackQuery):
    """
    Сброс выбранных монет до пустого набора.
    """
    user_id = callback.from_user.id
    user_coins[user_id] = set()
    page = user_pages.get(user_id, 0)
    keyboard = await coins_keyboard(page=page, selected_coins=set())
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer("Выбор сброшен")

@dp.callback_query(lambda c: c.data.startswith("page_"))
async def paginate_coins(callback: CallbackQuery):
    """
    Переход по страницам выбора монет.
    """
    page = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    user_pages[user_id] = page

    selected = user_coins.get(user_id, set())
    keyboard = await coins_keyboard(page=page, selected_coins=selected)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "confirm_selection")
async def confirm_selection(callback: CallbackQuery):
    """
    При нажатии «Подтвердить»:
      - Сохраняем выбор в БД,
      - Генерируем цены,
      - Убираем панель (инлайн-клавиатуру),
      - Отправляем сообщение с ценой.
    """
    user_id = callback.from_user.id
    selected = user_coins.get(user_id, set())

    if not selected:
        await callback.answer("⚠️ Выберите хотя бы одну монету!", show_alert=True)
        return

    # Сохраняем выбор в БД
    await set_user_coins(user_id, list(selected))

    # Получаем цены выбранных монет
    prices = await get_crypto_prices(selected)
    msg = build_price_message(prices)

    # Убираем инлайн-клавиатуру
    await callback.message.edit_reply_markup(reply_markup=None)

    # Отправляем сообщение
    await callback.message.answer(msg, reply_markup=menu_buttons)
    await callback.answer("Выбор подтверждён")

# ======================== Запуск бота ========================
async def main():
    print("🤖 Bot started!")
    await init_db()  # Инициализация базы данных (если нужно)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
