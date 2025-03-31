import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src import TG_TOKEN
from src.utils.setup_bot_commands import setup_bot_commands
from database import init_db
from src.services.notifications import schedule_notifications

from src.handlers import commands, callbacks

bot = Bot(token=TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_routers(commands.router, callbacks.router)


async def main():
    print("🤖 Bot started!")
    await setup_bot_commands(bot)
    await init_db()
    asyncio.create_task(schedule_notifications(bot))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
