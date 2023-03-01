from config_data import config
from dadata import Dadata


dadata = Dadata(config.DADATA_TOKEN, config.DADATA_SECRET_KEY)


def geocoder(user_address: str):
    return dadata.clean("address", user_address)


if __name__ == "__main__":
    print(geocoder('подольск '))

