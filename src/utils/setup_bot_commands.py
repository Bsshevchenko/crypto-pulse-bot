from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeDefault
)

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