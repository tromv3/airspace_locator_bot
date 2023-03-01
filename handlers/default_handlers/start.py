from telebot.types import Message

from loader import bot
from keyboards.reply.keyboard_start import keyboard_start
from database.database import User
from utils.save_history import save_history


@bot.message_handler(commands=["start"])
def bot_start(message: Message) -> None:
    """
    Функция, для выполнения команды /start.

    :argument:
        message (Message): Ответ пользователя

    """
    user = User.get_or_none(User.id == message.from_user.id)
    if not user:
        user = User.create(id=message.from_user.id,
                           name=f'{message.from_user.first_name} {message.from_user.last_name}')
    bot.send_message(message.chat.id, f" Привет, {user}!\n", reply_markup=keyboard_start())
    save_history(message.from_user.id, "/start")
