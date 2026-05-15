from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BTN_START = "🏠 Старт"
BTN_HELP = "📋 Справка"
BTN_CHECK_NOW = "🔄 Проверить RSS"
BTN_LIST_WORDS = "📝 Список слов"
BTN_REFRESH = "🔃 Обновить ключи"
BTN_ADD_WORD = "➕ Добавить слово"
BTN_DELETE_WORD = "➖ Удалить слово"
BTN_CANCEL = "❌ Отмена"

ADMIN_BUTTONS = frozenset(
    {
        BTN_CHECK_NOW,
        BTN_LIST_WORDS,
        BTN_REFRESH,
        BTN_ADD_WORD,
        BTN_DELETE_WORD,
    }
)

ALL_MENU_BUTTONS = ADMIN_BUTTONS | {BTN_START, BTN_HELP, BTN_CANCEL}

#[KeyboardButton(text=BTN_START),
def main_keyboard(is_admin: bool) -> ReplyKeyboardMarkup:
    if is_admin:
        rows = [
            [KeyboardButton(text=BTN_HELP),KeyboardButton(text=BTN_CHECK_NOW)],
            [KeyboardButton(text=BTN_LIST_WORDS), KeyboardButton(text=BTN_REFRESH)],
            [KeyboardButton(text=BTN_ADD_WORD), KeyboardButton(text=BTN_DELETE_WORD)],
        ]
    else:
        rows = [
            [KeyboardButton(text=BTN_START), KeyboardButton(text=BTN_HELP)],
        ]

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие или введите команду",
    )


def cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
        input_field_placeholder="Введите слово или нажмите «Отмена»",
    )
