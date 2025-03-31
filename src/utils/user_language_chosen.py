from aiogram.types import Message, CallbackQuery
from src.constants.states import user_lang
from src.constants.locales import LEXICON


# ------------------------ Декоратор проверки языка ------------------------

def user_language_chosen(func):
    async def wrapper(event, *args, **kwargs):
        if isinstance(event, (Message, CallbackQuery)):
            uid = event.from_user.id
            if uid not in user_lang or user_lang[uid] is None:
                await event.answer(
                    LEXICON["ru"]["unknown_command_before_lang"] + "\n" +
                    LEXICON["en"]["unknown_command_before_lang"]
                )
                return
            return await func(event, *args)  # ⬅️ удаляем kwargs
        return await func(event, *args, **kwargs)
    return wrapper
