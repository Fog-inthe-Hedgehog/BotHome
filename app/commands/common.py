from aiogram import Dispatcher, F
from aiogram.filters.command import Command
from aiogram.types import Message

from app.services.rss_parser import RSSParserBot


def register_handlers(
    dp: Dispatcher,
    parser: RSSParserBot,
    admin_id: int,
    check_interval_hours: int,
) -> None:
    @dp.message(Command(commands=["start"]))
    async def start_command(message: Message) -> None:
        user_id = message.from_user.id if message.from_user else "unknown"
        await message.answer(
            f"Привет!\n🆔 Ваш Chat ID: <code>{user_id}</code>",
            parse_mode="HTML",
        )

    @dp.message(Command("help"))
    async def cmd_help(message: Message) -> None:
        await message.answer(
            "📋 <b>Команды бота:</b>\n\n"
            "/start — запуск бота\n"
            "/check_now — принудительная проверка RSS (только админ)\n"
            "/help — показать эту справку\n\n"
            "<b>Автоматическая проверка:</b>\n"
            f"Бот автоматически проверяет новости раз в {check_interval_hours} ч.",
            parse_mode="HTML",
        )

    @dp.message(Command("check_now"), F.from_user.id == admin_id)
    async def cmd_check_now(message: Message) -> None:
        await message.answer("🔄 Запущена ручная проверка RSS-ленты...")
        count = await parser.check_and_notify()

        if count:
            await message.answer(f"✅ Отправлено уведомлений: {count}")
        else:
            await message.answer("ℹ️ Новых релевантных новостей не найдено")

    @dp.message(Command("check_now"), F.from_user.id != admin_id)
    async def cmd_check_now_denied(message: Message) -> None:
        await message.answer("⛔ Эта команда доступна только администратору.")
