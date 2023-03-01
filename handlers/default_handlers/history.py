from telebot.types import Message

from loader import bot
from keyboards.reply.keyboard_start import keyboard_start
from database.database import History


@bot.message_handler(commands=["history"])
def bot_history(message: Message) -> None:
    hist = list(History.select().where(History.user == message.from_user.id))
    # TODO: Удаление старых записей
    bot.send_message(message.chat.id, "Выполненные Вами запросы:")
    text = ''
    for rec in hist:
        text += f"{rec.command} | {str(rec.date)}"
        if len(text) + 100 > 4000:
            bot.send_message(message.chat.id, text)
            text = ''
    if text != '':
        bot.send_message(message.chat.id, text)
