import telebot
from telebot import types
import customer
import driver
import psycopg2
from psycopg2 import Error
import re

bot = telebot.TeleBot('1618386430:AAF_-TsdAqRYckgTA3rMMopDJWkJa3wRCAI')

categories = ['A', 'B', 'C', 'D', 'E']
default_price = 3000
all_ = {}
phone_pattern = r'\b\+?[7,8]7(\s*\d{2}\s*\d{3}\s*\d{2}\s*\d{2})\b'

#-------------------------------БД-------------------------------------------
def start_db():
    conn = psycopg2.connect(dbname='postgres', user='postgres', password='HamiT181', host="localhost")
    return conn.cursor()
cursor=start_db()

#-------------------------------БД-------------------------------------------
def select_from_db_drivers(cursor):
    cursor.execute('SELECT * FROM public.drivers')
    records = cursor.fetchall()

def select_from_db_clients(cursor):
    cursor.execute('SELECT * FROM public.clients')
    records = cursor.fetchall()

#-------------------------------БД-------------------------------------------
def insert_into_db_clients(user):
    DB = "INSERT INTO public.clients(chat_id, category, transmission, phone, username, price, location, location_togo) " \
        f"VALUES ({user.chat_id}, '{user.category}', '{user.transmission}', " \
        f"{user.phone}, '{user.username}', {user.price}, ARRAY{[user.location.longitude, user.location.latitude]}, " \
        f"ARRAY{[user.location_togo.longitude, user.location_togo.latitude]})"
    print(DB)
    cursor.execute(DB)

def insert_into_db_drivers(user):
    DB = "INSERT INTO public.drivers(chat_id, category, transmission, phone, username) " \
        f"VALUES ({user.chat_id}, ARRAY{user.category}, '{user.transmission}', " \
        f"{user.phone}, '{user.username}')"
    print(DB)
    cursor.execute(DB)

#--------------------------основное сообщение------------------
def other_message(message):
    keyboard0 = types.ReplyKeyboardMarkup(False, True)
    keyboard0.row('Мне нужен трезвый водитель!', 'Я трезвый водитель! (регистрация)')
    bot.send_message(message.chat.id, 'Упс, что-то пошло не так. давайте начнем с начала... ;)', reply_markup=keyboard0)

#--------------------------основные команды------------------
@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.id in all_:
        del all_[message.chat.id]
    keyboard0 = types.ReplyKeyboardMarkup(False, True)
    keyboard0.row('Мне нужен трезвый водитель!', 'Я трезвый водитель! (регистрация)')
    bot.send_message(message.chat.id, 'Вам нужен трезвый водитель? Или вы сами трезвый водитель?', reply_markup=keyboard0)
    
@bot.message_handler(commands=['help'])
def help_message(message):
    keyboard = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton('Главное меню', callback_data='/start')
    item2 = types.InlineKeyboardButton('Помощь', callback_data='/help')
    item3 = types.InlineKeyboardButton('О боте', callback_data='/about')
    item4 = types.InlineKeyboardButton('ЧАВО / FAQ', callback_data='/faq')
    keyboard.add(item1, item2, item3, item4, row_width=2)
    bot.send_message(message.chat.id, f'Цена внутри квадрата Альфараби, Саина, Рыскулова, ВОАД = {default_price}')
    bot.send_message(message.chat.id, 'Водитель имеет права отказаться ехать, если его что-то не устроит.' \
        '\nПри этом вы можете смело вызывать другого водителя.')
    bot.send_message(message.chat.id, 'Так же и хозяин имеет права отказаться от водителя, если первого что-то не устроит.' \
        '\nПри этом вы можете смело получать другой заказ.')
    bot.send_message(message.chat.id, 'Всегда проверяйте документы как водителей так и хозяев автомашин,' \
        'соблюдайте ПДД.', reply_markup=keyboard)

#--------------------------прослушка сообщений------------------
@bot.message_handler(content_types=['text', 'location', 'contact'])
def main_handler(message):
    print('--------------------------------------------------------------')
    chat_id = message.chat.id
    if message.text == 'Мне нужен трезвый водитель!':
        all_[chat_id] = customer.customer(bot, default_price)
        all_[chat_id].update_progress('select transmission')
        all_[chat_id].send_transmission_request(message)
    elif message.text == 'Я трезвый водитель! (регистрация)':
        all_[chat_id] = driver.driver(bot,default_price)
        all_[chat_id].update_progress('select transmission')
        all_[chat_id].send_transmission_request(message)
    elif not chat_id in all_:
        other_message(message)

    #----------------повтор для заказчиков-------------
    elif all_[chat_id].progress == 'select transmission' and all_[chat_id].type_ == 'need':
        bot.send_message(chat_id, 'Давайте попробуем еще раз, выберите коробку передач авто')
        all_[chat_id].send_transmission_request(message)
    elif all_[chat_id].progress == 'select category' and all_[chat_id].type_ == 'need':
        bot.send_message(chat_id, 'Давайте попробуем еще раз, выберите категорию авто')
        all_[chat_id].send_category_request(all_[chat_id].transmission, chat_id)
    elif all_[chat_id].progress == 'send phone' and all_[chat_id].type_ == 'need' and \
        message.contact == None and not re.search(phone_pattern, message.text):
        bot.send_message(chat_id, 'Давайте попробуем еще раз, отправьте номер телефона')
        all_[chat_id].send_phone_request(message, all_[chat_id].category)
    elif all_[chat_id].progress == 'send location' and all_[chat_id].type_ == 'need' and \
        message.location == None:
        bot.send_message(chat_id, 'Давайте попробуем еще раз, отправьте свое местополение')
        all_[chat_id].send_location_request(message, all_[chat_id].phone)
    elif all_[chat_id].progress == 'send location_togo' and all_[chat_id].type_== 'need' and \
        message.location == None:
        bot.send_message(chat_id, 'Давайте попробуем еще раз?')
        all_[chat_id].send_location_togo_request(message, all_[chat_id].location)
    elif all_[chat_id].progress == 'send price' and all_[chat_id].type_ == 'need':
        if message.text.isdigit() and int(message.text) >= default_price:
            all_[chat_id].send_final_message(message.text, chat_id)
            insert_into_db_clients(all_[chat_id])
        else:
            all_[chat_id].send_own_price_request(message, all_[chat_id].location_togo)
    elif all_[chat_id].progress == 'send own price' and all_[chat_id].type_ == 'need':
        all_[chat_id].send_own_price_request(message, all_[chat_id].location_togo)
    elif all_[chat_id].progress == 'send final' and all_[chat_id].type_ == 'need':
        print(all_[chat_id])
        bot.send_message(chat_id, 'Ищу водителя! \nЕсли прошло много времени попробуйте еще раз вызвать через /start' \
            '\nВы можете почитать помощь /help или узнать больше о боте /about')
    #----------------повтор для водителей-------------
    elif all_[chat_id].progress == 'select transmission' and all_[chat_id].type_ == 'vodila':
        bot.send_message(chat_id, 'Давайте попробуем еще раз?')
        all_[chat_id].send_transmission_request(message)
    elif all_[chat_id].progress == 'select category' and all_[chat_id].type_ == 'vodila':
        bot.send_message(chat_id, 'Давайте попробуем еще раз?')
        all_[chat_id].send_category_request(all_[chat_id].transmission, chat_id, 'Выберите категории ВУ и нажмите далее')
    elif all_[chat_id].progress == 'send phone' and all_[chat_id].type_ == 'vodila' and \
        message.contact == None and not re.search(phone_pattern, message.text):
        bot.send_message(chat_id, 'Давайте попробуем еще раз?')
        all_[chat_id].send_phone_request(message, all_[chat_id].category)
    elif all_[chat_id].progress == 'send price' and all_[chat_id].type_ == 'vodila':
        bot.send_message(chat_id, 'Давайте попробуем еще раз, отправьте свою цену')
        all_[chat_id].send_price_request(message)
    elif all_[chat_id].progress == 'send final' and all_[chat_id].type_ == 'vodila':
        bot.send_message(chat_id, 'Вы уже зарегистрированы как водитель! \nЕсли хотите вызвать трезвого' \
            ' водителя нажмите /start \nТак же есть помощь /help и рубрика о боте /about')
    
    #--------------------------проверка------------------
    if chat_id in all_:
        #--------------------------первое для заказчиков------------------
        if all_[chat_id].progress == 'send phone' and all_[chat_id].type_ == 'need' and \
            (message.contact != None or (message.text != None and re.search(phone_pattern, message.text))):
            all_[chat_id].update_progress('send location')
            all_[chat_id].send_location_request(message, message.contact.phone_number if message.contact else message.text)
        elif all_[chat_id].progress == 'send location' and all_[chat_id].type_ == 'need' and \
            message.location != None:
            all_[chat_id].update_progress('send location_togo')
            all_[chat_id].send_location_togo_request(message, message.location)
        elif all_[chat_id].progress == 'send location_togo' and all_[chat_id].type_== 'need' and \
            message.location != None:
            all_[chat_id].update_progress('send price')
            all_[chat_id].send_price_request(message, message.location)
        elif all_[chat_id].progress == 'send own price' and all_[chat_id].type_ == 'need':
            all_[chat_id].send_own_price_request(message, all_[chat_id].location_togo)

        #--------------------------первое для водил------------------
        if all_[chat_id].progress == 'send phone' and all_[chat_id].type_ == 'vodila' and \
            (message.contact != None or (message.text != None and re.search(phone_pattern, message.text))):
            all_[chat_id].update_progress('send final')
            phone_number = message.contact.phone_number if message.contact else message.text
            all_[chat_id].send_final_message(message, phone_number)
            print(all_[chat_id])
            insert_into_db_drivers(all_[chat_id])


#--------------------------прослушка Call  сообщений------------------
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    #--------------------------прослушка команд------------------
    if call.data == '/start':
        start_message(call.message)
        return
    elif call.data == '/help':
        help_message(call.message)
        return
    elif call.data == '/faq':
        bot.send_message(call.from_user.id, 'разрабатываются........')
        return
    elif call.data == '/about':
        bot.send_message(call.from_user.id, 'разрабатывается........')
        return
    elif not call.from_user.id in all_:
        other_message(call.message)
        return
    
    #--------------------------прослушка call заказчиков------------------
    user = all_[call.from_user.id]
    if user.type_ == 'need':
        if user.progress == 'select transmission' and (call.data == 'АКПП' or call.data == 'МКПП'):
            user.update_progress('select category')
            user.send_category_request(call.data, call.from_user.id)
        elif user.progress == 'select category' and \
            (call.data == 'A' or call.data == 'B' or call.data == 'C' or \
            call.data == 'D' or call.data == 'E'):
            user.update_progress('send phone')
            user.send_phone_request(call.message, call.data)
        elif user.progress == 'send price' and call.data == 'own':
            user.update_progress('send own price')
        elif user.progress == 'send price' and \
            (int(call.data) == default_price or int(call.data) == default_price+500 or 
            int(call.data) == default_price+1000 or int(call.data) == default_price+1500 or
            int(call.data) == default_price+2000 or int(call.data) == 10000):
            user.update_progress('send final')
            user.send_final_message(call.data, call.from_user.id)
            insert_into_db_clients(user)
    #--------------------------прослушка call водил------------------
    if user.type_ == 'vodila' and user.chat_id == call.from_user.id:
        if user.progress == 'select transmission' and (call.data == 'АКПП' or call.data == 'АКПП + МКПП'):
            user.update_progress('select category')
            user.send_category_request(call.data, call.from_user.id, 'выберите категории ВУ')
        elif user.progress == 'select category' and call.data in categories:
            user.category_select(call.data)
            user.send_category_request(user.transmission, call.from_user.id, 'Может у Вас несколько категорий? По окончании нажмите далее')
        elif user.progress == 'select category' and call.data == 'Далее' and any(x != '' for x in user.category):
            user.update_progress('send phone')
            user.send_phone_request(call.message, user.category)
        elif user.progress == 'select category' and call.data == 'Далее' and all(x == '' for x in user.category):
            user.send_category_request(user.transmission, call.from_user.id, 'Вам НУЖНО выбрать категории ВУ')


bot.polling()
