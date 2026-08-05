import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from loguru import logger
from pydantic import ValidationError

from bot.config import get_settings
from bot.constants import DEFAULT_COMMANDS
from bot.db.session import create_engine, create_session_maker
from bot.handlers import setup_routers
from bot.middlewares.db import DbSessionMiddleware
from bot.services.airlabs_client import AirLabsClient
from bot.services.geocoder_client import DadataClient
from bot.services.opensky_client import OpenSkyClient
from bot.services.planespotters_client import PlanespottersClient


async def main() -> None:
    logger.add(
        "debug.log",
        format="{time} | {level} | {message}",
        level="DEBUG",
        rotation="10 MB",
        compression="zip",
    )

    try:
        settings = get_settings()
    except ValidationError as exc:
        logger.error(f"Некорректная конфигурация: {exc}")
        sys.exit(1)

    engine = create_engine()
    session_maker = create_session_maker(engine)
    dadata_client = DadataClient(settings.dadata_token, settings.dadata_secret_key)
    airlabs_client = AirLabsClient(settings.air_labs_api_key)
    opensky_client = OpenSkyClient()
    planespotters_client = PlanespottersClient()

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher(storage=MemoryStorage())
    dispatcher.update.middleware(DbSessionMiddleware(session_maker))
    dispatcher["dadata_client"] = dadata_client
    dispatcher["airlabs_client"] = airlabs_client
    dispatcher["opensky_client"] = opensky_client
    dispatcher["planespotters_client"] = planespotters_client
    dispatcher.include_router(setup_routers())

    try:
        commands = [
            BotCommand(command=command, description=description)
            for command, description in DEFAULT_COMMANDS
        ]
        await bot.set_my_commands(commands)

        logger.info("Бот запущен!")
        await dispatcher.start_polling(bot, skip_updates=True)
    finally:
        await bot.session.close()
        await airlabs_client.aclose()
        await opensky_client.aclose()
        await planespotters_client.aclose()
        await dadata_client.aclose()
        await engine.dispose()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Выключение...")
