from telethon import TelegramClient

from app.logger import logger
from app.mtproto_proxy import (
    mtproxy_connection_candidates,
    parse_mtproto_proxy,
)
from app.settings import Settings


def _build_client(
    settings: Settings,
    proxy,
    connection_class,
) -> TelegramClient:
    return TelegramClient(
        "bothome_bot",
        settings.api_id,
        settings.api_hash,
        connection=connection_class,
        proxy=(proxy.server, proxy.port, proxy.secret),
    )


async def create_connected_client(settings: Settings) -> TelegramClient:
    proxy = parse_mtproto_proxy(settings.telegram_proxy)
    candidates = mtproxy_connection_candidates(
        proxy.secret,
        mode=settings.telegram_mtproto_mode,
    )

    if (
        settings.telegram_mtproto_mode == "randomized"
        and proxy.secret.startswith("ee")
    ):
        logger.warning(
            "TELEGRAM_MTPROTO_MODE=randomized is usually wrong for ee-secrets. "
            "Remove it from .env or set intermediate."
        )

    logger.info(
        "MTProto proxy {}:{} (secret: {} chars, prefix: {})",
        proxy.server,
        proxy.port,
        len(proxy.secret),
        proxy.secret[:4],
    )

    last_error: Exception | None = None

    for connection_class in candidates:
        mode_name = connection_class.__name__
        logger.info("Trying MTProto mode: {}", mode_name)

        client = _build_client(settings, proxy, connection_class)
        try:
            await client.start(bot_token=settings.telegram_bot_token)
            logger.info("Connected via {}", mode_name)
            return client
        except ConnectionError as exc:
            last_error = exc
            logger.warning("Mode {} failed: {}", mode_name, exc)
            try:
                await client.disconnect()
            except Exception:
                pass

    raise ConnectionError(
        f"Failed to connect via MTProto proxy after {len(candidates)} attempt(s)"
    ) from last_error
