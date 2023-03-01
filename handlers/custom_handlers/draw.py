import os

from telebot.types import Message
from loguru import logger

from loader import bot
from database.database import User, Aircraft
from keyboards.reply.keyboard_start import keyboard_start
from utils.misc.map import draw_map
from utils.save_history import save_history


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Отрисовать полученные данные")
def draw(message: Message) -> None:
    """
    Функция, для выполнения запроса пользователя "Отрисовать полученные данные".

    :argument:
        message (Message): Ответ пользователя

    """
    try:
        aircraft = list(Aircraft.select().where(Aircraft.user == message.from_user.id))
        if len(aircraft) == 0:
            bot.send_message(message.chat.id, 'Для начала необходимо получить данные!',
                             reply_markup=keyboard_start())
        else:
            user = User.get(User.id == message.from_user.id)
            location_user = list(map(float, user.location.split(', ')))
            bbox = list(map(float, user.bbox.split(', ')))

            lat = list()
            lng = list()

            for air in aircraft:
                lat.append(air.latitude)
                lng.append(air.longitude)

            if not os.path.exists(os.path.join(os.getcwd(), 'temp')):
                os.makedirs(os.path.join(os.getcwd(), 'temp'))

            name_map = draw_map(location_user, [lat, lng], bbox, os.path.join(os.getcwd(), 'temp'))

            with open(os.path.join(os.getcwd(), 'temp', f'{name_map}'), 'rb') as image:
                bot.send_photo(message.chat.id, image)

            if os.path.isfile(os.path.join(os.getcwd(), 'temp', f'{name_map}')):
                os.remove(os.path.join(os.getcwd(), 'temp', f'{name_map}'))

            save_history(message.from_user.id, "Отрисовать полученные данные")

            bot.send_message(message.chat.id, f"{user}, что дальше?\n",
                             reply_markup=keyboard_start())
    except Exception as error:
        logger.error(error.__class__.__name__)
        bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте еще раз', reply_markup=keyboard_start())
