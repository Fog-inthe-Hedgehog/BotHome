import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError
from aiogram.types import Message

from commands.handlers import register_handlers
from utils.rss_parser import start_background_parser

# Загружаем переменные из .env файла
load_dotenv()  # ищет .env в текущей директории

async def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN not found. "
            "Create a .env file with TELEGRAM_BOT_TOKEN=your_token"
        )

    admin_id = os.getenv("ADMIN_ID")
    if not admin_id:
        raise RuntimeError(
            "ADMIN_ID not found. "
            "Create a .env file with ADMIN_ID=your_chat_id"
        )

    bot = Bot(token=token)
    dp = Dispatcher()
    register_handlers(dp)

    # Запускаем фоновый парсер RSS
    await start_background_parser(
        bot=bot,
        chat_id=int(admin_id)
    )

    print("Bot started. Waiting for messages...")
    try:
        await dp.start_polling(bot)
    except TelegramAPIError as error:
        print(f"Telegram error: {error}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
