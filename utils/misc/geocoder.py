from config_data import config
import dadata
from typing import Dict


dada = dadata.Dadata(config.DADATA_TOKEN, config.DADATA_SECRET_KEY)


def geocoder(user_address: str) -> Dict:
    """
    Функция для определения точки по адресу

    :argument:
        user_address (str): адрес

    :return:
        (Dict): информация по полученному адресу

    """
    return dada.clean("address", user_address)
