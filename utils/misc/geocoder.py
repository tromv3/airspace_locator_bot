from config_data import config
from dadata import Dadata
from typing import Dict


dadata = Dadata(config.DADATA_TOKEN, config.DADATA_SECRET_KEY)


def geocoder(user_address: str) -> Dict:
    """
    Функция для определения точки по адресу

    :argument:
        user_address (str): адрес

    :return:
        (Dict): информация по полученному адресу

    """
    return dadata.clean("address", user_address)


if __name__ == "__main__":
    print(geocoder('подольск '))
