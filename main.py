import os
import time
import uuid
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
    KeyboardButton,
    BotCommand,
    BotCommandScopeDefault
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Ваши внутренние модули
from database import init_db, add_user, set_user_coins, set_language, count_users, set_user_premium, is_user_premium
from constants.admins import ADMINS

from yookassa import Configuration, Payment

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
PAYMASTER_TEST_TOKEN = os.getenv("PAYMASTER_TEST_TOKEN")

# Настройки ЮKassa
SHOP_ID = os.getenv("SHOP_ID")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY")
Configuration.account_id = SHOP_ID
Configuration.secret_key = YOOKASSA_API_KEY

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ------------------------ ЛОКАЛИЗАЦИЯ ------------------------
LEXICON = {
    "en": {
        "lang_prompt": "Please choose your language:",
        "language_chosen": "✅ Language set to English.",
        "language_changed": "✅ Language changed to English.",
        "start_user_prompt": "Use /menu to see all commands or pick language below:",
        "start_chosen_lang_menu_msg": "Use the menu below to quickly access commands.",
        "unknown_command_before_lang": "You must choose your language first.",

        "choose_coins_prompt": "Choose up to 3 coins, then press «Confirm».",
        "choose_coins_button_prefix_selected": "✅",
        "choose_coins_button_prefix_not_selected": "🔸",
        "reset_selection": "🔄 Reset",
        "confirm_selection": "✅ Confirm",
        "back": "← Back",
        "forward": "Forward →",

        "selection_cleared": "Selection cleared.",
        "must_select_at_least_one": "⚠️ Please select at least one coin!",
        "max_3_coins": "⚠️ You can select up to 3 coins only!",
        "selection_confirmed": "Selection confirmed.",

        "no_coins_chosen": "⚠️ You haven't chosen any coins yet. Use /choice_coin.",
        "no_data": "No data available.",
        "current_prices_header": "🚀 <b>Current crypto prices:</b>",
        "updated_time": "⏰ Updated:",

        "menu_commands_header": "📋 Available commands:\n",
        "menu_start": "/start - Start bot",
        "menu_choice_coin": "/choice_coin - Select or change coins",
        "menu_price": "/price - See prices of chosen coins",
        "menu_userStats": "/userStats - User statistics (admin only)",
        "menu_menu": "/menu - Show this menu",
        "menu_change_interval": "/change_interval - Choosing the notification interval",
        "menu_buy_premium": "/buy_premium - Upgrade to Premium",

        "admin_denied": "🚫 Access denied",
        "userStats_count": "📊 Number of bot users: <b>{count}</b>",
        "lang_change_info": "Use buttons below to switch language.",

        # Уведомления
        "notify_interval_prompt": "Select how often you want to get price updates:",
        "notify_1m": "Every 1 minute",
        "notify_30m": "Every 30 minutes",
        "notify_1h": "Every 1 hour",
        "notify_3h": "Every 3 hours",
        "notify_12h": "Every 12 hours",
        "notify_24h": "Every 24 hours",
        "notify_set": "✅ Notification interval is set!",
        "no_coins_for_notify": "You haven't chosen any coins yet, so notifications are off.",
        "notify_price_now": "Current prices for your selected coins (one-time).",

        # Премиум
        "premium_prompt": "💎 Buy Premium access to choose up to 10 coins!",
        "premium_buy": "Pay for Premium",
        "premium_paid": "✅ I have paid",
        "premium_user": "✨ You are already a Premium user!",
        "premium_congratulations": "🎉 Congratulations! Premium access is activated!",
        "premium_error": "❌ Payment has not been confirmed. Please repeat later.",
    },
    "ru": {
        "lang_prompt": "Пожалуйста, выберите язык:",
        "language_chosen": "✅ Язык установлен на русский.",
        "language_changed": "✅ Язык изменён на русский.",
        "start_user_prompt": "Используйте /menu для просмотра всех команд или выберите язык ниже:",
        "start_chosen_lang_menu_msg": "Используйте меню ниже для быстрого доступа к командам.",
        "unknown_command_before_lang": "Сначала выберите язык!",

        "choose_coins_prompt": "Выберите монеты для мониторинга (до 3-х), затем нажмите «Подтвердить».",
        "choose_coins_button_prefix_selected": "✅",
        "choose_coins_button_prefix_not_selected": "🔸",
        "reset_selection": "🔄 Сбросить выбор",
        "confirm_selection": "✅ Подтвердить",
        "back": "← Назад",
        "forward": "Вперед →",

        "selection_cleared": "Выбор сброшен.",
        "must_select_at_least_one": "⚠️ Выберите хотя бы одну монету!",
        "max_3_coins": "⚠️ Можно выбрать максимум 3 монеты!",
        "selection_confirmed": "✅ Выбор подтверждён.",

        "no_coins_chosen": "⚠️ Вы ещё не выбрали монеты. Используйте /choice_coin.",
        "no_data": "Нет данных по выбранным монетам.",
        "current_prices_header": "🚀 <b>Текущий курс криптовалют:</b>",
        "updated_time": "⏰ Обновлено:",

        "menu_commands_header": "📋 Доступные команды:\n",
        "menu_start": "/start - Начать работу с ботом",
        "menu_choice_coin": "/choice_coin - Выбор (или изменение) монет",
        "menu_price": "/price - Посмотреть цены на выбранные монеты",
        "menu_userStats": "/userStats - Статистика пользователей (только для админов)",
        "menu_menu": "/menu - Показать это меню",
        "menu_change_interval": "/change_interval - Выбор интервала уведомлений",
        "menu_buy_premium": "/buy_premium - Купить Premium-доступ",

        "admin_denied": "🚫 Доступ запрещён",
        "userStats_count": "📊 Количество пользователей бота: <b>{count}</b>",
        "lang_change_info": "Ниже можно переключить язык.",

        # Уведомления
        "notify_interval_prompt": "Выберите, как часто отправлять уведомления о цене:",
        "notify_1m": "Каждую 1 минуту",
        "notify_30m": "Каждые 30 минут",
        "notify_1h": "Каждый 1 час",
        "notify_3h": "Каждые 3 часа",
        "notify_12h": "Каждые 12 часов",
        "notify_24h": "Каждые 24 часа",
        "notify_set": "✅ Интервал уведомлений установлен!",
        "no_coins_for_notify": "У вас ещё не выбраны монеты, поэтому уведомления отключены.",
        "notify_price_now": "Текущая цена по выбранным монетам (одноразово).",

        # Премиум
        "premium_prompt": "💎 Купите Premium-доступ, чтобы выбирать до 10 монет!",
        "premium_buy": "Оплатить Premium",
        "premium_paid": "✅ Я оплатил",
        "premium_user": "✨ Вы уже являетесь Premium-пользователем!",
        "premium_congratulations": "🎉 Поздравляем! Premium доступ активирован!",
        "premium_error": "❌ Оплата не подтверждена. Пожалуйста, повторите позже.",

    }
}
# ----------------------- Константы ---------------------------------
MAX_COINS_STANDARD = 3
MAX_COINS_PREMIUM = 10

# ------------------------ Глобальные словари ------------------------
user_lang = {}              # user_id -> 'en'/'ru'
user_coins = {}             # user_id -> set(['bitcoin','ethereum'])
user_pages = {}
top_100_cache = []

user_first_time = {}        # user_id -> bool (впервые ли запущен бот)
user_first_interval = {}    # user_id -> bool (впервые ли пользователь ставит интервал)

user_intervals = {}         # user_id -> seconds
user_next_notify = {}       # user_id -> float (timestamp)

# Дополнительные словари для хранения message_id сообщений, которые нужно удалять
temp_coin_msg = {}          # user_id -> message_id (сообщение "Выберите монеты...")
temp_interval_msg = {}      # user_id -> message_id (сообщение "Выберите интервал...")

async def setup_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="See start information"),
        BotCommand(command="choice_coin", description="Select coins"),
        BotCommand(command="price", description="Get crypto prices"),
        BotCommand(command="menu", description="Show menu"),
        BotCommand(command="change_lang", description="Change language"),
        BotCommand(command="change_interval", description="Change interval notification"),
        BotCommand(command="buy_premium", description="Upgrade to premium")
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

def get_menu_buttons(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/price"),
                KeyboardButton(text="/choice_coin"),
                # KeyboardButton(text="/change_lang"),
                # KeyboardButton(text="/change_interval")
            ]
        ],
        resize_keyboard=True
    )

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

# ------------------------ Инлайн-клавиатура выбора монет ------------------------
async def coins_keyboard(page=0, per_page=15, selected_coins=None, language="ru"):
    if selected_coins is None:
        selected_coins = set()

    coins_data = await get_top_100_coins()
    total_coins = len(coins_data)
    if total_coins == 0:
        return InlineKeyboardMarkup(inline_keyboard=[])

    total_pages = (total_coins - 1) // per_page
    page = max(0, min(page, total_pages))

    start = page * per_page
    end = min(start + per_page, total_coins)

    kb_buttons = []
    row = []

    prefix_sel = LEXICON[language]["choose_coins_button_prefix_selected"]
    prefix_not_sel = LEXICON[language]["choose_coins_button_prefix_not_selected"]

    for coin in coins_data[start:end]:
        coin_id = coin['id']
        symbol = coin['symbol'].upper()
        prefix = prefix_sel if coin_id in selected_coins else prefix_not_sel
        row.append(
            InlineKeyboardButton(
                text=f"{prefix} {symbol}",
                callback_data=f"coin_{coin_id}_{page}"
            )
        )
        if len(row) == 3:
            kb_buttons.append(row)
            row = []
    if row:
        kb_buttons.append(row)

    nav_row = []
    if page > 0:
        nav_row.append(
            InlineKeyboardButton(
                text=LEXICON[language]["back"],
                callback_data=f"page_{page - 1}"
            )
        )
    if page < total_pages:
        nav_row.append(
            InlineKeyboardButton(
                text=LEXICON[language]["forward"],
                callback_data=f"page_{page + 1}"
            )
        )
    if nav_row:
        kb_buttons.append(nav_row)

    if selected_coins:
        reset_btn = InlineKeyboardButton(
            text=LEXICON[language]["reset_selection"],
            callback_data="reset_selection"
        )
        confirm_btn = InlineKeyboardButton(
            text=LEXICON[language]["confirm_selection"],
            callback_data="confirm_selection"
        )
        kb_buttons.append([reset_btn, confirm_btn])

    return InlineKeyboardMarkup(inline_keyboard=kb_buttons)

# ------------------------ Инлайн-клавиатура выбора интервала ------------------------
def interval_keyboard(lang: str) -> InlineKeyboardMarkup:
    intervals = [
        ("notify_1m", "60"),
        ("notify_30m", "1800"),
        ("notify_1h", "3600"),
        ("notify_3h", "10800"),
        ("notify_12h", "43200"),
        ("notify_24h", "86400"),
    ]
    rows = []
    for label_key, val in intervals:
        text = LEXICON[lang][label_key]
        rows.append([InlineKeyboardButton(text=text, callback_data=f"interval_{val}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ------------------------ Декоратор проверки языка ------------------------
def user_language_chosen(func):
    async def wrapper(message: Message, *args, **kwargs):
        uid = message.from_user.id
        if uid not in user_lang or user_lang[uid] is None:
            await message.answer(
                LEXICON["ru"]["unknown_command_before_lang"] + "\n" +
                LEXICON["en"]["unknown_command_before_lang"]
            )
            return
        return await func(message, *args, **kwargs)
    return wrapper

# ------------------------ Хендлеры команд ------------------------
@dp.message(Command("start"))
async def cmd_start(message: Message, **kwargs):
    user_id = message.from_user.id
    user_lang[user_id] = None
    user_first_time[user_id] = True
    user_first_interval[user_id] = False

    await add_user(user_id, message.from_user.username)

    text_ru = LEXICON["ru"]["lang_prompt"]
    text_en = LEXICON["en"]["lang_prompt"]

    await message.answer(
        f"{text_ru}\n{text_en}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
            ]]
        )
    )
    await message.answer(
        LEXICON["ru"]["start_user_prompt"] + "\n" +
        LEXICON["en"]["start_user_prompt"]
    )

@dp.message(Command("menu"))
@user_language_chosen
async def cmd_menu(message: Message, **kwargs):
    lang = user_lang[message.from_user.id]
    lines = [
        LEXICON[lang]["menu_commands_header"],
        LEXICON[lang]["menu_start"],
        LEXICON[lang]["menu_choice_coin"],
        LEXICON[lang]["menu_price"],
        LEXICON[lang]["menu_change_interval"],
        LEXICON[lang]["menu_menu"]
    ]
    await message.answer("\n".join(lines), reply_markup=get_menu_buttons(lang))

@dp.message(Command("choice_coin"))
@user_language_chosen
async def cmd_choice_coin(message: Message, **kwargs):
    """
    Каждый новый вызов /choice_coin:
    - сбрасываем выбранные монеты,
    - предлагаем выбрать,
    - сохраняем message_id в temp_coin_msg,
    - после подтверждения удаляем это сообщение.
    """
    user_id = message.from_user.id
    lang = user_lang[user_id]

    user_first_time[user_id] = False

    user_coins[user_id] = set()
    user_pages[user_id] = 0

    keyboard = await coins_keyboard(page=0, selected_coins=set(), language=lang)
    # Отправляем сообщение «Выберите монеты...»
    msg = await message.answer(
        LEXICON[lang]["choose_coins_prompt"],
        reply_markup=keyboard
    )
    # Запоминаем, чтобы удалить позже
    temp_coin_msg[user_id] = msg.message_id

@dp.message(Command("price"))
@user_language_chosen
async def cmd_price(message: Message, **kwargs):
    user_id = message.from_user.id
    lang = user_lang[user_id]
    selected = user_coins.get(user_id, set())

    if not selected:
        await message.answer(
            LEXICON[lang]["no_coins_chosen"],
            reply_markup=get_menu_buttons(lang)
        )
        return

    data = await get_crypto_prices(selected)
    msg = build_price_message(data, lang)
    await message.answer(msg, reply_markup=get_menu_buttons(lang))

@dp.message(Command("userStats"))
@user_language_chosen
async def cmd_user_stats(message: Message, **kwargs):
    lang = user_lang[message.from_user.id]
    if str(message.from_user.id) in ADMINS:
        await message.reply(LEXICON[lang]["admin_denied"])
        return
    count = await count_users()
    reply_text = LEXICON[lang]["userStats_count"].format(count=count)
    await message.answer(reply_text, reply_markup=get_menu_buttons(lang))

@dp.message(Command("change_lang"))
@user_language_chosen
async def cmd_change_lang(message: Message, **kwargs):
    user_id = message.from_user.id
    lang = user_lang[user_id]

    text = LEXICON[lang]["lang_change_info"]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
        ]]
    )
    await message.answer(text, reply_markup=keyboard)

@dp.message(Command("change_interval"))
@user_language_chosen
async def cmd_change_interval(message: Message, **kwargs):
    """
    Смена интервала уведомлений вручную.
    Храним message_id в temp_interval_msg, чтобы удалить при выборе.
    """
    user_id = message.from_user.id
    lang = user_lang[user_id]

    user_first_interval[user_id] = False
    kb = interval_keyboard(lang)
    msg = await message.answer(
        LEXICON[lang]["notify_interval_prompt"],
        reply_markup=kb
    )
    temp_interval_msg[user_id] = msg.message_id

# ------------------------ Обработчики колбэков ------------------------
@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def callback_set_language(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    chosen = callback.data.split("_")[1]
    await callback.message.delete()
    user_lang[user_id] = chosen
    await set_language(user_id, chosen)
    if user_first_time[user_id]:
        await callback.message.answer(LEXICON[chosen]["language_chosen"])
        user_coins[user_id] = set()
        user_pages[user_id] = 0
        keyboard = await coins_keyboard(page=0, selected_coins=set(), language=chosen)
        msg = await callback.message.answer(
            LEXICON[chosen]["choose_coins_prompt"],
            reply_markup=keyboard
        )
        temp_coin_msg[user_id] = msg.message_id
    else:
        msg = (LEXICON['en']["language_changed"]
               if chosen == 'en' else LEXICON['ru']["language_changed"])
        await callback.message.answer(msg, reply_markup=get_menu_buttons(chosen))
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("coin_"))
@user_language_chosen
async def callback_select_coin(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    lang = user_lang[user_id]
    parts = callback.data.split("_", 2)
    coin_id = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0

    premium = await is_user_premium(user_id)
    max_coins = MAX_COINS_PREMIUM if premium else MAX_COINS_STANDARD

    selected_coins = user_coins.setdefault(user_id, set())

    if coin_id in selected_coins:
        selected_coins.remove(coin_id)
    else:
        if len(selected_coins) >= max_coins:
            if lang == "ru":
                await callback.answer(
                    f"⚠️ Можно выбрать максимум {max_coins} монет!",
                    show_alert=True
                )
                return
            elif lang == "en":
                await callback.answer(
                    f"⚠️ You can select a maximum of {max_coins} coins!",
                    show_alert=True
                )
                return

        selected_coins.add(coin_id)

    user_pages[user_id] = page
    keyboard = await coins_keyboard(page=page, selected_coins=selected_coins, language=lang)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "reset_selection")
async def callback_reset_selection(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    user_coins[user_id] = set()
    page = user_pages.get(user_id, 0)
    keyboard = await coins_keyboard(page=page, selected_coins=set(), language=lang)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(LEXICON[lang]["selection_cleared"])

@dp.callback_query(lambda c: c.data.startswith("page_"))
async def callback_paginate_coins(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    page = int(callback.data.split("_")[1])
    user_pages[user_id] = page
    selected = user_coins.get(user_id, set())
    keyboard = await coins_keyboard(page=page, selected_coins=selected, language=lang)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "confirm_selection")
async def callback_confirm_selection(callback: CallbackQuery, **kwargs):
    """
    Пользователь подтвердил выбор монет:
    - удаляем сообщение с текстом «Выберите монеты...»
    - генерируем/выводим цену или предлагаем интервал (при первом запуске)
    """
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    selected = user_coins.get(user_id, set())
    if not selected:
        await callback.answer(
            LEXICON[lang]["must_select_at_least_one"],
            show_alert=True
        )
        return

    # Убираем inline-клавиатуру
    await callback.message.edit_reply_markup(reply_markup=None)

    # Удаляем сообщение "Выберите монеты...", если оно есть
    if user_id in temp_coin_msg:
        try:
            await bot.delete_message(callback.message.chat.id, temp_coin_msg[user_id])
        except Exception:
            pass
        del temp_coin_msg[user_id]

    # Сохраняем выбор монет
    await set_user_coins(user_id, list(selected))

    if user_first_time.get(user_id, False):
        user_first_time[user_id] = False
        user_first_interval[user_id] = True
        await callback.message.answer(LEXICON[lang]["selection_confirmed"])
        kb = interval_keyboard(lang)
        # Отправляем сообщение "Выберите интервал..."
        msg_interval = await callback.message.answer(
            LEXICON[lang]["notify_interval_prompt"],
            reply_markup=kb
        )
        temp_interval_msg[user_id] = msg_interval.message_id
    else:
        data = await get_crypto_prices(selected)
        msg_price = build_price_message(data, lang)
        await callback.message.answer(LEXICON[lang]["selection_confirmed"])
        await callback.message.answer(msg_price, reply_markup=get_menu_buttons(lang))
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("interval_"))
async def callback_select_interval(callback: CallbackQuery, **kwargs):
    """
    Пользователь выбрал интервал:
    - удаляем сообщение «Выберите интервал...»
    - если первый раз, отправляем цены
    """
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    await callback.message.edit_reply_markup(reply_markup=None)

    # Удаляем сообщение "Выберите интервал...", если есть
    if user_id in temp_interval_msg:
        try:
            await bot.delete_message(callback.message.chat.id, temp_interval_msg[user_id])
        except Exception:
            pass
        del temp_interval_msg[user_id]

    parts = callback.data.split("_", 1)
    interval_seconds = int(parts[1])
    user_intervals[user_id] = interval_seconds
    user_next_notify[user_id] = time.time() + interval_seconds

    await callback.message.answer(
        LEXICON[lang]["notify_set"],
        reply_markup=get_menu_buttons(lang)
    )

    if user_first_interval.get(user_id, False):
        user_first_interval[user_id] = False
        selected = user_coins.get(user_id, set())
        if selected:
            data = await get_crypto_prices(selected)
            msg_price = build_price_message(data, lang)
            await callback.message.answer(msg_price)
        else:
            await callback.message.answer(LEXICON[lang]["no_coins_for_notify"])
    await callback.answer()

# ------------------------ Фоновая задача с уведомлениями ------------------------
async def schedule_notifications():
    while True:
        await asyncio.sleep(15)
        now = time.time()
        for uid, nxt in list(user_next_notify.items()):
            interval = user_intervals.get(uid)
            if not interval:
                continue
            if now >= nxt:
                selected = user_coins.get(uid)
                lang = user_lang.get(uid, "en")
                if not selected:
                    await bot.send_message(uid, LEXICON[lang]["no_coins_for_notify"])
                else:
                    data = await get_crypto_prices(selected)
                    msg_price = build_price_message(data, lang)
                    await bot.send_message(uid, msg_price)
                user_next_notify[uid] = now + interval

# ------------------------ /buy_premium ------------------------
@dp.message(Command("buy_premium"))
@user_language_chosen
async def cmd_buy_premium(message: Message, **kwargs):
    user_id = message.from_user.id
    lang = user_lang[user_id]

    if await is_user_premium(user_id):
        await message.answer(LEXICON[lang]["premium_user"])
        return

    payment = Payment.create({
        "amount": {"value": "100.00", "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": "https://t.me/YourBotUsername"},
        "capture": True,
        "description": f"Premium-доступ для пользователя {user_id}"
    })

    payment_id = payment.id
    payment_url = payment.confirmation.confirmation_url

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON[lang]["premium_buy"], url=payment_url)],
        [InlineKeyboardButton(text=LEXICON[lang]["premium_paid"], callback_data=f"check_payment_{payment_id}")]
    ])

    await message.answer(LEXICON[lang]["premium_prompt"], reply_markup=keyboard)

# ------------------------ Проверка оплаты ------------------------
async def verify_payment(payment_id: str):
    payment = Payment.find_one(payment_id)
    return payment.status == "succeeded"

@dp.callback_query(lambda c: c.data.startswith("check_payment_"))
@user_language_chosen
async def callback_check_payment(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    lang = user_lang[user_id]
    payment_id = callback.data.split("_")[2]

    if await verify_payment(payment_id):
        await set_user_premium(user_id)
        await callback.message.edit_text(LEXICON[lang]["premium_congratulations"])
    else:
        await callback.answer(LEXICON[lang]["premium_error"], show_alert=True)


# ------------------------ Запуск бота ------------------------
async def main():
    print("🤖 Bot started!")
    await setup_bot_commands(bot)
    await init_db()
    asyncio.create_task(schedule_notifications())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

