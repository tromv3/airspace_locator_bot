from database.database import User, History


def save_history(id_user: int, command: str) -> None:
    """
    Функция, для сохранения запросов пользователя.

    :argument:
        id_user (int): id пользователь
        command (str): выполненная команда

    """
    History.create(user=User.get(id=id_user), command=command).save()
    # requests = History.select().order_by(History.date)
    # print(requests)
