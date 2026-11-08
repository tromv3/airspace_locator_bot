from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.constants import DEFAULT_COMMANDS
from bot.db.repositories.history_repo import HistoryRepository

router = Router(name=__name__)


@router.message(Command("help"))
async def bot_help(message: Message, session: AsyncSession) -> None:
    text = "\n".join(f"/{command} - {description}" for command, description in DEFAULT_COMMANDS)
    await message.reply(text)
    await HistoryRepository(session).add(message.from_user.id, "Вывести справку")
