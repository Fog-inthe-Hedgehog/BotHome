from telethon import TelegramClient

from app.logger import logger
from app.mtproto_proxy import mtproxy_connection_class, parse_mtproto_proxy
from app.settings import Settings


def create_client(settings: Settings) -> TelegramClient:
    proxy = parse_mtproto_proxy(settings.telegram_proxy)
    connection_class = mtproxy_connection_class(
        proxy.secret,
        mode=settings.telegram_mtproto_mode,
    )

    logger.info(
        "Telegram client uses MTProto proxy {}:{} (secret prefix: {}, mode: {})",
        proxy.server,
        proxy.port,
        proxy.secret[:4],
        connection_class.__name__,
    )

    return TelegramClient(
        "bothome_bot",
        settings.api_id,
        settings.api_hash,
        connection=connection_class,
        proxy=(proxy.server, proxy.port, proxy.secret),
    )
