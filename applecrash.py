#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Простой диалоговый бот, помогающий узнать цену ремонта техники Apple
# Создан с помощью библиотеки https://github.com/python-telegram-bot/python-telegram-bot

# Импортируем модули
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)

from localisation import *
from faults import *

import logging
import functools

from peewee import *

# Определяем базу данных и таблицу "Users"
db = SqliteDatabase('users.db')

class Users(Model):
    chat_id = IntegerField()
    nickname = CharField(max_length = 255)
    first_name = CharField(max_length = 255)
    last_name = CharField(max_length = 255)
    lang = CharField(max_length = 255)
    contact = CharField(max_length = 255)
    device = CharField(max_length = 255)
    device_model = CharField(max_length = 255)
    fault = CharField(max_length = 255)
    first_step_lang = CharField(max_length = 255)
    second_step_choose = CharField(max_length = 255)
    what_bad = CharField(max_length = 255)

    class Meta:
        database = db

# Активируем logging
logging.basicConfig(format='%(asctime)s -%(name)s -%(levelname)s -%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем переменные для состояний
DEVICE, IPHONE, IPAD, RESULT, ASK_INFO, END, BAD_END, CHOOSE, MENU, AGAIN = range(10)

INFO = {}

# Декоратор для проверки id пользователя
def check_user(func):
    logger = logging.getLogger(func.__module__)
    @functools.wraps(func) #используем декоратор function.wraps для копирования информации об оборачиваемой функции
    def check(*args, **kwargs):
        logger.info('Entering: {}'.format(func.__name__))
        bot, update = args
        for a in args:
            logger.info(a)        
        user = Users.get(chat_id=update.message.chat_id)
        kwargs['user'] = user
        result = func(*args, **kwargs)
        logger.info('Exiting: {}'.format(func.__name__))
        return result
    return check

def start(bot, update, **kwargs):
    reply_keyboard = [['English'], ['Русский']]
    # Проверяем, есть ли в нашей базе данный пользователь, в случае отсутствия - создаём его
    try:
        Users.get(chat_id=update.message.chat_id).chat_id
    except:
        user = Users.create(chat_id=update.message.chat_id, nickname=update.message.from_user.username, first_name=update.message.from_user.first_name, last_name=update.message.from_user.last_name)
    update.message.reply_text("Пожалуйста, выберите свой язык. \n(Please, choose your language).", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MENU
    
@check_user
def menu(bot, update, **kwargs):
    user = kwargs['user']

    if update.message.text == 'English':
        user.lang = "en_US"
    elif update.message.text == 'Русский':
        user.lang = "ru_RU"

    user.first_step_lang = "yes" # Маркер первого шага
    user.save()

    reply_keyboard = [[langs[user.lang]["know_the_price"]], [langs[user.lang]["promotions"]]]
    update.message.reply_text(langs[user.lang]["hello"].format(user.first_name), reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSE

@check_user
def promotions(bot, update, **kwargs):
    user = kwargs['user']

    user.second_step_choose = "узнать акции" # Маркер второго шага
    user.save()
    
    reply_keyboard = [[langs[user.lang]["start_again"]]]
    update.message.reply_photo(photo="AgADAgADk6gxG8EEwEkPv7Z27gipHaziDw4ABMDGXUBxL3xm0h0EAAEC", caption=langs[user.lang]["first_promo"]) # Отсылаем фото акции по идентификатору в базе данных Telegram

    contact_promo_button = KeyboardButton(text=langs[user.lang]["send_contact"], request_contact=True)
    reply_keyboard = [[contact_promo_button, langs[user.lang]["no_contact"]], [langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["ask_contact_promo"],
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return END
    
@check_user
def know_the_price(bot, update, **kwargs):
    user = kwargs['user']
    user.second_step_choose = "узнать цену" # Маркер второго шага
    
    user.second_step_choose = "узнать цену"
    user.save()

    reply_keyboard = [["iPhone", "iPad"], [langs[user.lang]["full_price"]]]
    update.message.reply_text(langs[user.lang]["ask_the_price"], reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return DEVICE

@check_user
def full_price(bot, update, **kwargs):
    user = kwargs['user']

    user.second_step_choose = "скачать прайс"
    user.save()

    keyboard = [[InlineKeyboardButton(langs[user.lang]["see_price"], url='https://docs.google.com/spreadsheets/d/1OK-gHe7BJlh2UiQt4_BtUXXNuUy4tVNdA0QtQYbplQw/edit?usp=sharing')]]
    update.message.reply_text(langs[user.lang]["download_price"], reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))

    reply_keyboard = [[langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["to_start_again"], reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

#    contact_keyboard = KeyboardButton(text=send_contact, request_contact=True)
#    reply_keyboard = [[contact_keyboard, langs[user.lang]["no_contact"]], [langs[user.lang]["start_again"]]]    
#    update.message.reply_text(ask_contact,
#                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    
    return AGAIN
    
@check_user
def iphone(bot, update, **kwargs):
    user = kwargs['user']
    user.device = update.message.text
    user.save()

    reply_keyboard = [["5", "5c", "5s", "5se"], ["6", "6c", "6s", "6+", "6s+"], ["7", "7+", "8", "8+", "X"], [langs[user.lang]["start_again"]]]

    update.message.reply_text(langs[user.lang]["ask_model"].format(user.device),
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return IPHONE
    
@check_user
def ipad(bot, update, **kwargs):
    user = kwargs['user']
    user.device = update.message.text
    user.save()

    reply_keyboard = [["1", "2", "3", "4"], ["Air", "Air 2", "Mini", "Mini 2", "Mini 3"], [langs[user.lang]["start_again"]]]

    update.message.reply_text(langs[user.lang]["ask_model"].format(user.device),
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return IPAD

@check_user
def choice(bot, update, **kwargs):
    user = kwargs['user']
    user.device_model = update.message.text
    user.save()

    reply_keyboard = [[langs[user.lang]["screen"], langs[user.lang]["liquid"]], [langs[user.lang]["button"], langs[user.lang]["cam"]], [langs[user.lang]["mic"], langs[user.lang]["connector"]], [langs[user.lang]["other"], langs[user.lang]["I_dont_know"]], [langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["ask_fault"].format(user.device, user.device_model), reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return RESULT

def result(bot, update, **kwargs):
    user = Users.get(chat_id=update.message.chat_id)
    user.fault = update.message.text
    for phrase in langs[user.lang]:
        if user.fault == langs[user.lang][phrase]:
            user.fault = phrase
    user.save()

    yes_no_keyboard = [[langs[user.lang]["yes"], langs[user.lang]["no"]], [langs[user.lang]["start_again"]]]
    yes_no_markup = ReplyKeyboardMarkup(yes_no_keyboard, one_time_keyboard=True)

    if user.fault == "other" or user.fault == "I_dont_know":
            update.message.reply_text(langs[user.lang]["if_dont_know"], reply_markup = yes_no_markup)
    else:
        if user.device == "iPhone":
            result_text = faults_iphone[user.device_model][user.fault]
        elif user.device == "iPad":
            result_text = faults_ipad[user.device_model][user.fault]
        if user.device == "iPhone" and (user.device_model == "8" or user.device_model == "8+" or user.device_model == "X"):
            update.message.reply_text(langs[user.lang]["iphone_after_eight"].format(user.device_model), reply_markup=yes_no_markup)
        elif user.fault == "screen":
            update.message.reply_text(langs[user.lang]["result_with_screen"].format(langs[user.lang][user.fault], langs[user.lang].get(result_text[0], result_text[0]), langs[user.lang][result_text[1]], langs[user.lang][result_text[2]]), reply_markup=yes_no_markup)
        else:
            update.message.reply_text(langs[user.lang]["resulting"].format(langs[user.lang][user.fault], langs[user.lang].get(result_text[0], result_text[0]), langs[user.lang][result_text[1]], langs[user.lang][result_text[2]]), reply_markup=yes_no_markup)
    return ASK_INFO

@check_user
def ask_info(bot, update, **kwargs):
    user = kwargs['user']

    contact_keyboard = KeyboardButton(text = langs[user.lang]["send_contact"], request_contact=True)
    reply_keyboard = [[contact_keyboard, no_contact], [langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["ask_contact"],
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return END

@check_user
def ask_again(bot, update, **kwargs):
    user = kwargs['user']

    reply_keyboard = [[langs[user.lang]["price"], langs[user.lang]["terms"]], [langs[user.lang]["necessity_contacts"]], [langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["so_sad"], reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    
    return BAD_END

@check_user
def bad_end(bot, update, **kwargs):
    user = kwargs['user']

    user.what_bad = update.message.text
    user.save()

    reply_keyboard = [[langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["thank_you_bad"], reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    total_info = ('Заказ от {} {}\nАппарат: {} {}\nНеисправность: {}\nЧто не устроило: {}\nСсылка на telegram: @{}\nchat_id: {}'.format(user.first_name,
                                user.last_name, user.device, user.device_model, langs[user.lang][user.fault], user.what_bad, user.nickname, user.chat_id))

    for chatid in [130955703, 226052695]:
        bot.sendMessage(chat_id=chatid, text = total_info)

    return ConversationHandler.END

@check_user        
def end(bot, update, **kwargs):
    user = kwargs['user']
    user.contact = update.message.text if update.message.text else "+" + update.message.contact.phone_number
    user.save()

    reply_keyboard = [[langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["thank_you_good"], reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))

    total_info = ('Заказ от {} {}\nАппарат: {} {}\nНеисправность: {}\nЧто не устроило: {}\nСсылка на telegram: @{}\nchat_id: {}'.format(user.first_name,
                                user.last_name, user.device, user.device_model, langs[user.lang][user.fault], user.what_bad, user.nickname, user.chat_id))

    for chatid in [130955703, 226052695]:
        bot.sendMessage(chat_id=chatid, text=total_info)
        return ConversationHandler.END

@check_user
def cancel(bot, update, **kwargs):
    user = kwargs['user']
    reply_keyboard = [[langs[user.lang]["start_again"]]]
    update.message.reply_text(if_cancel, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return ConversationHandler.END


# Выводим в логи ошибки
def error(bot, update, error):
    logger.warning('Update "{}" caused error "{}"'.format(update, error))


def main():
    updater = Updater("418052681:AAHSUdS0xUriYpOC6ro3dU8Rm0hWmpvDMzU")

    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', start), MessageHandler(Filters.text, start)],
        
	# состояния, на каждом шаге, если парсер не находит ответа из списка - начинаем сначала
        states = {
            MENU: [RegexHandler('^(English|Русский)$', menu),
                     MessageHandler(Filters.text, start),],
            AGAIN: [MessageHandler(Filters.text, start),],
            CHOOSE: [RegexHandler('^(I want to know the price|Хочу узнать цену ремонта)$', know_the_price),
                     RegexHandler('^(promotions|Рассказать про акции и скидки)$', promotions),
                     MessageHandler(Filters.text, start),],
            DEVICE: [RegexHandler('^iPhone$', iphone),
                     RegexHandler('^iPad$', ipad),
                     RegexHandler('^(Send me full price|Получить полный список цен)$', full_price),
                     MessageHandler(Filters.text, start),],
            IPHONE: [RegexHandler('^(5|5c|5s|5se|6|6c|6s|6\+|6s\+|7|7\+|8|8\+|X)$', choice), RegexHandler('^Начать сначала$', start), MessageHandler(Filters.text, cancel)],
            IPAD: [RegexHandler('^(1|2|3|4|Air|Air 2|Mini|Mini 2|Mini 3)$', choice), RegexHandler('^Начать сначала$', start), MessageHandler(Filters.text, start)],
            RESULT: [RegexHandler('^(разбился экран|попала жидкость|сломалась кнопка|сломалась камера|сломался микрофон|сломался разъём|другое|я не знаю|the screen is broken|the button is broken|liquid got inside|cam is broken|mic is broken|connector is broken|other|I don\'t know)$', result), RegexHandler('^Начать сначала$', start), MessageHandler(Filters.text, start)],
            ASK_INFO: [RegexHandler('^(Да|Yes)$', ask_info),
                       RegexHandler('^(Нет|No)$', ask_again),
                       RegexHandler('^(Начать сначала|Start again)$', start),
                       MessageHandler(Filters.text, start)],
            END: [MessageHandler(Filters.contact, end),  RegexHandler('^(Начать сначала|Start again)$', start), MessageHandler(Filters.text, ask_again)],
            BAD_END: [ RegexHandler('^(Начать сначала|Start again)$', start), MessageHandler(Filters.text, bad_end)]
        },
        
        fallbacks = [CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
