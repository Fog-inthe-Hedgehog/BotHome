import html

from aiogram import Dispatcher, F
from aiogram.filters.command import Command
from aiogram.types import Message

from app.keywords import KeywordsStore
from app.services.rss_parser import RSSParserBot


def _command_argument(message: Message) -> str | None:
    text = (message.text or "").strip()
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None
    return parts[1].strip() or None


def register_handlers(
    dp: Dispatcher,
    parser: RSSParserBot,
    keywords_store: KeywordsStore,
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
            "/add_word &lt;слово&gt; — добавить ключевое слово (только админ)\n"
            "/delete_word &lt;слово&gt; — удалить ключевое слово (только админ)\n"
            "/list_words — список ключевых слов (только админ)\n"
            "/refresh — перезагрузить ключевые слова из файла "
            "(после ручного редактирования, только админ)\n"
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

    @dp.message(Command("add_word"), F.from_user.id == admin_id)
    async def cmd_add_word(message: Message) -> None:
        word = _command_argument(message)
        if not word:
            await message.answer("Использование: /add_word &lt;слово&gt;", parse_mode="HTML")
            return

        ok, reply = keywords_store.add(word)
        await message.answer("✅ " + reply if ok else "⚠️ " + reply)

    @dp.message(Command("add_word"), F.from_user.id != admin_id)
    async def cmd_add_word_denied(message: Message) -> None:
        await message.answer("⛔ Эта команда доступна только администратору.")

    @dp.message(Command("delete_word"), F.from_user.id == admin_id)
    async def cmd_delete_word(message: Message) -> None:
        word = _command_argument(message)
        if not word:
            await message.answer(
                "Использование: /delete_word &lt;слово&gt;",
                parse_mode="HTML",
            )
            return

        ok, reply = keywords_store.delete(word)
        await message.answer("✅ " + reply if ok else "⚠️ " + reply)

    @dp.message(Command("delete_word"), F.from_user.id != admin_id)
    async def cmd_delete_word_denied(message: Message) -> None:
        await message.answer("⛔ Эта команда доступна только администратору.")

    @dp.message(Command("list_words"), F.from_user.id == admin_id)
    async def cmd_list_words(message: Message) -> None:
        try:
            keywords = keywords_store.load()
        except RuntimeError as exc:
            await message.answer(f"⚠️ {exc}")
            return

        if not keywords:
            await message.answer("📝 Список ключевых слов пуст.")
            return

        lines = "\n".join(
            f"{index}. {html.escape(word)}" for index, word in enumerate(keywords, 1)
        )
        await message.answer(
            f"📝 <b>Ключевые слова ({len(keywords)}):</b>\n\n{lines}",
            parse_mode="HTML",
        )

    @dp.message(Command("list_words"), F.from_user.id != admin_id)
    async def cmd_list_words_denied(message: Message) -> None:
        await message.answer("⛔ Эта команда доступна только администратору.")

    @dp.message(Command("refresh"), F.from_user.id == admin_id)
    async def cmd_refresh(message: Message) -> None:
        try:
            keywords = keywords_store.reload()
        except RuntimeError as exc:
            await message.answer(f"⚠️ {exc}")
            return

        await message.answer(
            f"✅ Ключевые слова перезагружены из файла. Всего: {len(keywords)}"
        )

    @dp.message(Command("refresh"), F.from_user.id != admin_id)
    async def cmd_refresh_denied(message: Message) -> None:
        await message.answer("⛔ Эта команда доступна только администратору.")
