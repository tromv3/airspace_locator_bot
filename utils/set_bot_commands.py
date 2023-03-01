from telebot.types import BotCommand
from telebot import TeleBot
from config_data.config import DEFAULT_COMMANDS


def set_default_commands(bot: TeleBot) -> None:
    """
    Функция для установки команд бота.
    Основных команд.

    :argument:
        bot (TeleBot): Телеграмм Бот

    """
    bot.set_my_commands(
        [BotCommand(*i) for i in DEFAULT_COMMANDS]
    )
