import os
from telebot import types
from telebot.types import Message

from loader import bot
from database.database import User, Aircraft
from keyboards.reply.keyboard_start import keyboard_start
from utils.misc.map import draw_map


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Отрисовать полученные данные")
def draw(message: Message) -> None:
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
            bot.send_message(message.chat.id, f"{user}, что дальше?\n",
                             reply_markup=keyboard_start())
    except:
        bot.send_message(message.chat.id, 'Что-то пошло не так, попробуйте еще раз', reply_markup=keyboard_start())
