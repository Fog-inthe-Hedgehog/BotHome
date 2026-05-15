import asyncio

from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramAPIError

from app.commands.common import register_handlers
from app.logger import logger
from app.services.rss_parser import RSSParserBot, start_background_parser
from app.settings import settings


async def main() -> None:
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher()

    parser = RSSParserBot(
        bot=bot,
        chat_id=settings.admin_id,
        settings=settings,
    )
    register_handlers(
        dp,
        parser,
        admin_id=settings.admin_id,
        check_interval_hours=settings.check_interval_hours,
    )

    await parser.warm_up()
    start_background_parser(parser)

    logger.info("Bot started. Waiting for messages...")
    try:
        await dp.start_polling(bot)
    except TelegramAPIError:
        logger.exception("Telegram API error")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
