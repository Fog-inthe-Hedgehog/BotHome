import asyncio

from app.bot_factory import create_client
from app.commands.common import register_handlers
from app.logger import logger
from app.services.rss_parser import RSSParserBot, start_background_parser
from app.settings import settings


async def main() -> None:
    client = create_client(settings)

    parser = RSSParserBot(
        client=client,
        chat_id=settings.admin_id,
        settings=settings,
    )
    register_handlers(
        client,
        parser,
        admin_id=settings.admin_id,
        check_interval_hours=settings.check_interval_hours,
    )

    async with client:
        await client.start(bot_token=settings.telegram_bot_token)
        await parser.warm_up()
        start_background_parser(parser)

        logger.info("Bot started. Waiting for messages...")
        await client.run_until_disconnected()


if __name__ == "__main__":
    asyncio.run(main())
