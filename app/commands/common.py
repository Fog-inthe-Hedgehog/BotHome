from telethon import TelegramClient, events

from app.services.rss_parser import RSSParserBot


def register_handlers(
    client: TelegramClient,
    parser: RSSParserBot,
    admin_id: int,
    check_interval_hours: int,
) -> None:
    @client.on(events.NewMessage(pattern=r"^/start$", incoming=True))
    async def start_command(event: events.NewMessage.Event) -> None:
        user_id = event.sender_id or "unknown"
        await event.respond(
            f"Привет!\n🆔 Ваш Chat ID: <code>{user_id}</code>",
            parse_mode="html",
        )

    @client.on(events.NewMessage(pattern=r"^/help$", incoming=True))
    async def cmd_help(event: events.NewMessage.Event) -> None:
        await event.respond(
            "📋 <b>Команды бота:</b>\n\n"
            "/start — запуск бота\n"
            "/check_now — принудительная проверка RSS (только админ)\n"
            "/help — показать эту справку\n\n"
            "<b>Автоматическая проверка:</b>\n"
            f"Бот автоматически проверяет новости раз в {check_interval_hours} ч.",
            parse_mode="html",
        )

    @client.on(events.NewMessage(pattern=r"^/check_now$", incoming=True))
    async def cmd_check_now(event: events.NewMessage.Event) -> None:
        if event.sender_id != admin_id:
            await event.respond("⛔ Эта команда доступна только администратору.")
            return

        await event.respond("🔄 Запущена ручная проверка RSS-ленты...")
        count = await parser.check_and_notify()

        if count:
            await event.respond(f"✅ Отправлено уведомлений: {count}")
        else:
            await event.respond("ℹ️ Новых релевантных новостей не найдено")
