"""
Фоновая задача отправки уведомлений о цене криптовалют.
"""
import asyncio
import time
from aiogram import Bot

from src.constants.locales import LEXICON
from src.constants.states import user_next_notify, user_intervals, user_coins, user_lang
from src.utils.get_crypto_coins import get_crypto_prices, build_price_message

async def schedule_notifications(bot: Bot):
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
