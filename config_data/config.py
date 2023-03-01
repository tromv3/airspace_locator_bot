import os
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
AIR_LABS_API_KEY = os.getenv("AIR_LABS_API_KEY")
DADATA_TOKEN = os.getenv("DADATA_TOKEN")
DADATA_SECRET_KEY = os.getenv("DADATA_SECRET_KEY")

DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("help", "Вывести справку"),
    ("cancel", "Вернуться к главному меню"),
    ("history", "Показать выполненные запросы")
)

# TODO: Привести справку в порядок
