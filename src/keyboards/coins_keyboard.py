from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from src.constants.locales import LEXICON
from src.utils.get_crypto_coins import get_top_100_coins

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
