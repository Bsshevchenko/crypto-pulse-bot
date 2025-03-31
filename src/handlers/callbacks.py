import time
from aiogram import Router
from yookassa import Payment
from aiogram.types import CallbackQuery

from database import set_language, set_user_coins, is_user_premium, set_user_premium, get_referrer_id
from src.constants.constants import MAX_COINS_STANDARD, MAX_COINS_PREMIUM
from src.constants.locales import LEXICON
from src.constants.states import (
    user_lang, user_first_time, user_coins, user_pages, temp_coin_msg,
    user_first_interval, temp_interval_msg, user_intervals, user_next_notify
)
from src.keyboards.get_menu_buttons import get_menu_buttons
from src.keyboards.coins_keyboard import coins_keyboard
from src.keyboards.interval_keyboard import interval_keyboard
from src.utils.get_crypto_coins import get_crypto_prices, build_price_message
from src.utils.user_language_chosen import user_language_chosen
from aiogram import Bot

router = Router()


@router.callback_query(lambda c: c.data.startswith("lang_"))
async def callback_set_language(callback: CallbackQuery):
    """Установка языка после выбора"""
    user_id = callback.from_user.id
    chosen = callback.data.split("_")[1]
    await callback.message.delete()
    user_lang[user_id] = chosen
    await set_language(user_id, chosen)

    referrer_id = await get_referrer_id(user_id)
    if referrer_id:
        await set_user_premium(referrer_id)
        await callback.bot.send_message(referrer_id, "🎉 Один из приглашённых активировал бота — вы получили Premium!")

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
        msg = LEXICON['en']["language_changed"] if chosen == 'en' else LEXICON['ru']["language_changed"]
        await callback.message.answer(msg, reply_markup=get_menu_buttons(chosen))
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("coin_"))
@user_language_chosen
async def callback_select_coin(callback: CallbackQuery):
    """Обработка выбора/снятия криптовалют"""
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
            await callback.answer(
                LEXICON[lang]["coin_limit_exceeded"].format(max_coins=max_coins),
                show_alert=True
            )
            return
        selected_coins.add(coin_id)

    user_pages[user_id] = page
    keyboard = await coins_keyboard(page=page, selected_coins=selected_coins, language=lang)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(lambda c: c.data == "reset_selection")
async def callback_reset_selection(callback: CallbackQuery):
    """Сброс выбора монет"""
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    user_coins[user_id] = set()
    page = user_pages.get(user_id, 0)
    keyboard = await coins_keyboard(page=page, selected_coins=set(), language=lang)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(LEXICON[lang]["selection_cleared"])


@router.callback_query(lambda c: c.data.startswith("page_"))
async def callback_paginate_coins(callback: CallbackQuery):
    """Пагинация монет"""
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    page = int(callback.data.split("_")[1])
    user_pages[user_id] = page
    selected = user_coins.get(user_id, set())
    keyboard = await coins_keyboard(page=page, selected_coins=selected, language=lang)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@router.callback_query(lambda c: c.data == "confirm_selection")
async def callback_confirm_selection(callback: CallbackQuery):
    """
    Подтверждение выбора монет:
    - удаляем сообщение выбора
    - сохраняем монеты
    - предлагаем интервал или сразу отправляем цены
    """
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    selected = user_coins.get(user_id, set())

    if not selected:
        await callback.answer(LEXICON[lang]["must_select_at_least_one"], show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=None)

    if user_id in temp_coin_msg:
        try:
            await callback.bot.delete_message(callback.message.chat.id, temp_coin_msg[user_id])
        except Exception:
            pass
        del temp_coin_msg[user_id]

    await set_user_coins(user_id, list(selected))

    if user_first_time.get(user_id, False):
        user_first_time[user_id] = False
        user_first_interval[user_id] = True
        await callback.message.answer(LEXICON[lang]["selection_confirmed"])
        kb = interval_keyboard(lang)
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


@router.callback_query(lambda c: c.data.startswith("interval_"))
async def callback_select_interval(callback: CallbackQuery):
    """Выбор интервала уведомлений"""
    user_id = callback.from_user.id
    lang = user_lang.get(user_id, "ru")
    await callback.message.edit_reply_markup(reply_markup=None)

    if user_id in temp_interval_msg:
        try:
            await callback.bot.delete_message(callback.message.chat.id, temp_interval_msg[user_id])
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


# ------------------------ Проверка оплаты ------------------------
async def verify_payment(payment_id: str):
    payment = Payment.find_one(payment_id)
    return payment.status == "succeeded"

@router.callback_query(lambda c: c.data.startswith("check_payment_"))
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