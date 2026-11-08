from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.repositories.history_repo import HistoryRepository

router = Router(name=__name__)

_MESSAGE_CHUNK_LIMIT = 4000


@router.message(Command("history"))
async def bot_history(message: Message, session: AsyncSession) -> None:
    records = await HistoryRepository(session).list_for_user(message.from_user.id)
    await message.answer("Выполненные Вами запросы:")
    chunk = ""
    for record in records:
        chunk += f"{record.date.strftime('%d-%m-%Y %H:%M:%S')} | {record.command}\n"
        chunk += "-" * 10 + "\n"
        if len(chunk) + 100 > _MESSAGE_CHUNK_LIMIT:
            await message.answer(chunk)
            chunk = ""
    if chunk:
        await message.answer(chunk)
