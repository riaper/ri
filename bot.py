from datetime import datetime as dt
import telebot
import threading
import time
import json
import re

from weather_api import get_days, get_current, get_hours, get_coords, parse_icon


TOKEN = '1358249505:AAFXgoTa4iIJOwgJ5UmuaF7YD8HRXfuJiZE'
ERROR_MSG = '<b>Неверный формат команд</b>\n\n' \
            '1) <i>/city "city_name"</i> — установить локацию по названию города\n' \
            '2) <i>/coords "lat" "lon"</i> — установить локацию по широте и долготе соответственно\n' \
            '3) <i>/current</i> — для погоды сейчас\n' \
            '4) <i>/hours "hours_count"</i> — для погоды через <i>hours_count</i> часов\n' \
            '5) <i>/days "days_count"</i> — для погоды через <i>days_count</i> дней\n' \
            '6) <i>/follow</i> — подписаться на ежедневные погодные уведомления\n' \
            '7) <i>/unfollow</i> — отписаться от ежедневных погодных уведомлений\n'
LOCATION_ERROR_MSG = 'Локация не указана'
CITY_NOT_FOUND_ERROR_MSG = 'Город с таким названием не найден'
LOCATION_SUCCESS_MSG = 'Локация успешно обновлена'
FOLLOW_SUCCESS_MSG = 'Теперь вы следите за погодой'
UNFOLLOW_SUCCESS_MSG = 'Вы больше не следите за погодой'
NO_INFO_ERROR_MSG = 'Пока что нет прогноза на данную дату'
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['city'])
def handle_city(msg):
    if re.match(r'^/city(\s[\w-]{3,})(,[a-zA-Z]{2,4})?$', msg.text) is None:
        handle_error(msg.chat.id, ERROR_MSG)
    else:
        city = msg.text.split()[1]
        coords = get_coords(city)
        if coords is None:
            bot.send_message(msg.chat.id, CITY_NOT_FOUND_ERROR_MSG)
            return
        update_json(msg.chat.id, city=city, coords=coords)
        bot.send_message(msg.chat.id, LOCATION_SUCCESS_MSG)


@bot.message_handler(commands=['coords'])
def handle_city(msg):
    if re.match(r'^/coords(\s\d+(\.\d+)?)(\s\d+(\.\d+)?)$', msg.text) is None:
        handle_error(msg.chat.id, ERROR_MSG)
    else:
        coords = [float(msg.text.split()[1]), float(msg.text.split()[2])]
        update_json(msg.chat.id, city='', coords=coords)
        bot.send_message(msg.chat.id, LOCATION_SUCCESS_MSG)


@bot.message_handler(commands=['current'])
def current_weather(msg):
    if re.match(r'^/current$', msg.text) is None:
        handle_error(msg.chat.id, ERROR_MSG)
    else:
        user_info = fetch_user_info(msg.chat.id)
        if user_info is None:
            bot.send_message(msg.chat.id, LOCATION_ERROR_MSG)
            return
        weather = get_current(*user_info['coords'])
        bot.send_message(
            msg.chat.id,
            get_ready_msg(**weather),
            parse_mode='html',
            disable_web_page_preview=False
        )


@bot.message_handler(commands=['hours'])
def current_weather(msg):
    if re.match(r'^/hours\s\d+$', msg.text) is None:
        handle_error(msg.chat.id, ERROR_MSG)
    else:
        user_info = fetch_user_info(msg.chat.id)
        if user_info is None:
            bot.send_message(msg.chat.id, LOCATION_ERROR_MSG)
            return
        weather = get_hours(msg.text.split()[1], *user_info['coords'])
        if weather is None:
            bot.send_message(msg.chat.id, NO_INFO_ERROR_MSG)
        else:
            bot.send_message(
                msg.chat.id,
                get_ready_msg(**weather),
                parse_mode='html',
                disable_web_page_preview=False
            )


@bot.message_handler(commands=['days'])
def current_weather(msg):
    if re.match(r'^/days\s\d+', msg.text) is None:
        handle_error(msg.chat.id, ERROR_MSG)
    else:
        user_info = fetch_user_info(msg.chat.id)
        if user_info is None:
            bot.send_message(msg.chat.id, LOCATION_ERROR_MSG)
            return
        weather = get_days(msg.text.split()[1], *user_info['coords'])
        if weather is None:
            bot.send_message(msg.chat.id, NO_INFO_ERROR_MSG)
        else:
            bot.send_message(
                msg.chat.id,
                get_ready_msg(**weather),
                parse_mode='html',
                disable_web_page_preview=False
            )


@bot.message_handler(commands=['follow'])
def follow(msg):
    if re.match(r'^/follow$', msg.text) is None:
        handle_error(msg.chat.id, ERROR_MSG)
    user_info = fetch_user_info(msg.chat.id)
    if user_info is None:
        bot.send_message(msg.chat.id, LOCATION_ERROR_MSG)
        return
    update_json(msg.chat.id, follow=True)
    bot.send_message(msg.chat.id, FOLLOW_SUCCESS_MSG)


@bot.message_handler(commands=['unfollow'])
def follow(msg):
    if re.match(r'^/unfollow$', msg.text) is None:
        handle_error(msg.chat.id, ERROR_MSG)
    user_info = fetch_user_info(msg.chat.id)
    if user_info is None:
        bot.send_message(msg.chat.id, LOCATION_ERROR_MSG)
        return
    update_json(msg.chat.id, follow=False)
    bot.send_message(msg.chat.id, UNFOLLOW_SUCCESS_MSG)


@bot.message_handler(content_types=['text'])
def handle_text(msg):
    handle_error(msg.chat.id, ERROR_MSG)


def handle_error(*args):
    bot.send_message(*args, parse_mode='html')


def update_json(user_id, **kwargs):
    with open('db.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    try:
        db[str(user_id)].update(kwargs)
    except KeyError:
        db[str(user_id)] = kwargs

    with open('db.json', 'w', encoding='utf-8') as f:
        json.dump(db, f)


def fetch_user_info(chat_id):
    with open('db.json', 'r', encoding='utf-8') as f:
        db = json.load(f)

    try:
        return db[str(chat_id)]
    except KeyError:
        return


def get_ready_msg(is_icon=True, **kwargs):
    return f'<b><u>Сводка по погоде</u></b>\n\n' \
           f'<b>Временная зона</b>: {kwargs["timezone"]}\n' \
           f'<b>Дата и время</b>: {dt.fromtimestamp(kwargs["dt"]).strftime("%a, %d. %b %Y %H:%M")}\n' \
           f'<b>Погода</b>: {kwargs["weather"][0]["main"]}\n' \
           f'<b>Температура</b>: {kwargs["temp"]["day"] if isinstance(kwargs["temp"], dict) else kwargs["temp"]} °C\n' \
           f'<b>Ощущается</b>: ' \
           f'{kwargs["feels_like"]["day"] if isinstance(kwargs["feels_like"], dict) else kwargs["feels_like"]} °C\n' \
           f'<b>Давление</b>: {kwargs["pressure"]} мм рт. ст.\n' \
           f'<b>Влажность</b>: {kwargs["humidity"]} %\n' \
           f'<b>Облачность</b>: {kwargs["clouds"]} %\n' \
           f'<b>Скорость ветра</b>: {kwargs["wind_speed"]} м/с\n' \
           f'<a href="{parse_icon(kwargs["weather"][0]["icon"]) if is_icon else ""}">&#8205;</a>'


def poll_follow_worker():
    time.sleep(2)
    while True:
        with open('db.json', 'r', encoding='utf-8') as f:
            followers = json.load(f)
        for chat_id, kwargs in followers.items():
            if 'follow' in kwargs.keys() and kwargs['follow']:
                weather = get_current(*kwargs['coords'])
                bot.send_message(
                    chat_id,
                    get_ready_msg(**weather),
                    parse_mode='html',
                    disable_web_page_preview=False
                )
        time.sleep(15)


if __name__ == '__main__':
    threading.Thread(target=poll_follow_worker).start()
    bot.polling(none_stop=True)
