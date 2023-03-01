from telebot import types

from loader import bot
from states.set_location import SetLocationState
from database.database import User
from keyboards.reply.keyboard_address import keyboard_address
from keyboards.reply.keyboard_start import keyboard_start
from utils.misc.geocoder import geocoder


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Изменить местоположение")
def location(message) -> None:
    bot.set_state(message.from_user.id, SetLocationState.location, message.chat.id)
    bot.send_message(message.chat.id, 'Отправьте точку на карте, либо выберите метод ввода:',
                     reply_markup=keyboard_address())


@bot.message_handler(state=SetLocationState.location, content_types=["location"])
def get_location_button(message):
    user = User.get(User.id == message.from_user.id)
    user.location = '{}, {}'.format(message.location.latitude, message.location.longitude)
    user.save()
    bot.send_message(message.chat.id, f"{user}, Ваше местоположение записано!\n", reply_markup=keyboard_start())


@bot.message_handler(state=SetLocationState.location, func=lambda message: message.text == "Ввести адрес")
def get_location_address(message):
    bot.set_state(message.from_user.id, SetLocationState.address, message.chat.id)
    bot.send_message(message.chat.id, "Введите адрес:\n(напр. москва рабочая 36):",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(state=SetLocationState.address, content_types=["text"])
def set_location_address(message):
    result = geocoder(message.text)
    if result['geo_lat'] is None or result['geo_lon'] is None:
        bot.send_message(message.from_user.id, "К сожалению не удалось определить координаты. Попробуйте еще раз:")
    else:
        bot.send_message(message.from_user.id, "Удалось определить следующие координаты:")
        user = User.get(User.id == message.from_user.id)
        user.location = '{}, {}'.format(result['geo_lat'], result['geo_lon'])
        user.save()
        bot.delete_state(message.from_user.id, message.chat.id)
        bot.send_message(message.chat.id,
                         f"{user}, Ваше местоположение записано!\n"
                         f"({result['result']} | [{user.location}])",
                         reply_markup=keyboard_start())


@bot.message_handler(state=SetLocationState.location, func=lambda message: message.text == "Ввести координаты")
def get_location_coordinate(message):
    bot.set_state(message.from_user.id, SetLocationState.coordinate, message.chat.id)
    bot.send_message(message.chat.id,
                     f"Отправьте свои координаты в формате: "
                     f"\nширота, долгота (напр. 12.3456, 65.4321)",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(state=SetLocationState.coordinate, content_types=["text"])
def set_location_coordinate(message):
    def is_digit(string):
        if string.isdigit():
            return True
        else:
            try:
                float(string)
                return True
            except ValueError:
                return False

    coordinate = str(message.text).split(', ')
    if len(coordinate) == 2:
        if is_digit(coordinate[0]) and is_digit(coordinate[1]):
            if -90 <= float(coordinate[0]) <= 90 and -180 <= float(coordinate[1]) <= 180:
                user = User.get(User.id == message.from_user.id)
                user.location = '{}, {}'.format(coordinate[0], coordinate[1])
                user.save()
                bot.delete_state(message.from_user.id, message.chat.id)
                bot.send_message(message.chat.id,
                                 f"{user}, Ваше местоположение записано!\n",
                                 reply_markup=keyboard_start())
            else:
                bot.send_message(message.from_user.id, "Неверный ввод! Попробуйте еще раз.")
        else:
            bot.send_message(message.from_user.id, "Неверный ввод! Попробуйте еще раз.")
    else:
        bot.send_message(message.from_user.id, "Неверный ввод! Попробуйте еще раз.")


