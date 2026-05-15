from aiogram import Dispatcher
from aiogram.filters.command import Command
from aiogram.types import Message

from app.services.rss_parser import start_background_parser

def register_handlers(dp: Dispatcher) -> None:
    @dp.message(Command(commands=["start"]))
    async def start_command(message: Message) -> None:
        await message.answer("Привет" f"🆔 Ваш Chat ID: `{message.from_user.id}`\n")

    @dp.message(Command("help"))
    async def cmd_help(message: Message):
        await message.answer(
            "📋 <b>Команды бота:</b>\n\n"
            "/start - запуск бота\n"
            "/check_now - принудительная проверка RSS\n"
            "/help - показать эту справку\n\n"
            "<b>Автоматическая проверка:</b>\n"
            "Бот автоматически проверяет новости раз в 24 часа",
            parse_mode="HTML"
        )
    
    @dp.message(Command("check_now"))
    async def cmd_check_now(message: Message):
        """Команда для ручной проверки RSS"""
        await message.answer("🔄 Запущена ручная проверка RSS-ленты...")
        
        # Здесь нужно передать реальный chat_id и keywords
        # Пока используем заглушку, реальные значения будут из main.py
        await message.answer("⚠️ Функция в разработке. Пожалуйста, используйте основного бота.")