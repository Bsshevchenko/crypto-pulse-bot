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
    KeyboardButton,
    BotCommand,
    BotCommandScopeDefault
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Ваши модули
from database import init_db, add_user, set_user_coins, set_language, count_users
from constants.admins import ADMINS

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ---------------------- Локализация ----------------------
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

        "admin_denied": "🚫 Access denied",
        "userStats_count": "📊 Number of bot users: <b>{count}</b>",

        "lang_change_info": "Use buttons below to switch language."
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
        "selection_confirmed": "Выбор подтверждён.",

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

        "admin_denied": "🚫 Доступ запрещён",
        "userStats_count": "📊 Количество пользователей бота: <b>{count}</b>",

        "lang_change_info": "Ниже можно переключить язык."
    }
}

# ---------------------- Состояния ----------------------
user_lang = {}
user_coins = {}
user_pages = {}
top_100_cache = []
# Сохраняем ID сообщения «Choose up to 3 coins... + inline-кнопки»,
# чтобы удалить именно его при подтверждении.
temp_inline_msg = {}  # user_id -> message_id

async def setup_bot_commands(bot: Bot):
    """
    Устанавливает команды, описание и короткое описание бота.
    """
    # Список команд (будет выводиться в меню при вводе "/")
    commands = [
        BotCommand(command="start", description="See start information"),
        BotCommand(command="choice_coin", description="Select coins"),
        BotCommand(command="price", description="Get crypto prices"),
        BotCommand(command="menu", description="Show menu"),
        BotCommand(command="change_lang", description="Change language")
    ]

    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())

    # Короткое описание (отображается вверху, где «What can this bot do?»)
    await bot.set_my_short_description("Shows approximate creation date for any account")
    # Основное описание (видно в профиле бота под кнопкой «What can this bot do?»)
    await bot.set_my_description(
        "This bot can show approximate creation date for any Telegram account."
        "\nUse /id <user_id> or /help for more info."
    )


def get_menu_buttons(language: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/price"),
                KeyboardButton(text="/choice_coin"),
                KeyboardButton(text="/change_lang")
            ]
        ],
        resize_keyboard=True
    )


# ---------------------- Функции CoinGecko ----------------------
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


# ---------------------- Клавиатура выбора монет ----------------------
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

    # Кнопки пагинации
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

    # Кнопки сброса и подтверждения
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


# ---------------------- Декоратор, запрещающий команды до выбора языка ----------------------
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


# ---------------------- Обработчики команд ----------------------
@dp.message(Command("start"))
async def cmd_start(message: Message, **kwargs):
    user_id = message.from_user.id
    user_lang[user_id] = None

    await add_user(user_id, message.from_user.username)

    text_ru = LEXICON["ru"]["lang_prompt"]
    text_en = LEXICON["en"]["lang_prompt"]

    # Сообщение с выбором языка
    await message.answer(
        f"{text_ru}\n{text_en}",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
                    InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
                ]
            ]
        )
    )
    # Оставляем второе сообщение-подсказку
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
        LEXICON[lang]["menu_menu"]
    ]
    await message.answer("\n".join(lines), reply_markup=get_menu_buttons(lang))


@dp.message(Command("choice_coin"))
@user_language_chosen
async def cmd_choice_coin(message: Message, **kwargs):
    user_id = message.from_user.id
    lang = user_lang[user_id]

    user_coins[user_id] = set()
    user_pages[user_id] = 0

    keyboard = await coins_keyboard(page=0, selected_coins=set(), language=lang)
    # Сообщение с «Choose up to 3 coins...»
    # + inline-клавиатура
    msg_coins = await message.answer(
        LEXICON[lang]["choose_coins_prompt"],
        reply_markup=keyboard
    )
    # Сохраняем только это сообщение, чтобы удалить при нажатии «Подтвердить»
    temp_inline_msg[user_id] = msg_coins.message_id



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

    prices = await get_crypto_prices(selected)
    msg = build_price_message(prices, lang)
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
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")
            ]
        ]
    )
    await message.answer(text, reply_markup=keyboard)


# ---------------------- Обработчики CallbackQuery ----------------------
@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def callback_set_language(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    prev_lang = user_lang.get(user_id)
    chosen = callback.data.split("_")[1]

    # Удаляем сообщение с выбором языка
    await callback.message.delete()

    user_lang[user_id] = chosen
    await set_language(user_id, chosen)

    # Если язык не был выбран — первый старт
    if prev_lang is None:
        await callback.message.answer(LEXICON[chosen]["language_chosen"])
        # Автоматически вызываем «choose_coins_prompt»
        user_coins[user_id] = set()
        user_pages[user_id] = 0

        keyboard = await coins_keyboard(page=0, selected_coins=set(), language=chosen)
        msg_coins = await callback.message.answer(
            LEXICON[chosen]["choose_coins_prompt"],
            reply_markup=keyboard
        )
        temp_inline_msg[user_id] = msg_coins.message_id
    else:
        # Язык меняем
        if chosen == 'en':
            msg = LEXICON['en']["language_changed"]
        else:
            msg = LEXICON['ru']["language_changed"]
        await callback.message.answer(msg, reply_markup=get_menu_buttons(chosen))

    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("coin_"))
async def callback_select_coin(callback: CallbackQuery, **kwargs):
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")

    parts = callback.data.split("_", 2)
    coin_id = parts[1]
    page = int(parts[2]) if len(parts) > 2 else 0

    selected_coins = user_coins.setdefault(user_id, set())

    if coin_id in selected_coins:
        selected_coins.remove(coin_id)
    else:
        if len(selected_coins) >= 3:
            await callback.answer(
                LEXICON[lang]["max_3_coins"],
                show_alert=True
            )
            return
        selected_coins.add(coin_id)

    user_pages[user_id] = page
    keyboard = await coins_keyboard(
        page=page, selected_coins=selected_coins, language=lang
    )
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
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")

    selected = user_coins.get(user_id, set())
    if not selected:
        await callback.answer(
            LEXICON[lang]["must_select_at_least_one"],
            show_alert=True
        )
        return

    # Удаляем полностью сообщение c inline-клавиатурой (choose_coins_prompt)
    # Если оно есть
    msg_id = temp_inline_msg.get(user_id)
    if msg_id:
        try:
            await bot.delete_message(chat_id=callback.message.chat.id, message_id=msg_id)
        except Exception:
            pass
        # Чистим из словаря
        del temp_inline_msg[user_id]

    # Сохраняем выбор
    await set_user_coins(user_id, list(selected))

    # Генерируем цену
    prices = await get_crypto_prices(selected)
    msg = build_price_message(prices, lang)

    # Отправляем сообщение с ценами
    await callback.message.answer(msg, reply_markup=get_menu_buttons(lang))

    # Ответ для убирания "часиков" на кнопке
    await callback.answer(LEXICON[lang]["selection_confirmed"])


# ---------------------- Запуск бота ----------------------
async def main():
    print("🤖 Bot started!")
    await setup_bot_commands(bot)
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
