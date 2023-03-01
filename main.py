import os
from loguru import logger
from telebot.custom_filters import StateFilter, IsDigitFilter
import handlers

from loader import bot
from utils.set_bot_commands import set_default_commands


if __name__ == "__main__":
    try:
        logger.add("debug.log",
                   format="{time} | {level} | {message}",
                   level="DEBUG",
                   rotation="10 MB",
                   compression="zip")
        bot.add_custom_filter(StateFilter(bot))
        bot.add_custom_filter(IsDigitFilter())
        set_default_commands(bot)
        bot.infinity_polling(skip_pending=True)
        logger.info("Бот запущен!")
    except KeyboardInterrupt:
        logger.info("Выключение...")
    finally:
        logger.info("Удаление временных файлов...")
        if os.path.isdir(os.path.join(os.getcwd(), 'temp')):
            os.rmdir(os.path.join(os.getcwd(), 'temp'))
        logger.info("Временные файлы удалены!")

