import datetime
import os
from loguru import logger
from peewee import *


db = SqliteDatabase(os.path.join(os.getcwd(), 'database', 'bot.db'))


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = IntegerField(null=False)
    name = CharField(null=True)
    location = CharField(null=True)
    bbox = CharField(null=True)
    last_req = DateTimeField(null=True)

    def __str__(self):
        return str(self.name)


class Aircraft(BaseModel):
    user = ForeignKeyField(User, related_name='aircraft')
    reg_number = CharField(null=True)
    flag = CharField(null=True)
    type_plane = CharField(null=True)
    latitude = FloatField(null=True)
    longitude = FloatField(null=True)
    alt = IntegerField(null=True)


class History(BaseModel):
    user = ForeignKeyField(User, related_name='history')
    command = CharField(null=True)
    date = DateTimeField(default=datetime.datetime.now)

    class Meta:
        database = db
        order_by = ('date',)


tables = [User, Aircraft, History]
db.create_tables(tables)
logger.debug('Таблицы созданы успешно.')

