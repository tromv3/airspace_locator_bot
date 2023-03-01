import datetime
import os
from loguru import logger
from peewee import *


db = SqliteDatabase(os.path.join(os.getcwd(), 'database', 'bot.db'))


class BaseModel(Model):
    """
     Класс BaseModel. Базовый класс.

     """

    class Meta:
        database = db


class User(BaseModel):
    """
    Класс User(пользователь). Родительский класс BaseModel.

    Attributes:
        id (int): id пользователя
        name (str): имя пользователя
        location (str): точка стояния
        bbox (str): область, определяемая двумя долготами и двумя широтами
        last_req (datetime): дата и время последнего запроса пользователя

    """

    id = IntegerField(null=False)
    name = CharField(null=True)
    location = CharField(null=True)
    bbox = CharField(null=True)
    last_req = DateTimeField(null=True)

    def __str__(self):
        return str(self.name)


class Aircraft(BaseModel):
    """
    Класс Aircraft(воздушное судно). Родительский класс BaseModel.

    Attributes:
        user (object): id пользователя, который делал запрос по данному судну
        reg_number (str): регистрационный номер воздушного судна
        flag (str): принадлежность воздушного судна (страна)
        type_plane (str): тип воздушного судна
        latitude (float): широта местоположения
        longitude (float): долгота местоположения
        alt (int): высота полета


    """
    user = ForeignKeyField(User, related_name='aircraft')
    reg_number = CharField(null=True)
    flag = CharField(null=True)
    type_plane = CharField(null=True)
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
    alt = IntegerField(null=True)


class History(BaseModel):
    """
    Класс History(история запросов). Родительский класс BaseModel.

    Attributes:
        user (object): id пользователя, который выполнял команду
        command (str): выполняемая команда
        date (datetime): дата и время выполнения команды

    """
    user = ForeignKeyField(User, related_name='history')
    command = CharField(null=True)
    date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        order_by = ('date',)


tables = [User, Aircraft, History]
try:
    db.create_tables(tables)
    logger.info("Таблицы созданы успешно.")
except Exception as error:
    logger.error(f"Не удалось создать таблицы! {error.__class__.__name__}")

