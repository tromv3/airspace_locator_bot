import os
from loguru import logger
from dotenv import load_dotenv, find_dotenv

if not find_dotenv():
    logger.error("Переменные окружения не загружены т.к отсутствует файл .env")
    exit("Переменные окружения не загружены т.к отсутствует файл .env")
else:
    load_dotenv()
    logger.info("Переменные окружения загружены.")

BOT_TOKEN = os.getenv("BOT_TOKEN")
AIR_LABS_API_KEY = os.getenv("AIR_LABS_API_KEY")
DADATA_TOKEN = os.getenv("DADATA_TOKEN")
DADATA_SECRET_KEY = os.getenv("DADATA_SECRET_KEY")

count_req = 50  # Количество запросов пользователя храниться в БД

DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("cancel", "Вернуться к главному меню"),
    ("history", f"Показать выполненные запросы (последние {str(count_req)})"),
    ("help", "Вывести справку"),
)
