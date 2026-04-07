import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramError
from aiogram.types import Message

from commands.handlers import register_handlers


async def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set")

    bot = Bot(token=token)
    dp = Dispatcher()
    register_handlers(dp)

    print("Bot started. Waiting for messages...")
    try:
        await dp.start_polling(bot)
    except TelegramError as error:
        print(f"Telegram error: {error}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
