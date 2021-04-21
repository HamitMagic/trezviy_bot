import telebot
from telebot import types
import customer
import driver
import psycopg2
from psycopg2 import Error
import time
import threading
import re
import asyncio

bot = telebot.TeleBot('1618386430:AAF_-TsdAqRYckgTA3rMMopDJWkJa3wRCAI')

categories = ['A', 'B', 'C', 'D', 'E']
default_price = 3000 #тенге
sleep_driver= 3600 #секунды
sleep_time = 300 #секунды
all_ = {}
# drivers = {}
phone_pattern = r'\b\+?[7,8]7(\s*\d{2}\s*\d{3}\s*\d{2}\s*\d{2})\b'

#-------------------------------БД-------------------------------------------
conn = psycopg2.connect(dbname='postgres', user='postgres', password='HamiT181', host="localhost")
cursor=conn.cursor()

def select_from_db_drivers(cursor):
    cursor.execute('SELECT * FROM public.drivers')
    records = cursor.fetchall()

def select_from_db_clients(cursor):
    cursor.execute('SELECT * FROM public.clients')
    records = cursor.fetchall()

def insert_into_db_clients(user):
    DB = f"""INSERT INTO public.clients(chat_id, category, transmission, phone, username, price, location, location_togo)
    VALUES ({user.chat_id}, '{user.category}', '{user.transmission}', {user.phone}, '{user.username}', {user.price},
    ARRAY{[user.location.longitude, user.location.latitude]}, ARRAY{[user.location_togo.longitude, user.location_togo.latitude]})"""
    cursor.execute(DB)
    conn.commit()

def insert_into_db_drivers(user):
    cursor.execute(f"SELECT chat_id FROM public.drivers WHERE chat_id = {user.chat_id}")
    drivers = cursor.fetchall()
    if len(drivers) > 0:
        DB = f"""UPDATE public.drivers
        SET category=ARRAY{user.category}, phone={user.phone}, username='{user.username}', transmission='{user.transmission}', ready=true
        WHERE chat_id = {user.chat_id}"""
    else:
        DB = f"""INSERT INTO public.drivers(chat_id, category, transmission, phone, username, ready)
        VALUES ({user.chat_id}, ARRAY{user.category}, '{user.transmission}', {user.phone}, '{user.username}', true)"""
    cursor.execute(DB)
    conn.commit()

#--------------------------основное сообщение------------------
def other_message(message):
    keyboard0 = types.ReplyKeyboardMarkup(False, True)
    keyboard0.row('Мне нужен трезвый водитель!', 'Я трезвый водитель! (регистрация)')
    bot.send_message(message.chat.id, 'Упс, что-то пошло не так. давайте начнем с начала... ;)', reply_markup=keyboard0)

def correct_phone(message):
    if message.contact != None:
        phone = f'{message.contact.phone_number[-10:]}'
    else:
        phone = f'{message.text[-10:]}'
    return phone

#------------------------------------------------------------------
def wait_for_driver (driver_id):
    time.sleep(sleep_driver)
    cursor.execute(f"UPDATE public.drivers SET ready = true WHERE chat_id = '{driver_id}'")
    conn.commit()
    
async def send_contacts (client_id):
    await asyncio.sleep(sleep_time)
    driver_id = all_[client_id].drivers_id
    if driver_id == None:
        bot.send_message(client_id, 'Извините, но все водители в данный момент заняты, либо далеко.\n' \
            'Воспользуйтесь нашей услугой позже, спасибо')
        return
    cursor.execute(f"""SELECT phone, username FROM public.drivers WHERE chat_id = '{driver_id}'""")
    driver = cursor.fetchone()
    bot.send_message(client_id, f'телефон водителя - +7{driver[0]} \nНе переживайте, он скоро приедет 😀' \
        '\nСпасибо что воспользовались нашей услугой. Порекомендуйте меня (бота) другу')
    bot.send_message(driver_id, f'телефон автовладельца - +7{all_[client_id].phone}')
    cursor.execute(f"UPDATE public.drivers SET ready = false WHERE chat_id = '{driver_id}'")
    conn.commit()
    thread=threading.Thread(target=wait_for_driver, args=[driver_id])
    thread.start()
    # drivers = []
    all_[client_id] = None
    del all_[client_id]

def get_all_drivers (chat_id):
    if all_[chat_id].transmission == "МКПП":
        cursor.execute(f"""SELECT chat_id
	    FROM public.drivers
	    WHERE transmission = '{'АКПП + МКПП'}' and '{all_[chat_id].category}' = ANY(category) and ready = true""")
    else:
        cursor.execute(f"""SELECT chat_id
	    FROM public.drivers
	    WHERE '{all_[chat_id].category}' = ANY(category) and ready = true""")
    all_drivers = cursor.fetchall()
    return all_drivers

def send_msg_to_drivers(all_drivers, chat_id):
    for el in all_drivers:
        if el[0] not in all_:
            bot.send_message(el[0], 'Есть заказ на перегон машины от:')
            bot.send_location(el[0], all_[chat_id].location.latitude, all_[chat_id].location.longitude)
            bot.send_message(el[0], 'и до места:')
            bot.send_location(el[0], all_[chat_id].location_togo.latitude, all_[chat_id].location_togo.longitude)
            sended_message = bot.send_message(el[0], f'Готовы заплатить {all_[chat_id].price}.' \
                f'Если Вы согласны, отправьте свое местоположение ответом на это сообщение в течении {sleep_time//60} минут')
            drivers = {}
            drivers[el[0]] = driver.driver(bot, chat_id=el[0])
            drivers[el[0]].message_id = sended_message.message_id
            drivers[el[0]].progress = 'sended order'
            drivers[el[0]].client_id = chat_id
    all_[chat_id].offered_drivers = drivers
    asyncio.run(send_contacts(chat_id))

def findDriver(chat_id, message_id = None):
    if message_id == None:
        return None
    for key1, client in all_.items():
        if not client.offered_drivers:
            continue
        for key2, driver in client.offered_drivers.items():
            if driver.chat_id == chat_id and driver.message_id == message_id:
                return driver
    return None

#--------------------------основные команды------------------
@bot.message_handler(commands=['start'])
def start_message(message):
    if message.chat.id in all_:
        all_[message.chat.id] = None
        del all_[message.chat.id]
    keyboard0 = types.ReplyKeyboardMarkup(False, True)
    keyboard0.row('Мне нужен трезвый водитель!', 'Я трезвый водитель! (регистрация)')
    bot.send_message(message.chat.id, 'Вам нужен трезвый водитель? Или вы сами трезвый водитель?', reply_markup=keyboard0)

@bot.message_handler(commands=['start_work'])
def order_message(message):
    cursor.execute(f"UPDATE public.drivers SET ready = true WHERE chat_id = {message.chat.id}")
    conn.commit()

@bot.message_handler(commands=['stop_work'])
def unorder_message(message):
    cursor.execute(f"UPDATE public.drivers SET ready = false WHERE chat_id = {message.chat.id}")
    conn.commit()

@bot.message_handler(commands=['faq'])
def faq_message(message):
    bot.send_message(message.chat.id, 'разрабатываются........')

@bot.message_handler(commands=['about'])
def about_message(message):
    bot.send_message(message.chat.id, 'разрабатывется....')

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
    chat_id = message.chat.id
    replied_driver = None
    #--------------------------первое для водил на заказ------------------
    try:
        replied_driver = findDriver(chat_id, message.reply_to_message.id)
        if replied_driver != None and chat_id not in all_:
            if replied_driver.progress == 'sended order' and message.location != None:
                try:
                    if replied_driver != None:
                        replied_driver.location = message.location
                        bot.send_message(chat_id, f'Понял Вас, ожидайте приглашения! \n Если менее чем через {sleep_time//60}' \
                            'минут не придет сообщение, значит выбрали другого водителя')
                        client_id = replied_driver.client_id
                        distance = (all_[client_id].location.latitude - replied_driver.location.latitude)**2 + \
                            (all_[client_id].location.longitude - replied_driver.location.longitude)**2
                        all_[client_id].distance = distance if distance <= all_[client_id].distance else all_[client_id].distance
                        all_[client_id].drivers_id = chat_id if distance <= all_[client_id].distance else all_[client_id].drivers_id
                except:
                    bot.send_message(chat_id, 'отправьте свое местоположение ОТВЕТОМ на сообщение')
        else:
            raise Exception()
    except:
        if chat_id in all_:
            #--------------------------повтор для заказчиков--------------
            if all_[chat_id].progress == 'select transmission' and all_[chat_id].type_ == 'need':
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
                    thread=threading.Thread(target=send_msg_to_drivers, args=(get_all_drivers(chat_id), chat_id))
                    thread.start()
                else:
                    all_[chat_id].send_own_price_request(message, all_[chat_id].location_togo)
            elif all_[chat_id].progress == 'send own price' and all_[chat_id].type_ == 'need':
                all_[chat_id].send_own_price_request(message, all_[chat_id].location_togo)
            elif all_[chat_id].progress == 'send final' and all_[chat_id].type_ == 'need':
                bot.send_message(chat_id, 'Ищу водителя! \nЕсли прошло много времени попробуйте еще раз вызвать через /start' \
                    '\nВы можете почитать помощь /help или узнать больше о боте /about')
            
            #---------------------------повтор для водителей---------------
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
            
            #--------------------------первое для заказчиков------------------
            if all_[chat_id].progress == 'send phone' and all_[chat_id].type_ == 'need' and \
                (message.contact != None or (message.text != None and re.search(phone_pattern, message.text))):
                all_[chat_id].update_progress('send location')
                all_[chat_id].send_location_request(message, correct_phone(message))
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
            elif all_[chat_id].progress == 'send phone' and all_[chat_id].type_ == 'vodila' and \
                (message.contact != None or (message.text != None and re.search(phone_pattern, message.text))):
                all_[chat_id].update_progress('send final')
                all_[chat_id].send_final_message(message, correct_phone(message))
                insert_into_db_drivers(all_[chat_id])

        #--------------------------первое сообщение и other msg------------------
        if chat_id not in all_:
            if message.text == 'Мне нужен трезвый водитель!':
                all_[chat_id] = customer.customer(bot, default_price)
                all_[chat_id].update_progress('select transmission')
                all_[chat_id].send_transmission_request(message)
            elif message.text == 'Я трезвый водитель! (регистрация)':
                all_[chat_id] = driver.driver(bot,default_price)
                all_[chat_id].update_progress('select transmission')
                all_[chat_id].send_transmission_request(message)
            elif not chat_id in all_ and replied_driver == None and all_[chat_id].progress != 'sended order':
                other_message(message)


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
        faq_message(call.message)
        return
    elif call.data == '/about':
        about_message(call.message)
        return
    elif call.from_user.id not in all_ and findDriver(call.from_user.id) == None:
        other_message(call.message)
        return
    
    #--------------------------прослушка call заказчиков------------------
    if call.from_user.id in all_:
        user = all_[call.from_user.id]
        if user.type_ == 'need' and user.chat_id == call.from_user.id:
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
                thread=threading.Thread(target=send_msg_to_drivers, args=(get_all_drivers(user.chat_id), user.chat_id))
                thread.start()

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
