from telebot.types import Message

from loader import bot
from database.database import Aircraft
from keyboards.reply.keyboard_start import keyboard_start
from keyboards.inline.plane_info import keyboard_plane
from utils.save_history import save_history


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Подробно о воздушном судне")
def plane_info(message: Message) -> None:
    """
    Функция, для выдачи дополнительной информации по воздушным судам

    :argument:
        message (Message): Ответ пользователя

    """
    plane = list(Aircraft.select().where(Aircraft.user == message.from_user.id))
    if len(plane) == 0:
        bot.send_message(message.chat.id, "Для начала необходимо получить данные!",
                         reply_markup=keyboard_start())
    else:
        plane_type = set([air.type_plane.upper() for air in plane if air.type_plane is not None])
        bot.send_message(message.chat.id, "При последнем поиске были следующие воздушные суда.",
                         reply_markup=keyboard_plane(plane_type))
        bot.send_message(message.chat.id, 'Что дальше?', reply_markup=keyboard_start())
    save_history(message.from_user.id, "Подробно о воздушном судне")

# TODO: Добавить парсер
