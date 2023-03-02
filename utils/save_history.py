from database.database import User, History
from config_data.config import count_req


def save_history(id_user: int, command: str) -> None:
    """
    Функция, для сохранения запросов пользователя.

    :argument:
        id_user (int): id пользователь
        command (str): выполненная команда

    """
    History.create(user=User.get(id=id_user), command=command).save()
    history = list(History.select().where(History.user == id_user).order_by(History.date))
    if len(history) > count_req:
        for req in history[0:-count_req]:
            req.delete_instance()
