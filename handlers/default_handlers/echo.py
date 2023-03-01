from telebot.types import Message

from loader import bot
from keyboards.reply.keyboard_start import keyboard_start


@bot.message_handler(state=None)
def bot_echo(message: Message) -> None:
    """
    Функция, для получения эхо от бота.
    Используется только для отладки.

    :argument:
        message (Message): Ответ пользователя

    """
    bot.reply_to(
        message, f"Эхо: {message.text}",
        reply_markup=keyboard_start()
    )
    bot.delete_state(message.from_user.id, message.chat.id)
