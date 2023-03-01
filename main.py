from telebot.custom_filters import StateFilter, IsDigitFilter
import handlers

from loader import bot
from utils.set_bot_commands import set_default_commands

if __name__ == "__main__":
    bot.add_custom_filter(StateFilter(bot))
    bot.add_custom_filter(IsDigitFilter())
    set_default_commands(bot)
    bot.infinity_polling(skip_pending=True)

# TODO: Добавить удаление временных файлов
