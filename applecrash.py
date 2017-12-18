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
    device = CharField(max_length = 255)
    device_model = CharField(max_length = 255)
    fault = CharField(max_length = 255)

    class Meta:
        database = db

# Активируем logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Определяем переменные для состояний
DEVICE, IPHONE, IPAD, RESULT, ASK_INFO, END, BAD_END, CHOOSE, MENU, AGAIN = range(10)

INFO = {}

# Декоратор для проверки id пользователя
def check_user(func):
    logger = logging.getLogger(func.__module__)
    @functools.wraps(func) #используем декоратор function.wraps для копирования информации об оборачиваемой функции
    def check(*args, **kwargs):
        logger.info('Entering: %s', func.__name__)
        bot, update = args
        for a in args:
            logger.info(a)        
        user = Users.get(chat_id=update.message.chat_id)
        kwargs['user'] = user
        result = func(*args, **kwargs)
        logger.info('Exiting: %s', func.__name__)
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
    name = Users.get(chat_id=update.message.chat_id).first_name
    reply_keyboard = [[langs[user.lang]["know_the_price"]], [langs[user.lang]["promotions"]]]
    update.message.reply_text(langs[user.lang]["hello"] % name, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSE

@check_user
def promotions(bot, update, **kwargs):
    user = kwargs['user']
    user.second_step_choose = "узнать акции" # Маркер второго шага
    reply_keyboard = [[langs[user.lang]["start_again"]]]
    update.message.reply_photo(photo="AgADAgADk6gxG8EEwEkPv7Z27gipHaziDw4ABMDGXUBxL3xm0h0EAAEC", caption=langs[user.lang]["first_promo"]) # Отсылаем фото акции по идентификатору в базе данных Telegram
    update.message.reply_text(langs[user.lang]["to_start_again"], reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return AGAIN
    
@check_user
def know_the_price(bot, update, **kwargs):
    user = kwargs['user']
    reply_keyboard = [["iPhone", "iPad"], [langs[user.lang]["full_price"]]]

    user.second_step_choose = "узнать цену"
    user.save()

    reply_keyboard = [[langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["ask_the_price"], reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return DEVICE

@check_user
def full_price(bot, update, **kwargs):
    user = kwargs['user']

    user.second_step_choose = "скачать прайс"
    user.save()

    reply_keyboard = [[langs[user.lang]["start_again"]]]
    keyboard = [[InlineKeyboardButton(langs[user.lang]["see_price"], url='https://docs.google.com/spreadsheets/d/1OK-gHe7BJlh2UiQt4_BtUXXNuUy4tVNdA0QtQYbplQw/edit?usp=sharing')]]
    update.message.reply_text(langs[user.lang]["download_price"], reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))
    update.message.reply_text(langs[user.lang]["to_start_again"], reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return AGAIN
    
@check_user
def iphone(bot, update, **kwargs):
    user = kwargs['user']
    reply_keyboard = [["5", "5c", "5s", "5se"], ["6", "6c", "6s", "6+", "6s+"], ["7", "7+", "8", "8+", "X"], [langs[user.lang]["start_again"]]]
    user.device = update.message.text
    update.message.reply_text(langs[user.lang]["ask_model"] % user.device,
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return IPHONE
    
@check_user
def ipad(bot, update, **kwargs):
    user = kwargs['user']
    reply_keyboard = [["1", "2", "3", "4"], ["Air", "Air 2", "Mini", "Mini 2", "Mini 3"], [start_again]]
    INFO["device"] = update.message.text
    update.message.reply_text(ask_model % INFO["device"],
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return IPAD
    
def choice(bot, update, **kwargs):
    user = Users.get(chat_id=update.message.chat_id)
    user.device_model = update.message.text
    reply_keyboard = [[langs[user.lang]["screen"], langs[user.lang]["liquid"]], [langs[user.lang]["button"], langs[user.lang]["cam"]], [langs[user.lang]["mic"], langs[user.lang]["connector"]], [langs[user.lang]["other"], langs[user.lang]["I_dont_know"]], [langs[user.lang]["start_again"]]]
    update.message.reply_text(langs[user.lang]["ask_fault"] % (user.device, user.device_model), reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return RESULT

def result(bot, update, **kwargs):
    user = Users.get(chat_id=update.message.chat_id)
    lang = user.lang
    user.fault = update.message.text    
    if INFO["fault"] == other or INFO["fault"] == idn:
            update.message.reply_text(if_dont_know, reply_markup=yes_no_markup)
    else:
        if INFO["device"] == "iPhone":
            result_text = faults_iphone[INFO["device_model"]][INFO["fault"]]
        elif INFO["device"] == "iPad":
            result_text = faults_ipad[INFO["device_model"]][INFO["fault"]]
        if INFO["device"] == "iPhone" and (INFO["device_model"] == "8" or INFO["device_model"] == "8+" or INFO["device_model"] == "X"):
            update.message.reply_text(iphone_after_eight % INFO["device_model"], reply_markup=yes_no_markup)
        elif INFO["fault"] == "screen":
            update.message.reply_text(result_with_screen % (INFO["fault"], result_text[0], result_text[1], result_text[2]), reply_markup=yes_no_markup)
        else:
            update.message.reply_text(resulting % (INFO["fault"], result_text[0], result_text[1], result_text[2]), reply_markup=yes_no_markup)
    return ASK_INFO

def ask_info(bot, update, **kwargs):
    contact_keyboard = KeyboardButton(text=send_contact, request_contact=True)
    reply_keyboard = [[contact_keyboard, no_contact], [start_again]]    
    update.message.reply_text(ask_contact,
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return END

def ask_again(bot, update, **kwargs):
    reply_keyboard = [[price, terms], [necessity_contacts], [start_again]]
    update.message.reply_text(so_sad, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    
    return BAD_END

def bad_end(bot, update, **kwargs):
    INFO["what_bad"] = update.message.text
    reply_keyboard = [[start_again]]
    update.message.reply_text(thank_you_bad, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    bot.sendMessage(chat_id = 130955703, text = 'Заказ от %s %s\nАппарат: %s %s\nНеисправность: %s\nЧто не устроило: %s\nСсылка на telegram: @%s\nchat_id: %s' % 
                    (INFO["first_name"], INFO["last_name"], INFO["device"], INFO["device_model"], INFO["fault"], INFO["what_bad"], INFO["username"], INFO["chat_id"]))
    bot.sendMessage(chat_id = 226052695, text = 'Заказ от %s %s\nАппарат: %s %s\nНеисправность: %s\nЧто не устроило: %s\nСсылка на telegram: @%s\nchat_id: %s' % 
                    (INFO["first_name"], INFO["last_name"], INFO["device"], INFO["device_model"], INFO["fault"], INFO["what_bad"], INFO["username"], INFO["chat_id"]))
    return ConversationHandler.END
        
def end(bot, update, **kwargs):
    INFO["connect"] = update.message.text if update.message.text else "+" + update.message.contact.phone_number
    reply_keyboard = [[start_again]]
    update.message.reply_text(thank_you_good, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    bot.sendMessage(chat_id = 130955703, text = 'Заказ от %s %s\nАппарат: %s %s\nНеисправность: %s\nДанные для связи: %s\nСсылка на telegram: @%s\nchat_id: %s' % 
                    (INFO["first_name"], INFO["last_name"], INFO["device"], INFO["device_model"], INFO["fault"], INFO["connect"], INFO["username"], INFO["chat_id"]))
    bot.sendMessage(chat_id = 226052695, text = 'Заказ от %s %s\nАппарат: %s %s\nНеисправность: %s\nДанные для связи: %s\nСсылка на telegram: @%s\nchat_id: %s' % 
                    (INFO["first_name"], INFO["last_name"], INFO["device"], INFO["device_model"], INFO["fault"], INFO["connect"], INFO["username"], INFO["chat_id"]))
    return ConversationHandler.END
    
def cancel(bot, update, **kwargs):
    reply_keyboard = [[start_again]]
    update.message.reply_text(if_cancel, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return ConversationHandler.END


def check(bot, update, **kwargs):
    user = Users.get(chat_id=update.message.chat_id)
    return user, lang

# Выводим в логи ошибки
def error(bot, update, error):
    logger.warn('Update "%s" caused error "%s"' % (update, error))


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
            ASK_INFO: [RegexHandler('^Да$', ask_info),
                       RegexHandler('^Нет$', ask_again),
                       RegexHandler('^Начать сначала$', start),
                       MessageHandler(Filters.text, result)],
            END: [MessageHandler(Filters.contact, end),  RegexHandler('^Начать сначала$', start), MessageHandler(Filters.text, ask_again)],
            BAD_END: [ RegexHandler('^Начать сначала$', start), MessageHandler(Filters.text, bad_end)]
        },
        
        fallbacks = [CommandHandler('cancel', cancel)]
    )

    dp.add_handler(conv_handler)

    dp.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
