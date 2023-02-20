from config import dadata_token, dadata_secret
from dadata import Dadata


dadata = Dadata(dadata_token, dadata_secret)


def geocoder(user_address: str):
    return dadata.clean("address", user_address)


if __name__ == "__main__":
    print(geocoder('подольск '))

