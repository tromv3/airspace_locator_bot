from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.history_repo import HistoryRepository
from bot.db.repositories.user_repo import UserRepository
from bot.keyboards.reply import main_menu_keyboard

router = Router(name=__name__)


@router.message(Command("start"))
async def bot_start(message: Message, session: AsyncSession) -> None:
    full_name = " ".join(
        part for part in (message.from_user.first_name, message.from_user.last_name) if part
    )
    user = await UserRepository(session).get_or_create(message.from_user.id, full_name)
    await message.answer(f"Привет, {user.name}!", reply_markup=main_menu_keyboard())
    await HistoryRepository(session).add(message.from_user.id, "Запустить бота")
