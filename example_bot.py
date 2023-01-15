import telebot

import config

bot = telebot.TeleBot(config.TOKEN)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Привет! В данный момент я знаю только 3 команды:\n"
                                      "1. - Привет;\n"
                                      "2. - /help;\n"
                                      "3. - /hello_world.\n")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text.lower() == "привет":
        bot.send_message(message.from_user.id, "Привет, скоро я многому научусь!")

    elif message.text.lower() == "/help":
        bot.send_message(message.from_user.id, "Я знаю только 3 команды:\n"
                                               "1. - Привет;\n"
                                               "2. - /help;\n"
                                               "3. - /hello_world.\n")

    elif message.text.lower() == "/hello_world":
        bot.send_message(message.from_user.id, "Старый-добрый 'Привет мир!'.")

    else:
        bot.send_message(message.from_user.id, "Я тебя не понимаю. Напиши '/help'.")


bot.polling(none_stop=True, interval=0)
