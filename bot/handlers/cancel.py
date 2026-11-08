from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.history_repo import HistoryRepository
from bot.keyboards.reply import main_menu_keyboard

router = Router(name=__name__)


@router.message(Command("cancel"))
async def bot_cancel(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    await message.answer("Выберите действие.", reply_markup=main_menu_keyboard())
    await HistoryRepository(session).add(message.from_user.id, "Вернуться к главному меню")
