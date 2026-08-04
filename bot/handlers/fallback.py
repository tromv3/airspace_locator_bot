from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards.reply import main_menu_keyboard

router = Router(name=__name__)


@router.message()
async def bot_echo(message: Message, state: FSMContext) -> None:
    await message.reply(f"Эхо: {message.text}", reply_markup=main_menu_keyboard())
    await state.clear()
