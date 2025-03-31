from aiogram import Router
from yookassa import Payment
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from database import add_user, count_users, is_user_premium
from src.constants.admins import ADMINS
from src.constants.locales import LEXICON
from src.constants.states import (
    user_lang, user_first_time, user_first_interval,
    user_pages, user_coins, temp_coin_msg, temp_interval_msg
)
from src.keyboards.get_menu_buttons import get_menu_buttons
from src.keyboards.coins_keyboard import coins_keyboard
from src.keyboards.interval_keyboard import interval_keyboard
from src.utils.get_crypto_coins import get_crypto_prices, build_price_message
from src.utils.user_language_chosen import user_language_chosen

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    args = message.text.split()
    referrer_id = None

    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1].split("ref_")[1])
            if referrer_id == user_id:
                referrer_id = None
        except ValueError:
            pass

    user_lang[user_id] = None
    user_first_time[user_id] = True
    user_first_interval[user_id] = False

    await add_user(user_id, message.from_user.username, referrer_id=referrer_id)

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


@router.message(Command("menu"))
@user_language_chosen
async def cmd_menu(message: Message):
    """Команда /menu — показать список команд"""
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


@router.message(Command("choice_coin"))
@user_language_chosen
async def cmd_choice_coin(message: Message):
    """
    Команда /choice_coin — выбор криптовалют:
    - сброс текущего выбора
    - показ клавиатуры
    """
    user_id = message.from_user.id
    lang = user_lang[user_id]

    user_first_time[user_id] = False
    user_coins[user_id] = set()
    user_pages[user_id] = 0

    keyboard = await coins_keyboard(page=0, selected_coins=set(), language=lang)
    msg = await message.answer(
        LEXICON[lang]["choose_coins_prompt"],
        reply_markup=keyboard
    )
    temp_coin_msg[user_id] = msg.message_id


@router.message(Command("price"))
@user_language_chosen
async def cmd_price(message: Message):
    """Команда /price — текущие цены выбранных монет"""
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


@router.message(Command("userStats"))
@user_language_chosen
async def cmd_user_stats(message: Message):
    """Команда /userStats — количество пользователей (только для админов)"""
    lang = user_lang[message.from_user.id]
    if str(message.from_user.id) in ADMINS:
        await message.reply(LEXICON[lang]["admin_denied"])
        return
    count = await count_users()
    reply_text = LEXICON[lang]["userStats_count"].format(count=count)
    await message.answer(reply_text, reply_markup=get_menu_buttons(lang))


@router.message(Command("change_lang"))
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


@router.message(Command("change_interval"))
@user_language_chosen
async def cmd_change_interval(message: Message):
    """
    Команда /change_interval — ручной выбор интервала уведомлений
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


@router.message(Command("buy_premium"))
@user_language_chosen
async def cmd_buy_premium(message: Message):
    """Команда /buy_premium — покупка премиум-доступа через ЮKassa"""
    user_id = message.from_user.id
    lang = user_lang[user_id]

    if await is_user_premium(user_id):
        await message.answer(LEXICON[lang]["premium_user"])
        return

    referral_link = f"https://t.me/CryptoProPulseBot?start=ref_{user_id}"

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
        [InlineKeyboardButton(text=LEXICON[lang]["premium_ref"], callback_data="ref_premium")],
        [InlineKeyboardButton(text=LEXICON[lang]["premium_paid"], callback_data=f"check_payment_{payment_id}")]
    ])

    await message.answer(LEXICON[lang]["premium_prompt"], reply_markup=keyboard)

    @router.callback_query(lambda c: c.data == "ref_premium")
    async def send_referral(callback: CallbackQuery):
        await callback.message.edit_reply_markup()
        await callback.message.answer(LEXICON[lang]["referral_msg"].format(link=referral_link))