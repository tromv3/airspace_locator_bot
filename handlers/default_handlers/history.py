from telebot.types import Message

from loader import bot
from keyboards.reply.keyboard_start import keyboard_start
from database.database import History


@bot.message_handler(commands=["history"])
def bot_history(message: Message) -> None:
    """
    Функция, для выполнения команды /history.

    :argument:
        message (Message): Ответ пользователя

    """
    hist = list(History.select().where(History.user == message.from_user.id))
    bot.send_message(message.chat.id, "Выполненные Вами запросы:")
    text = ''
    for rec in hist:
        text += f"{rec.date.strftime('%d-%m-%Y %H:%M:%S')} | {rec.command}\n"
        text += "-" * 10 + "\n"
        if len(text) + 100 > 4000:
            bot.send_message(message.chat.id, text)
            text = ''
    if text != '':
        bot.send_message(message.chat.id, text)
