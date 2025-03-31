from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from src.constants.locales import LEXICON

# ------------------------ Инлайн-клавиатура выбора интервала ------------------------
def interval_keyboard(lang: str) -> InlineKeyboardMarkup:
    intervals = [
        # ("notify_1m", "60"),
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