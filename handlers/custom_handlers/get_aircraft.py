from telebot import types
from telebot.types import Message

from loader import bot
from states.get_aircraft import GetAircraftState
from database.database import User, Aircraft
from keyboards.reply.keyboard_start import keyboard_start
from keyboards.reply.keyboard_filters import keyboard_filters
from utils.misc.aircraft import get_aircraft


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Получить данные о воздушных судах")
def get_dist(message: Message) -> None:
    user = User.get(User.id == message.from_user.id)
    if user.location is not None:
        bot.set_state(message.from_user.id, GetAircraftState.dist, message.chat.id)
        bot.send_message(message.chat.id, "Введите радиус поиска (от 100 до 500 км):",
                         reply_markup=types.ReplyKeyboardRemove())
    else:
        bot.send_message(message.chat.id,
                         "Необходимо указать местоположение.",
                         reply_markup=keyboard_start())


@bot.message_handler(state=GetAircraftState.dist, is_digit=True)
def get_air(message: Message):
    if 150 <= int(message.text) <= 500:
        bot.set_state(message.from_user.id, GetAircraftState.filters, message.chat.id)
        user = User.get(User.id == message.chat.id)
        get_aircraft(user, int(message.text))
        aircraft = Aircraft.select().where(Aircraft.user == user.id)
        bot.send_message(message.chat.id,
                         f"Всего найдено {len(aircraft)} воздушных судов. Выберите действие.",
                         reply_markup=keyboard_filters())
    else:
        bot.send_message(message.chat.id, "Необходимо ввести число от 100 до 500.")


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Фильтр по высоте (max)")
def filter_alt_max(message: Message):
    bot.set_state(message.from_user.id, GetAircraftState.filter_alt, message.chat.id)
    bot.send_message(message.chat.id, f"Введите максимальную высоту.",
                     reply_markup=types.ReplyKeyboardRemove())
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["filter"] = "max"


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Фильтр по высоте (min)")
def filter_alt_min(message: Message):
    bot.set_state(message.from_user.id, GetAircraftState.filter_alt, message.chat.id)
    bot.send_message(message.chat.id, f"Введите минимальную высоту.",
                     reply_markup=types.ReplyKeyboardRemove())
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["filter"] = "min"


@bot.message_handler(state=GetAircraftState.filter_alt, is_digit=True)
def set_filter_alt(message: Message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if data["filter"] == "max":
            Aircraft.delete().where(Aircraft.user == message.from_user.id,
                                    Aircraft.alt >= int(message.text)).execute()
        else:
            Aircraft.delete().where(Aircraft.user == message.from_user.id,
                                    Aircraft.alt <= int(message.text)).execute()

    bot.set_state(message.from_user.id, GetAircraftState.filters, message.chat.id)
    bot.send_message(message.chat.id,
                     f"Фильтр применен. \nВсего воздушных судов: "
                     f"{Aircraft.select().where(Aircraft.user == message.from_user.id).count()}."
                     f"\nВыберите действие:",
                     reply_markup=keyboard_filters())


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Фильтр по типу")
def filter_type(message: Message):
    bot.set_state(message.from_user.id, GetAircraftState.filter_type, message.chat.id)
    aircraft = Aircraft.select().where(Aircraft.user == message.from_user.id)
    plane_type = set([air.type_plane.upper() for air in aircraft if air.type_plane is not None])
    bot.send_message(message.chat.id, f"Введите тип:\n{', '.join(plane_type)}",
                     reply_markup=types.ReplyKeyboardRemove())
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['plane_type'] = plane_type


@bot.message_handler(state=GetAircraftState.filter_type)
def set_filter_type(message: Message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if message.text.upper() in data["plane_type"]:
            Aircraft.delete().where(Aircraft.user == message.from_user.id,
                                    Aircraft.type_plane != message.text.upper()).execute()
            bot.set_state(message.from_user.id, GetAircraftState.filters, message.chat.id)
            bot.send_message(message.chat.id,
                             f"Фильтр применен. \nВсего воздушных судов: "
                             f"{Aircraft.select().where(Aircraft.user == message.from_user.id).count()}."
                             f"\nВыберите действие:",
                             reply_markup=keyboard_filters())
        else:
            bot.send_message(message.chat.id,
                             f"Введите один из предложенных вариантов:\n{', '.join(data['plane_type'])}")


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Фильтр по принадлежности")
def filter_flag(message: Message):
    bot.set_state(message.from_user.id, GetAircraftState.filter_flag, message.chat.id)
    aircraft = Aircraft.select().where(Aircraft.user == message.from_user.id)
    flags = set([air.flag for air in aircraft if air.flag is not None])
    bot.send_message(message.chat.id, f"Введите принадлежность:\n{', '.join(flags)}",
                     reply_markup=types.ReplyKeyboardRemove())
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['flag'] = flags


@bot.message_handler(state=GetAircraftState.filter_flag)
def set_filter_flag(message: Message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        if message.text.upper() in data["flag"]:
            Aircraft.delete().where(Aircraft.user == message.from_user.id,
                                    Aircraft.flag != message.text.upper()).execute()
            bot.set_state(message.from_user.id, GetAircraftState.filters, message.chat.id)
            bot.send_message(message.chat.id,
                             f"Фильтр применен. \nВсего воздушных судов: "
                             f"{Aircraft.select().where(Aircraft.user == message.from_user.id).count()}."
                             f"\nВыберите действие:",
                             reply_markup=keyboard_filters())
        else:
            bot.send_message(message.chat.id, f"Введите один из предложенных вариантов:\n{', '.join(data['flag'])}")


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Показать воздушные суда")
def show(message: Message):
    aircraft = list(Aircraft.select().where(Aircraft.user == message.from_user.id))
    text = ''
    for air in aircraft:
        if air.reg_number is not None:
            text += f"Рег. номер: {air.reg_number}\n"
        if air.flag is not None:
            text += f"Страна: {air.flag}\n"
        if air.type_plane is not None:
            text += f"Тип: {air.type_plane}\n"
        if air.latitude is not None and air.longitude is not None:
            text += f"Широта: {air.latitude} | Долгота: {air.longitude}\n"
        if air.alt is not None:
            text += f"Высота: {air.alt}\n"
        text += '-' * 25 + '\n'
        if len(text) + 100 > 4000:
            bot.send_message(message.chat.id, text)
            text = ''
    if text != '':
        bot.send_message(message.chat.id, text)

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, 'Что дальше?', reply_markup=keyboard_start())


@bot.message_handler(state=GetAircraftState.dist, is_digit=False)
def dist_incorrect(message: Message):
    bot.send_message(message.chat.id, "Необходимо ввести число от 100 до 500.")


@bot.message_handler(state=GetAircraftState.filter_alt, is_digit=False)
def alt_incorrect(message: Message):
    bot.send_message(message.chat.id, "Необходимо ввести положительное число.")


# TODO: Сохранение примененных фильтров для отражения на рисунке
