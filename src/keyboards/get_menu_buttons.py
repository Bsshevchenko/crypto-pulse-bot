from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
)

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