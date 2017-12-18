#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Простой диалоговый бот, помогающий узнать цену ремонта техники Apple
# Создан с помощью библиотеки https://github.com/python-telegram-bot/python-telegram-bot

# Импортируем модули
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler, ConversationHandler)
import logging

# Импортируем ORM peewee
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

# Словарь локализации
langs = {
"en_US": {"screen": "the screen is broken",
	"button": "the button is broken",
	"liquid": "liquid got inside",
	"cam": "cam is broken",
	"mic": "mic is broken",
	"connector": "connector is broken",
	"yes": "Yes",
	"no": "No",
	"three_months": "3 months",
	"fifteen_min": "15 minutes",
	"twenty_min": "20 minutes",
	"thirty_min": "30 minutes",
	"forty_min": "40 minutes",
	"four_hours": "from 4 hours",
	"hello": "Hello, %s, I'm an AppleCrash bot (applecrash.ru), I can help you to know the cost of repair of iPhone and iPad.\nCould you tell me, what device you have?",
	"ask_model": "Excellent! So, you need repair of %s, what mark do you have?",
	"ask_fault": "You have %s %s, what is exactly wrong with it?",
	"if_dont_know": "If you don't know, what is exactly wrong with it, our master can come to you and check your device for free\nIf you agree, press \"Yes\"",
	"iphone_after_eight": "You have iPhone %s, they have been released on the Russian market just recently, that means that prices for the parts have to be checked, press \"Yes\" to make request for the cost",
	"result_with_screen": "If %s, the cost will be %s rubles + protective glass as a present!\nThe guarantee is from %s. The repair will take about %s\nThe cost includes visit of our master to your place\nIf you agree, press \"Yes\"",
	"resulting": "If %s, the cost will be %s rubles.\nThe guarantee is from %s. The repair will take about %s\nThe cost includes visit of our master to your place\nIf you agree, press \"Yes\"",
	"other": "other",
	"I_dont_know": "I don't know",
	"start_again": "Start again",
	"know_the_price": "I want to know the price",
	"full_price": "Send me full price",
	"ask_the_price": "You can choose your device or download full price",
	"promotions": "promotions",
	"first_promo": "-20% with this bot!",
	"see_price": "See price",
	"download_price": "U can see the price by pressing the link below",
	"to_start_again": "For starting again press \"Start again\"",
	},
"ru_RU": {"screen": "разбился экран",
	"button": "сломалась кнопка",
	"liquid": "попала жидкость",
	"cam": "cломалась камера",
	"mic": "сломался микрофон",
	"connector": "сломался разъём",
	"yes": "Да",
	"no": "Нет",
	"three_months": "3-х месяцев",
	"fifteen_min": "15 минут",
	"twenty_min": "20 минут",
	"thirty_min": "30 минут",
	"forty_min": "40 минут",
	"four_hours": "от 4-х часов",
	"hello": "Привет, %s, я бот AppleCrash (applecrash.ru) - Ваш помощник по вопросам быстрого ремонта техники Apple в Москве и Московской области.\nНиже вы можете увидеть, что я могу:",
	"ask_model": "Отлично! Вам нужен ремонт %s, какая у Вас модель?",
	"ask_fault": "У Вас %s %s, что именно неисправно?",
	"if_dont_know": "Если Вы не знаете, что именно у Вас неисправно, к Вам может выехать мастер и провести бесплатную диагностику\nЕсли Вас это устраивает, нажмите \"Да\"",
	"iphone_after_eight": "У Вас iPhone %s, в России они поступили в продажу совсем недавно, а это значит, что цены на запчасти нужно будет уточнять, нажмите \"Да\", чтобы оставить запрос цены",
	"result_with_screen": "Если у Вас %s, то ремонт у нас будет стоить %s рублей + защитное стекло в подарок!\nГарантия %s. Ремонт займёт примерно %s\nВ цену входит выезд мастера в удобное для Вас место!\nЕсли Вас это устраивает, нажмите \"Да\"",
	"resulting": "Если у Вас %s, то ремонт у нас будет стоить %s рублей.\nГарантия от %s. Ремонт займёт примерно %s\nВ цену входит выезд мастера в удобное для Вас место!\nЕсли Вас это устраивает, нажмите \"Да\"",
	"other": "другое",
	"I_dont_know": "я не знаю",
	"start_again": "Начать сначала",
	"know_the_price": "Хочу узнать цену ремонта",
	"full_price": "Получить полный список цен",
	"ask_the_price": "Вы можете выбрать устройство и узнать конкретную цену или скачать полный список цен",
	"promotions": "Рассказать про акции и скидки",
	"first_promo": "Скидка 20% при заказе через бота",
	"see_price": "Посмотреть прайс",
	"download_price": "Чтобы посмотреть прайс, нажмите кнопку ниже:",
	"to_start_again": "Чтобы начать сначала, нажмите \"Начать сначала\"",
	}}
iphone_after_eight = "У Вас iPhone %s, в России они поступили в продажу совсем недавно, а это значит, что цены на запчасти нужно будет уточнять, нажмите \"Да\", чтобы оставить запрос цены"
result_with_screen = "Если у Вас %s, то ремонт у нас будет стоить %s рублей + защитное стекло в подарок!\nГарантия от %s. Ремонт займёт примерно %s\nВ цену входит выезд мастера в удобное для Вас место!\nЕсли Вас это устраивает, нажмите \"Да\""
resulting = "Если у Вас %s, то ремонт у нас будет стоить %s рублей.\nГарантия от %s. Ремонт займёт примерно %s\nВ цену входит выезд мастера в удобное для Вас место!\nЕсли Вас это устраивает, нажмите \"Да\""
send_contact = "отправить контакт"
no_contact = "Пожалуй, я откажусь"
ask_contact = "Отлично! Оставьте, пожалуйста, свой контакт для связи"
price = "Цена"
terms = "Сроки"
necessity_contacts = "Необходимость оставлять контактные данные"
so_sad = "Жаль :( В целях улучшения бота, скажите, что именно Вас не устроило?"
thank_you_bad = "Спасибо за отзыв, мы обязательно используем эту информацию для улучшения нашего бота в будущем!\nЕсли хотите попробовать снова, нажмите \"Начать сначала\" или отправьте любой текст\nОбратная связь: @chernikovden, +79999776258 Дмитрий"
thank_you_good = "Спасибо! В ближайшее время с Вами свяжется менеджер для уточнения деталей.\nОбратная связь: @chernikovden, +79999776258 Дмитрий"
if_cancel = "К сожалению, я не могу распознать введённый Вами текст, давайте начнём сначала?"

faults_iphone = {
        "5": {"screen": ["2900", "three_months", "fifteen_min"], "button": ["от 1400", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["1400", "three_months", "thirty_min"], "mic": ["1300", "three_months", "thirty_min"], "connector": ["от 1400", "three_months", "thirty_min"]},
        "5c": {"screen": ["2900", "three_months", "fifteen_min"], "button": ["от 1600", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["от 1900", "three_months", "thirty_min"], "mic": ["1700", "three_months", "thirty_min"], "connector": ["1700", "three_months", "thirty_min"]},
        "5s": {"screen": ["2900", "three_months", "fifteen_min"], "button": ["от 1600", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["от 1900", "three_months", "thirty_min"], "mic": ["1700", "three_months", "thirty_min"], "connector": ["1700", "three_months", "thirty_min"]},
        "5se": {"screen": ["4500", "three_months", "fifteen_min"], "button": ["от 3500", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 3500", "three_months", "thirty_min"], "mic": ["3500", "three_months", "thirty_min"], "connector": ["3600", "three_months", "thirty_min"]},
        "6": {"screen": ["3600", "three_months", "fifteen_min"], "button": ["от 3500", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 3500", "three_months", "thirty_min"], "mic": ["3500", "three_months", "thirty_min"], "connector": ["3600", "three_months", "thirty_min"]},
        "6c": {"screen": ["5400", "three_months", "fifteen_min"], "button": ["от 3500", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 3500", "three_months", "thirty_min"], "mic": ["3500", "three_months", "thirty_min"], "connector": ["3600", "three_months", "thirty_min"]},
        "6s": {"screen": ["7500", "three_months", "fifteen_min"], "button": ["от 3500", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 3500", "three_months", "thirty_min"], "mic": ["3500", "three_months", "thirty_min"], "connector": ["3600", "three_months", "thirty_min"]},
        "6+": {"screen": ["4400", "three_months", "fifteen_min"], "button": ["4200", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 3500", "three_months", "thirty_min"], "mic": ["3500", "three_months", "thirty_min"], "connector": ["3600", "three_months", "thirty_min"]},
        "6s+": {"screen": ["7000", "three_months", "fifteen_min"], "button": ["4200", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 3500", "three_months", "thirty_min"], "mic": ["3500", "three_months", "thirty_min"], "connector": ["3600", "three_months", "thirty_min"]},
        "7": {"screen": ["8000", "three_months", "fifteen_min"], "button": ["4200", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 3500", "three_months", "thirty_min"], "Сломался мик рофон": ["3500", "three_months", "thirty_min"], "connector": ["3600", "three_months", "thirty_min"]},
        "7+": {"screen": ["10900", "three_months", "fifteen_min"], "button": ["4200", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 3500", "three_months", "thirty_min"], "mic": ["3500", "three_months", "thirty_min"], "connector": ["3600", "three_months", "thirty_min"]},
        "8": {"screen": ["30900", "three_months", "fifteen_min"], "button": ["9200", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 9500", "three_months", "thirty_min"], "mic": ["9500", "three_months", "thirty_min"], "connector": ["9600", "three_months", "thirty_min"]},
        "8+": {"screen": ["30900", "three_months", "fifteen_min"], "button": ["9200", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 9500", "three_months", "thirty_min"], "mic": ["9500", "three_months", "thirty_min"], "connector": ["9600", "three_months", "thirty_min"]},
        "X": {"screen": ["30900", "three_months", "fifteen_min"], "button": ["9200", "three_months", "thirty_min"], "liquid": ["от 3500", "three_months", "four_hours"], "cam": ["от 9500", "three_months", "thirty_min"], "mic": ["9500", "three_months", "thirty_min"], "connector": ["9600", "three_months", "thirty_min"]},
    }
faults_ipad = {
        "1": {"screen": ["3400", "three_months", "forty_min"], "button": ["2000", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["от 1900", "three_months", "thirty_min"], "mic": ["1500", "three_months", "thirty_min"], "connector": ["2000", "three_months", "thirty_min"]},
        "2": {"screen": ["3500", "three_months", "forty_min"], "button": ["2000", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["от 1900", "three_months", "thirty_min"], "mic": ["1500", "three_months", "thirty_min"], "connector": ["2000", "three_months", "thirty_min"]},
        "3": {"screen": ["3500", "three_months", "forty_min"], "button": ["2200", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["от 2000", "three_months", "thirty_min"], "mic": ["1700", "three_months", "thirty_min"], "connector": ["2000", "three_months", "thirty_min"]},
        "4": {"screen": ["3500", "three_months", "forty_min"], "button": ["2200", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["от 2000", "three_months", "thirty_min"], "mic": ["2000", "three_months", "thirty_min"], "connector": ["2000", "three_months", "thirty_min"]},
        "Air": {"screen": ["4500", "three_months", "forty_min"], "button": ["2600", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["от 2300", "three_months", "thirty_min"], "mic": ["от 2300", "three_months", "thirty_min"], "connector": ["2500", "three_months", "thirty_min"]},
        "Air 2": {"screen": ["18000", "three_months", "forty_min"], "button": ["2600", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["2900", "three_months", "thirty_min"], "mic": ["от 2300", "three_months", "thirty_min"], "connector": ["2500", "three_months", "thirty_min"]},
        "Mini": {"screen": ["4500", "three_months", "forty_min"], "button": ["2500", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["2500", "three_months", "thirty_min"], "mic": ["1500", "three_months", "thirty_min"], "connector": ["2200", "three_months", "thirty_min"]},
        "Mini 2": {"screen": ["4500", "three_months", "forty_min"], "button": ["2500", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["2500", "three_months", "thirty_min"], "mic": ["1500", "three_months", "thirty_min"], "connector": ["2200", "three_months", "thirty_min"]},
        "Mini 3": {"screen": ["4500", "three_months", "forty_min"], "button": ["2500", "three_months", "thirty_min"], "liquid": ["от 1500", "three_months", "four_hours"], "cam": ["3100", "three_months", "thirty_min"], "mic": ["1500", "three_months", "thirty_min"], "connector": ["2200", "three_months", "thirty_min"]},
    }

def start(bot, update):
    reply_keyboard = [['English'], ['Русский']]
    # Проверяем, есть ли в нашей базе данный пользователь, в случае отсутствия - создаём его
    try:
        Users.get(chat_id=update.message.chat_id).chat_id
    except:
        user = Users.create(chat_id=update.message.chat_id, nickname=update.message.from_user.username, first_name=update.message.from_user.first_name, last_name=update.message.from_user.last_name)
    update.message.reply_text("Пожалуйста, выберите свой язык. \n(Please, choose your language).", reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return MENU
    
def menu(bot, update):
    user = Users.get(chat_id=update.message.chat_id)
    if update.message.text == 'English':
        user.lang = "en_US"
    elif update.message.text == 'Русский':
        user.lang = "ru_RU"
    user.first_step_lang = "yes" # Маркер первого шага
    user.save()
    lang = Users.get(chat_id=update.message.chat_id).lang
    name = Users.get(chat_id=update.message.chat_id).first_name
    reply_keyboard = [[langs[lang]["know_the_price"]], [langs[lang]["promotions"]]]
    update.message.reply_text(langs[lang]["hello"] % name, reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return CHOOSE

def promotions(bot, update):
    user = Users.get(chat_id=update.message.chat_id)
    user.second_step_choose = "узнать акции" # Маркер второго шага
    lang = Users.get(chat_id=update.message.chat_id).lang
    reply_keyboard = [[langs[lang]["start_again"]]]
    update.message.reply_photo(photo="AgADAgADk6gxG8EEwEkPv7Z27gipHaziDw4ABMDGXUBxL3xm0h0EAAEC", caption=langs[lang]["first_promo"]) # Отсылаем фото акции по идентификатору в базе данных Telegram
    update.message.reply_text(langs[lang]["to_start_again"], reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return AGAIN
    

def know_the_price(bot, update):
    user = Users.get(chat_id=update.message.chat_id)
    user.second_step_choose = "узнать цену"
    lang = Users.get(chat_id=update.message.chat_id).lang
    reply_keyboard = [["iPhone", "iPad"], [langs[lang]["full_price"]]]
    update.message.reply_text(langs[lang]["ask_the_price"], reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return DEVICE

def full_price(bot, update):
    user = Users.get(chat_id=update.message.chat_id)
    user.second_step_choose = "скачать прайс"
    lang = Users.get(chat_id=update.message.chat_id).lang
    reply_keyboard = [[langs[lang]["start_again"]]]
    keyboard = [[InlineKeyboardButton(langs[lang]["see_price"], url='https://docs.google.com/spreadsheets/d/1OK-gHe7BJlh2UiQt4_BtUXXNuUy4tVNdA0QtQYbplQw/edit?usp=sharing')]]
    update.message.reply_text(langs[lang]["download_price"], reply_markup=InlineKeyboardMarkup(keyboard, one_time_keyboard=True))
    update.message.reply_text(langs[lang]["to_start_again"], reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return AGAIN
    

def iphone(bot, update):
    user = Users.get(chat_id=update.message.chat_id)
    lang = Users.get(chat_id=update.message.chat_id).lang
    reply_keyboard = [["5", "5c", "5s", "5se"], ["6", "6c", "6s", "6+", "6s+"], ["7", "7+", "8", "8+", "X"], [langs[lang]["start_again"]]]
    user.device = update.message.text
    update.message.reply_text(langs[lang]["ask_model"] % user.device,
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return IPHONE
    
def ipad(bot, update):
    reply_keyboard = [["1", "2", "3", "4"], ["Air", "Air 2", "Mini", "Mini 2", "Mini 3"], [start_again]]
    INFO["device"] = update.message.text
    update.message.reply_text(ask_model % INFO["device"],
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return IPAD
    
def choice(bot, update):
    user = Users.get(chat_id=update.message.chat_id)
    lang = Users.get(chat_id=update.message.chat_id).lang
    user.device_model = update.message.text
    reply_keyboard = [[langs[lang]["screen"], langs[lang]["liquid"]], [langs[lang]["button"], langs[lang]["cam"]], [langs[lang]["mic"], langs[lang]["connector"]], [langs[lang]["other"], langs[lang]["I_dont_know"]], [langs[lang]["start_again"]]]
    update.message.reply_text(langs[lang]["ask_fault"] % (user.device, user.device_model), reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return RESULT

def result(bot, update):
    INFO["fault"] = update.message.text
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

def ask_info(bot, update):
    contact_keyboard = KeyboardButton(text=send_contact, request_contact=True)
    reply_keyboard = [[contact_keyboard, no_contact], [start_again]]    
    update.message.reply_text(ask_contact,
                             reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return END

def ask_again(bot, update):
    reply_keyboard = [[price, terms], [necessity_contacts], [start_again]]
    update.message.reply_text(so_sad, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    
    return BAD_END

def bad_end(bot, update):
    INFO["what_bad"] = update.message.text
    reply_keyboard = [[start_again]]
    update.message.reply_text(thank_you_bad, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    bot.sendMessage(chat_id = 130955703, text = 'Заказ от %s %s\nАппарат: %s %s\nНеисправность: %s\nЧто не устроило: %s\nСсылка на telegram: @%s\nchat_id: %s' % 
                    (INFO["first_name"], INFO["last_name"], INFO["device"], INFO["device_model"], INFO["fault"], INFO["what_bad"], INFO["username"], INFO["chat_id"]))
    bot.sendMessage(chat_id = 226052695, text = 'Заказ от %s %s\nАппарат: %s %s\nНеисправность: %s\nЧто не устроило: %s\nСсылка на telegram: @%s\nchat_id: %s' % 
                    (INFO["first_name"], INFO["last_name"], INFO["device"], INFO["device_model"], INFO["fault"], INFO["what_bad"], INFO["username"], INFO["chat_id"]))
    return ConversationHandler.END
        
def end(bot, update):
    INFO["connect"] = update.message.text if update.message.text else "+" + update.message.contact.phone_number
    reply_keyboard = [[start_again]]
    update.message.reply_text(thank_you_good, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    bot.sendMessage(chat_id = 130955703, text = 'Заказ от %s %s\nАппарат: %s %s\nНеисправность: %s\nДанные для связи: %s\nСсылка на telegram: @%s\nchat_id: %s' % 
                    (INFO["first_name"], INFO["last_name"], INFO["device"], INFO["device_model"], INFO["fault"], INFO["connect"], INFO["username"], INFO["chat_id"]))
    bot.sendMessage(chat_id = 226052695, text = 'Заказ от %s %s\nАппарат: %s %s\nНеисправность: %s\nДанные для связи: %s\nСсылка на telegram: @%s\nchat_id: %s' % 
                    (INFO["first_name"], INFO["last_name"], INFO["device"], INFO["device_model"], INFO["fault"], INFO["connect"], INFO["username"], INFO["chat_id"]))
    return ConversationHandler.END
    
def cancel(bot, update):
    reply_keyboard = [[start_again]]
    update.message.reply_text(if_cancel, reply_markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True))
    return ConversationHandler.END

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
