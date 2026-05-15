import html

from aiogram import Dispatcher, F
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup

from app.commands.keyboards import (
    ADMIN_BUTTONS,
    ALL_MENU_BUTTONS,
    BTN_ADD_WORD,
    BTN_CANCEL,
    BTN_CHECK_NOW,
    BTN_DELETE_WORD,
    BTN_HELP,
    BTN_LIST_WORDS,
    BTN_REFRESH,
    BTN_START,
    cancel_keyboard,
    main_keyboard,
)
from app.keywords import KeywordsStore
from app.logger import logger
from app.services.rss_parser import RSSParserBot
from app.settings import settings


class KeywordForm(StatesGroup):
    waiting_add = State()
    waiting_delete = State()


def _debug_log(message: str, *args: object) -> None:
    if settings.debug:
        logger.debug(message, *args)


def _user_id(message: Message) -> int | None:
    return message.from_user.id if message.from_user else None


def _is_admin(message: Message, admin_id: int) -> bool:
    return _user_id(message) == admin_id


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
    def keyboard_for(message: Message) -> ReplyKeyboardMarkup:
        return main_keyboard(_is_admin(message, admin_id))

    async def answer_menu(message: Message, text: str, **kwargs: object) -> None:
        kwargs.setdefault("reply_markup", keyboard_for(message))
        await message.answer(text, **kwargs)

    def help_text() -> str:
        return (
            "📋 <b>Команды бота:</b>\n\n"
            "Используйте кнопки внизу или команды:\n\n"
            "/start — запуск бота\n"
            "/check_now — проверка RSS без учёта уже просмотренных (только админ)\n"
            "/add_word &lt;слово&gt; — добавить ключевое слово (только админ)\n"
            "/delete_word &lt;слово&gt; — удалить ключевое слово (только админ)\n"
            "/list_words — список ключевых слов (только админ)\n"
            "/refresh — перезагрузить ключевые слова из файла "
            "(после ручного редактирования, только админ)\n"
            "/help — показать эту справку\n"
            "/cancel — отменить ввод слова\n\n"
            "<b>Автоматическая проверка:</b>\n"
            f"Бот автоматически проверяет новости раз в {check_interval_hours} ч."
        )

    async def run_start(message: Message) -> None:
        user_id = _user_id(message) or "unknown"
        await answer_menu(
            message,
            f"Привет!\n🆔 Ваш Chat ID: <code>{user_id}</code>",
            parse_mode="HTML",
        )

    async def run_help(message: Message) -> None:
        await answer_menu(message, help_text(), parse_mode="HTML")

    async def run_check_now(message: Message) -> None:
        _debug_log(
            "Command /check_now from user_id={}",
            _user_id(message),
        )
        _debug_log("RSS URL: {}", parser.rss_url)
        _debug_log("Parser keywords: {}", parser.keywords)
        _debug_log("Seen links in memory: {}", len(parser.seen_links))

        await answer_menu(message, "🔄 Запущена ручная проверка RSS-ленты...")
        count = await parser.check_and_notify(ignore_seen=True)
        _debug_log("/check_now finished, notifications sent: {}", count)

        if count:
            await answer_menu(message, f"✅ Отправлено уведомлений: {count}")
        else:
            await answer_menu(message, "ℹ️ Новых релевантных новостей не найдено")

    async def run_add_word(message: Message, word: str | None) -> None:
        if not word:
            await answer_menu(
                message,
                "Использование: /add_word &lt;слово&gt;\n"
                "Или нажмите «➕ Добавить слово» и введите слово в чат.",
                parse_mode="HTML",
            )
            return

        _debug_log("Command /add_word word={!r}", word)
        ok, reply = keywords_store.add(word)
        if ok:
            _debug_log("Keywords after /add_word: {}", parser.keywords)
        await answer_menu(message, "✅ " + reply if ok else "⚠️ " + reply)

    async def run_delete_word(message: Message, word: str | None) -> None:
        if not word:
            await answer_menu(
                message,
                "Использование: /delete_word &lt;слово&gt;\n"
                "Или нажмите «➖ Удалить слово» и введите слово в чат.",
                parse_mode="HTML",
            )
            return

        _debug_log("Command /delete_word word={!r}", word)
        ok, reply = keywords_store.delete(word)
        if ok:
            _debug_log("Keywords after /delete_word: {}", parser.keywords)
        await answer_menu(message, "✅ " + reply if ok else "⚠️ " + reply)

    async def run_list_words(message: Message) -> None:
        try:
            keywords = keywords_store.load()
        except RuntimeError as exc:
            await answer_menu(message, f"⚠️ {exc}")
            return

        if not keywords:
            await answer_menu(message, "📝 Список ключевых слов пуст.")
            return

        lines = "\n".join(
            f"{index}. {html.escape(word)}" for index, word in enumerate(keywords, 1)
        )
        await answer_menu(
            message,
            f"📝 <b>Ключевые слова ({len(keywords)}):</b>\n\n{lines}",
            parse_mode="HTML",
        )

    async def run_refresh(message: Message) -> None:
        _debug_log("Command /refresh")
        try:
            keywords = keywords_store.reload()
        except RuntimeError as exc:
            await answer_menu(message, f"⚠️ {exc}")
            return

        _debug_log("Keywords after /refresh: {}", parser.keywords)
        await answer_menu(
            message,
            f"✅ Ключевые слова перезагружены из файла. Всего: {len(keywords)}",
        )

    async def deny_admin(message: Message) -> None:
        await answer_menu(message, "⛔ Эта команда доступна только администратору.")

    async def cancel_input(message: Message, state: FSMContext) -> None:
        current = await state.get_state()
        if current is None:
            await answer_menu(message, "Нечего отменять.")
            return
        await state.clear()
        await answer_menu(message, "Ввод отменён.")

    @dp.message(or_f(Command(commands=["start"]), F.text == BTN_START))
    async def start_command(message: Message) -> None:
        await run_start(message)

    @dp.message(or_f(Command("help"), F.text == BTN_HELP))
    async def cmd_help(message: Message) -> None:
        await run_help(message)

    @dp.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext) -> None:
        await cancel_input(message, state)

    @dp.message(F.text == BTN_CANCEL)
    async def btn_cancel(message: Message, state: FSMContext) -> None:
        await cancel_input(message, state)

    @dp.message(
        or_f(Command("check_now"), F.text == BTN_CHECK_NOW),
        F.from_user.id == admin_id,
    )
    async def cmd_check_now(message: Message) -> None:
        await run_check_now(message)

    @dp.message(
        or_f(Command("check_now"), F.text == BTN_CHECK_NOW),
        F.from_user.id != admin_id,
    )
    async def cmd_check_now_denied(message: Message) -> None:
        await deny_admin(message)

    @dp.message(Command("add_word"), F.from_user.id == admin_id)
    async def cmd_add_word(message: Message, state: FSMContext) -> None:
        await state.clear()
        await run_add_word(message, _command_argument(message))

    @dp.message(Command("add_word"), F.from_user.id != admin_id)
    async def cmd_add_word_denied(message: Message) -> None:
        await deny_admin(message)

    @dp.message(F.text == BTN_ADD_WORD, F.from_user.id == admin_id)
    async def btn_add_word(message: Message, state: FSMContext) -> None:
        await state.set_state(KeywordForm.waiting_add)
        await message.answer(
            "Введите слово для добавления:",
            reply_markup=cancel_keyboard(),
        )

    @dp.message(F.text == BTN_ADD_WORD, F.from_user.id != admin_id)
    async def btn_add_word_denied(message: Message) -> None:
        await deny_admin(message)

    @dp.message(
        KeywordForm.waiting_add,
        F.from_user.id == admin_id,
        ~F.text.in_(ALL_MENU_BUTTONS),
    )
    async def process_add_word(message: Message, state: FSMContext) -> None:
        word = (message.text or "").strip()
        await state.clear()
        await run_add_word(message, word)

    @dp.message(Command("delete_word"), F.from_user.id == admin_id)
    async def cmd_delete_word(message: Message, state: FSMContext) -> None:
        await state.clear()
        await run_delete_word(message, _command_argument(message))

    @dp.message(Command("delete_word"), F.from_user.id != admin_id)
    async def cmd_delete_word_denied(message: Message) -> None:
        await deny_admin(message)

    @dp.message(F.text == BTN_DELETE_WORD, F.from_user.id == admin_id)
    async def btn_delete_word(message: Message, state: FSMContext) -> None:
        await state.set_state(KeywordForm.waiting_delete)
        await message.answer(
            "Введите слово для удаления:",
            reply_markup=cancel_keyboard(),
        )

    @dp.message(F.text == BTN_DELETE_WORD, F.from_user.id != admin_id)
    async def btn_delete_word_denied(message: Message) -> None:
        await deny_admin(message)

    @dp.message(
        KeywordForm.waiting_delete,
        F.from_user.id == admin_id,
        ~F.text.in_(ALL_MENU_BUTTONS),
    )
    async def process_delete_word(message: Message, state: FSMContext) -> None:
        word = (message.text or "").strip()
        await state.clear()
        await run_delete_word(message, word)

    @dp.message(
        or_f(Command("list_words"), F.text == BTN_LIST_WORDS),
        F.from_user.id == admin_id,
    )
    async def cmd_list_words(message: Message) -> None:
        await run_list_words(message)

    @dp.message(
        or_f(Command("list_words"), F.text == BTN_LIST_WORDS),
        F.from_user.id != admin_id,
    )
    async def cmd_list_words_denied(message: Message) -> None:
        await deny_admin(message)

    @dp.message(
        or_f(Command("refresh"), F.text == BTN_REFRESH),
        F.from_user.id == admin_id,
    )
    async def cmd_refresh(message: Message) -> None:
        await run_refresh(message)

    @dp.message(
        or_f(Command("refresh"), F.text == BTN_REFRESH),
        F.from_user.id != admin_id,
    )
    async def cmd_refresh_denied(message: Message) -> None:
        await deny_admin(message)

    @dp.message(F.text.in_(ADMIN_BUTTONS), F.from_user.id != admin_id)
    async def admin_buttons_denied(message: Message) -> None:
        await deny_admin(message)

    @dp.message(StateFilter(KeywordForm.waiting_add, KeywordForm.waiting_delete))
    async def keyword_form_menu_button(message: Message, state: FSMContext) -> None:
        if message.text == BTN_CANCEL:
            await cancel_input(message, state)
            return
        await message.answer(
            "Сначала введите слово или нажмите «❌ Отмена».",
            reply_markup=cancel_keyboard(),
        )
