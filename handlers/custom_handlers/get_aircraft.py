from telebot import types
from telebot.types import Message

from loader import bot
from states.get_aircraft import GetAircraftState
from database.database import User, Aircraft
from keyboards.reply.keyboard_start import keyboard_start
from keyboards.reply.keyboard_filters import keyboard_filters
from utils.misc.aircraft import get_aircraft
from utils.save_history import save_history


@bot.message_handler(content_types=["text"], func=lambda message: message.text == "Получить данные о воздушных судах")
def get_dist(message: Message) -> None:
    """
    Функция, для выполнения запроса пользователя "Получить данные о воздушных судах".

    :argument:
        message (Message): Ответ пользователя

    """
    user = User.get(User.id == message.from_user.id)
    if user.location is not None:
        bot.set_state(message.from_user.id, GetAircraftState.dist, message.chat.id)
        bot.send_message(message.chat.id, "Введите радиус поиска (от 100 до 500 км):",
                         reply_markup=types.ReplyKeyboardRemove())
        save_history(message.from_user.id, "Получить данные о воздушных судах")
    else:
        bot.send_message(message.chat.id,
                         "Необходимо указать местоположение.",
                         reply_markup=keyboard_start())


@bot.message_handler(state=GetAircraftState.dist, is_digit=True)
def get_air(message: Message) -> None:
    """
    Функция, для валидации введенного пользователем расстояния и
    получения данных с сайта http://airlabs.co/.

    :argument:
        message (Message): Ответ пользователя

    """
    if 150 <= int(message.text) <= 500:
        bot.set_state(message.from_user.id, GetAircraftState.filters, message.chat.id)
        user = User.get(User.id == message.chat.id)
        get_aircraft(user, int(message.text))
        aircraft = Aircraft.select().where(Aircraft.user == user.id)
        bot.send_message(message.chat.id,
                         f"Всего найдено {len(aircraft)} воздушных судов. Выберите действие.",
                         reply_markup=keyboard_filters())
        save_history(message.from_user.id, f"Всего найдено {len(aircraft)} воздушных судов")
    else:
        bot.send_message(message.chat.id, "Необходимо ввести число от 100 до 500.")


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Фильтр по высоте (max)")
def filter_alt_max(message: Message) -> None:
    """
    Функция, для получения информации от пользователя для применения фильтра по высоте (max).

    :argument:
        message (Message): Ответ пользователя

    """
    bot.set_state(message.from_user.id, GetAircraftState.filter_alt, message.chat.id)
    bot.send_message(message.chat.id, f"Введите максимальную высоту.",
                     reply_markup=types.ReplyKeyboardRemove())
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["filter"] = "max"


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Фильтр по высоте (min)")
def filter_alt_min(message: Message) -> None:
    """
    Функция, для получения информации от пользователя для применения фильтра по высоте (min).

    :argument:
        message (Message): Ответ пользователя

    """
    bot.set_state(message.from_user.id, GetAircraftState.filter_alt, message.chat.id)
    bot.send_message(message.chat.id, f"Введите минимальную высоту.",
                     reply_markup=types.ReplyKeyboardRemove())
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data["filter"] = "min"


@bot.message_handler(state=GetAircraftState.filter_alt, is_digit=True)
def set_filter_alt(message: Message) -> None:
    """
    Функция, для применения фильтра по высоте.

    :argument:
        message (Message): Ответ пользователя

    """
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
    save_history(message.from_user.id, f"Применен фильтр по высоте.")


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Фильтр по типу")
def filter_type(message: Message) -> None:
    """
    Функция, для получения информации от пользователя для применения фильтра по типу судна.

    :argument:
        message (Message): Ответ пользователя

    """
    bot.set_state(message.from_user.id, GetAircraftState.filter_type, message.chat.id)
    aircraft = Aircraft.select().where(Aircraft.user == message.from_user.id)
    plane_type = set([air.type_plane.upper() for air in aircraft if air.type_plane is not None])
    bot.send_message(message.chat.id, f"Введите тип:\n{', '.join(plane_type)}",
                     reply_markup=types.ReplyKeyboardRemove())
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['plane_type'] = plane_type


@bot.message_handler(state=GetAircraftState.filter_type)
def set_filter_type(message: Message) -> None:
    """
    Функция, для применения фильтра по типу судна.

    :argument:
        message (Message): Ответ пользователя

    """
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
            save_history(message.from_user.id, f"Применен фильтр по типу судна.")
        else:
            bot.send_message(message.chat.id,
                             f"Введите один из предложенных вариантов:\n{', '.join(data['plane_type'])}")


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Фильтр по принадлежности")
def filter_flag(message: Message) -> None:
    """
    Функция, для получения информации от пользователя для применения фильтра по принадлежности судна.

    :argument:
        message (Message): Ответ пользователя

    """
    bot.set_state(message.from_user.id, GetAircraftState.filter_flag, message.chat.id)
    aircraft = Aircraft.select().where(Aircraft.user == message.from_user.id)
    flags = set([air.flag for air in aircraft if air.flag is not None])
    bot.send_message(message.chat.id, f"Введите принадлежность:\n{', '.join(flags)}",
                     reply_markup=types.ReplyKeyboardRemove())
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['flag'] = flags


@bot.message_handler(state=GetAircraftState.filter_flag)
def set_filter_flag(message: Message) -> None:
    """
    Функция, для применения фильтра по принадлежности судна.

    :argument:
        message (Message): Ответ пользователя

    """
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
            save_history(message.from_user.id, f"Применен фильтр по принадлежности судна.")
        else:
            bot.send_message(message.chat.id, f"Введите один из предложенных вариантов:\n{', '.join(data['flag'])}")


@bot.message_handler(state=GetAircraftState.filters, func=lambda message: message.text == "Показать воздушные суда")
def show(message: Message) -> None:
    """
    Функция, для вывода информации о воздушных судах пользователю.

    :argument:
        message (Message): Ответ пользователя

    """
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
        text += '-' * 10 + '\n'
        if len(text) + 100 > 4000:
            bot.send_message(message.chat.id, text)
            text = ''
    if text != '':
        bot.send_message(message.chat.id, text)

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.send_message(message.chat.id, 'Что дальше?', reply_markup=keyboard_start())
    save_history(message.from_user.id, f"Показано воздушных судов: {len(aircraft)}")


@bot.message_handler(state=GetAircraftState.dist, is_digit=False)
def dist_incorrect(message: Message) -> None:
    """
    Функция, для валидации расстояния введенного пользователем.

    :argument:
        message (Message): Ответ пользователя

    """
    bot.send_message(message.chat.id, "Необходимо ввести число от 100 до 500.")


@bot.message_handler(state=GetAircraftState.filter_alt, is_digit=False)
def alt_incorrect(message: Message) -> None:
    """
    Функция, для валидации высоты введенной пользователем.

    :argument:
        message (Message): Ответ пользователя

    """
    bot.send_message(message.chat.id, "Необходимо ввести положительное число.")


# TODO: Сохранение примененных фильтров для отражения на рисунке
