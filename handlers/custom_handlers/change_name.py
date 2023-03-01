from telebot import types
from telebot.types import Message

from loader import bot
from states.name_user import ChangeNameState
from database.database import User
from keyboards.reply.keyboard_start import keyboard_start
from utils.save_history import save_history


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Изменить имя")
def change_name(message: Message) -> None:
    """
    Функция, для запроса нового имени от пользователя

    :argument:
        message (Message): Ответ пользователя

    """
    bot.set_state(message.from_user.id, ChangeNameState.name, message.chat.id)
    bot.send_message(message.chat.id, "Введите новое имя\n(напр. Иван Иванов или Иван):",
                     reply_markup=types.ReplyKeyboardRemove())
    save_history(message.from_user.id, "Изменить имя")


@bot.message_handler(state=ChangeNameState.name)
def set_name(message: Message) -> None:
    """
    Функция, для валидации и сохранения нового имени пользователя

    :argument:
        message (Message): Ответ пользователя

    """
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
