from aiogram import Dispatcher
from aiogram.filters.command import Command
from aiogram.types import Message


def register_handlers(dp: Dispatcher) -> None:
    @dp.message(Command(commands=["start"]))
    async def start_command(message: Message) -> None:
        await message.answer("Привет")
