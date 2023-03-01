from telebot.types import Message

from loader import bot
from keyboards.reply.keyboard_start import keyboard_start


@bot.message_handler(commands=["cancel"], state="*")
def bot_cancel(message: Message) -> None:
    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, "Выберите действие.", reply_markup=keyboard_start())
