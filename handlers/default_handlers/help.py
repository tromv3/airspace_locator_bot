from telebot.types import Message

from config_data.config import DEFAULT_COMMANDS
from loader import bot
from utils.save_history import save_history


@bot.message_handler(commands=["help"])
def bot_help(message: Message) -> None:
    """
    Функция, для выполнения команды /help.

    :argument:
        message (Message): Ответ пользователя

    """
    text = [f"/{command} - {desk}" for command, desk in DEFAULT_COMMANDS]
    bot.reply_to(message, "\n".join(text))
    save_history(message.from_user.id, "/help")

