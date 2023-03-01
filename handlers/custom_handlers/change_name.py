from telebot import types

from loader import bot
from states.name_user import ChangeNameState
from database.database import User
from keyboards.reply.keyboard_start import keyboard_start


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Изменить имя")
def change_name(message) -> None:
    bot.set_state(message.from_user.id, ChangeNameState.name, message.chat.id)
    bot.send_message(message.chat.id, "Введите новое имя\n(напр. Иван Иванов или Иван):",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(state=ChangeNameState.name)
def set_name(message):
    new_name = str(message.text).split()
    if len(new_name) <= 2 and "".join(new_name).isalpha():
        if len(new_name) == 0:
            bot.send_message(message.from_user.id, "Введена пустая строка!")
        else:
            user = User.get(User.id == message.from_user.id)
            user.name = " ".join(word.capitalize() for word in new_name)
            user.save()
            bot.delete_state(message.from_user.id, message.chat.id)
            bot.send_message(message.from_user.id, f"Имя изменено. Теперь я буду Вас звать:\n{user}!",
                             reply_markup=keyboard_start())

    else:
        bot.send_message(message.from_user.id, "Некорректный ввод! Попробуйте еще раз.")
