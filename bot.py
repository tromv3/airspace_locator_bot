import telebot
import os
import json
from telebot import types

from config import TOKEN
from person import Person
from database import DB
from services.aircraft import get_aircraft
from services.geocoder import geocoder
from services.map import draw_map

bot = telebot.TeleBot(TOKEN)

keyboard_start = types.InlineKeyboardMarkup(row_width=1)
button_ch_user = types.InlineKeyboardButton(text="Изменить имя", callback_data='change_name')
button_address = types.InlineKeyboardButton(text="Изменить местоположение", callback_data='change_address')
button_aircraft = types.InlineKeyboardButton(text="Получить данные о воздушных судах", callback_data='get_distation')
button_info = types.InlineKeyboardButton(text="Подробно о воздушном судне", callback_data="aircraft_info")
button_draw = types.InlineKeyboardButton(text="Отрисовать полученные данные", callback_data='draw_map')

keyboard_start.add(button_ch_user, button_address, button_aircraft, button_draw, button_info)

keyboard_address = types.InlineKeyboardMarkup(row_width=2)
button_s_address = types.InlineKeyboardButton(text="Ввести адрес", callback_data='set_location_address')
button_s_coord = types.InlineKeyboardButton(text="Ввести координаты", callback_data='set_location_coord')
button_s_location = types.InlineKeyboardButton(text="Отправить свое местоположение",
                                               callback_data='set_location_geo',
                                               request_location=True)
keyboard_address.add(button_s_address, button_s_coord, button_s_location)


@bot.message_handler(commands=['start'])
def start_message(message):
    db = DB()
    if not db.select_single(message.from_user.id):
        user = Person(message.from_user.id, message.from_user.first_name, message.from_user.last_name)
        db.add_user(user)
    else:
        user = db.select_single(message.from_user.id)
    db.close()
    bot.send_message(message.chat.id, f" Привет, {user}!\n", reply_markup=keyboard_start)


@bot.callback_query_handler(func=lambda callback: True)
def callback_inline(callback: types.CallbackQuery) -> None:
    if callback.data == "change_name":
        send = bot.send_message(callback.message.chat.id, 'Введите новое имя\n(напр. Иван Иванов или Иван):',
                                reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(send, change_name)

    elif callback.data == "change_address":
        bot.send_message(callback.message.chat.id, 'Выберите способ ввода:', reply_markup=keyboard_address)

    elif callback.data == "get_distation":
        db = DB()
        user = db.select_single(callback.message.chat.id)
        db.close()
        if not user.get_location():
            bot.send_message(callback.message.chat.id, 'Для начала укажите местоположение!',
                             reply_markup=keyboard_start)
        else:
            send = bot.send_message(callback.message.chat.id, "Введите радиус поиска (от 100 до 500 км):",
                                    reply_markup=types.ReplyKeyboardRemove())
            bot.register_next_step_handler(send, info_aircraft)

    elif callback.data == "aircraft_info":
        db = DB()
        user = db.select_single(callback.message.chat.id)
        db.close()
        if not user.get_aircraft():
            bot.send_message(callback.message.chat.id, 'Для начала необходимо получить данные!',
                             reply_markup=keyboard_start)
        else:
            aircraft = json.loads(user.get_aircraft())
            aircraft = aircraft[0:-1]
            markup = types.InlineKeyboardMarkup()
            info_air = list()
            for air in aircraft:
                info_air.append(air['aircraft_icao'])
            info_air = set(info_air)
            for air in info_air:
                markup.add(types.InlineKeyboardButton(f"Cамолет: {air}",
                                                      url=f"https://skybrary.aero/aircraft/{air}"))
            bot.send_message(callback.message.chat.id, "При последнем поиске были следующие "
                                                       "воздушные судна.", reply_markup=markup)
            bot.send_message(callback.message.chat.id, 'Что дальше?', reply_markup=keyboard_start)

    elif callback.data == "draw_map":
        try:
            db = DB()
            user = db.select_single(callback.message.chat.id)
            db.close()
            if not user.get_aircraft():
                bot.send_message(callback.message.chat.id, 'Для начала необходимо получить данные!',
                                 reply_markup=keyboard_start)
            else:
                aircraft = json.loads(user.get_aircraft())
                location_user = list(map(float, user.get_location().split(', ')))
                bbox = aircraft[-1]
                aircraft = aircraft[0:-1]
                lat = list()
                lng = list()
                for air in aircraft:
                    lat.append(air['lat'])
                    lng.append(air['lng'])
                if not os.path.exists(os.path.join(os.getcwd(), 'services', 'temp')):
                    os.makedirs(os.path.join(os.getcwd(), 'services', 'temp'))
                name_map = draw_map(location_user, [lat, lng], bbox, os.path.join(os.getcwd(), 'services', 'temp'))
                with open(os.path.join(os.getcwd(), 'services', 'temp', f'{name_map}'), 'rb') as image:
                    bot.send_photo(callback.message.chat.id, image)
                if os.path.isfile(os.path.join(os.getcwd(), 'services', 'temp', f'{name_map}')):
                    os.remove(os.path.join(os.getcwd(), 'services', 'temp', f'{name_map}'))
                bot.send_message(callback.message.chat.id, f"{user}, что дальше?\n",
                                 reply_markup=keyboard_start)
        except:
            bot.send_message(callback.message.chat.id, 'Что-то пошло не так, попробуйте еще раз',
                             reply_markup=keyboard_start)

    elif callback.data == "set_location_address":
        send = bot.send_message(callback.message.chat.id, 'Введите адрес:\n(напр. москва рабочая 36):',
                                reply_markup=types.ReplyKeyboardRemove())
        bot.register_next_step_handler(send, decode_address)

    elif callback.data == "set_location_coord":
        db = DB()
        user = db.select_single(callback.message.chat.id)
        db.close()
        send = bot.send_message(callback.message.chat.id, f"{user}, отправьте свои координаты в формате: "
                                                          f"широта, долгота (напр. 12.3456, 65.4321)")
        bot.register_next_step_handler(send, validation_coordinate)

    elif callback.data == "set_location_geo":
        db = DB()
        user = db.select_single(callback.message.chat.id)
        db.close()
        keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        button_location = types.KeyboardButton(text="Отправить свое местоположение", request_location=True)
        keyboard.add(button_location)
        bot.send_message(callback.message.chat.id, f"{user}, для отправки своего местоположения необходимо нажать "
                                                   f"'Отправить свое местоположение'", reply_markup=keyboard)


def change_name(message):
    new_name = str(message.text).split()
    # TODO: Необходимо добавить валидацию
    if len(new_name) <= 2:
        if len(new_name) == 0:
            bot.send_message(message.from_user.id, "Введена пустая строка!", reply_markup=keyboard_start)
        else:
            db = DB()
            user = db.select_single(message.from_user.id)
            if len(new_name) == 1:
                user.set_name(first_name=str(new_name[0].capitalize()))
                db.change_user(user)
                db.close()
            elif len(new_name) == 2:
                user.set_name(first_name=str(new_name[0].capitalize()),
                              last_name=str(new_name[1].capitalize()))
                db.change_user(user)
                db.close()
            bot.send_message(message.from_user.id, f"Имя изменено. Теперь я буду вас звать: {user}!",
                             reply_markup=keyboard_start)
    else:
        bot.send_message(message.from_user.id, "Неверный ввод!", reply_markup=keyboard_start)


@bot.message_handler(content_types=['location'])
def location_message(message):
    db = DB()
    user = db.select_single(message.from_user.id)
    user.set_location('{}, {}'.format(message.location.latitude, message.location.longitude))
    db.set_user_location(user)
    db.close()
    bot.send_message(message.chat.id, f"{user}, Ваше местоположение записано!\n",
                     reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(message.chat.id, f"{user}, что дальше?\n",
                     reply_markup=keyboard_start)


def is_digit(string):
    if string.isdigit():
        return True
    else:
        try:
            float(string)
            return True
        except ValueError:
            return False


def validation_coordinate(message):
    coordinate = str(message.text).split(', ')
    if len(coordinate) == 2:
        if is_digit(coordinate[0]) and is_digit(coordinate[1]):
            if -90 <= float(coordinate[0]) <= 90 and -180 <= float(coordinate[1]) <= 180:
                db = DB()
                user = db.select_single(message.from_user.id)
                user.set_location('{}, {}'.format(coordinate[0], coordinate[1]))
                db.set_user_location(user)
                db.close()
                bot.send_message(message.chat.id, f"{user}, Ваше местоположение записано!\n",
                                 reply_markup=types.ReplyKeyboardRemove())
                bot.send_message(message.chat.id, f"{user}, что дальше?\n",
                                 reply_markup=keyboard_start)
            else:
                bot.send_message(message.from_user.id, "Неверный ввод!", reply_markup=keyboard_start)
        else:
            bot.send_message(message.from_user.id, "Неверный ввод!", reply_markup=keyboard_start)
    else:
        bot.send_message(message.from_user.id, "Неверный ввод!", reply_markup=keyboard_start)


def decode_address(message):
    result = geocoder(message.text)
    if int(result['qc']) == 5:
        bot.send_message(message.from_user.id, "Не удалось определить координаты:", reply_markup=keyboard_address)
    else:
        if int(result['qc']) == 0:
            bot.send_message(message.from_user.id, "Удалось определить точные координаты:")
        elif 1 <= int(result['qc']) <= 2:
            bot.send_message(message.from_user.id, "Удалось определить ближайшие координаты:")
        else:
            bot.send_message(message.from_user.id, "Удалось определить координаты населенного пункта:")

        db = DB()
        user = db.select_single(message.from_user.id)
        user.set_location('{}, {}'.format(result['geo_lat'], result['geo_lon']))
        db.set_user_location(user)
        db.close()
        bot.send_message(message.chat.id, f"{user}, Ваше местоположение записано!\n"
                                          f"({result['result']} | [{user.get_location()}])",
                         reply_markup=types.ReplyKeyboardRemove())
        bot.send_message(message.chat.id, f"{user}, что дальше?\n",
                         reply_markup=keyboard_start)


def info_aircraft(message):
    if not (is_digit(message.text) and 100 <= int(message.text) <= 500):
        bot.send_message(message.chat.id, 'Неверно введено расстояние!', reply_markup=keyboard_start)
    else:
        # TODO: Добавить фильтры: высота(мин, макс), принадлежность, тип
        db = DB()
        user = db.select_single(message.chat.id)
        db.close()
        location = user.get_location().split(', ')
        result = get_aircraft(float(location[0]), float(location[1]), int(message.text))

        bbox = list(map(float, result['request']['params']['bbox'].split(',')))
        aircraft = list(result['response'])

        for air in aircraft:
            text = str(f"Рег. номер: {air['reg_number']}\n"
                       f"Страна: {air['flag']} | "
                       f"Тип: {air['aircraft_icao']}\n"
                       f"Широта: {air['lat']} | Долгота: {air['lng']}\n"
                       f"Высота: {air['alt']}")
            bot.send_message(message.chat.id, text, parse_mode='Markdown')
        bot.send_message(message.chat.id, 'Что дальше?', reply_markup=keyboard_start)
        # TODO: Добавить поля bbox в Person
        aircraft.append(bbox)
        db = DB()
        user = db.select_single(message.chat.id)
        user.set_aircraft(json.dumps(aircraft))
        db.set_aircraft(user)
        db.close()


if __name__ == '__main__':
    bot.polling(none_stop=True)
