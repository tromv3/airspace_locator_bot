from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.history_repo import HistoryRepository
from bot.db.repositories.user_repo import UserRepository
from bot.keyboards.reply import main_menu_keyboard
from bot.states.change_name import ChangeNameStates

router = Router(name=__name__)


@router.message(F.text == "Изменить имя")
async def change_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.set_state(ChangeNameStates.name)
    await message.answer(
        "Введите новое имя\n(напр. Иван Иванов или Иван):",
        reply_markup=ReplyKeyboardRemove(),
    )
    await HistoryRepository(session).add(message.from_user.id, "Изменить имя")


@router.message(ChangeNameStates.name)
async def set_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    words = (message.text or "").split()
    if not words or len(words) > 2 or not "".join(words).isalpha():
        await message.answer("Некорректный ввод! Попробуйте еще раз.")
        return

    name = " ".join(word.capitalize() for word in words)
    await UserRepository(session).set_name(message.from_user.id, name)
    await state.clear()
    await message.answer(
        f"Имя изменено. Теперь я буду Вас звать:\n{name}!", reply_markup=main_menu_keyboard()
    )
