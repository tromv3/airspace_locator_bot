"""Bot-wide constants that don't belong in Settings (not sourced from env)."""

HISTORY_LIMIT = 50  # Сколько последних записей истории хранится и показывается на пользователя

DEFAULT_COMMANDS = (
    ("start", "Запустить бота"),
    ("cancel", "Вернуться к главному меню"),
    ("history", f"Показать выполненные запросы (последние {HISTORY_LIMIT})"),
    ("help", "Вывести справку"),
)
