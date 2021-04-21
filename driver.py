from telebot import types

class driver:
    type_ = 'vodila'
    bot = None
    transmission = None
    category = None
    phone = None
    location = None
    price = None
    chat_id = None
    default_price = None
    username = None
    progress = " "
    transmissions = ['АКПП', 'АКПП + МКПП']
    date = None
    client_id = None
    message_id = None

    def __init__(self, bot, default_price=None, chat_id=None):
        self.bot = bot # устанавливаем имя
        self.default_price = default_price
        self.chat_id = chat_id
        self.category = ["", "", "", "", ""]

    def __str__(self):
        return "из драйвера: type_ - %s, transmission - %s, category - %s, phone - %s, location - %s, price - %s, chat_id - %s, username - %s" % (self.type_, self.transmission, self.category, self.phone, self.location, self.price, self.chat_id, self.username)
    
    def update_progress(self, state):
        self.progress = state

    def send_transmission_request(self, message):
        self.chat_id = message.chat.id
        self.username = message.chat.username
        keyboard = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton('АКПП', callback_data='АКПП')
        item2 = types.InlineKeyboardButton('АКПП + МКПП', callback_data='АКПП + МКПП')
        keyboard.add(item1, item2)
        self.bot.send_message(message.chat.id, 'На чем Вы умеете езить?', reply_markup=keyboard)

    def send_category_request(self, transmission, chat_id, text):
        self.transmission = transmission
        keyboard = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton('A', callback_data='A')
        item2 = types.InlineKeyboardButton('B', callback_data='B')
        item3 = types.InlineKeyboardButton('C', callback_data='C')
        item4 = types.InlineKeyboardButton('D', callback_data='D')
        item5 = types.InlineKeyboardButton('E', callback_data='E')
        item6 = types.InlineKeyboardButton('Далее', callback_data='Далее')
        keyboard.add(item1, item2, item3, item4, item5, item6, row_width=5)
        self.bot.send_message(chat_id, text, reply_markup=keyboard)
    
    def category_select(self, category):
        if category == 'A':
            self.category[0] = 'A'
        elif category == 'B':
            self.category[1] = 'B'
        elif category == 'C':
            self.category[2] = 'C'
        elif category == 'D':
            self.category[3] = 'D'
        elif category == 'E':
            self.category[4] = 'E'
        
    def send_phone_request(self, message, category):
        keyboard0 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True) 
        button_phone = types.KeyboardButton(text='Номер телефона', request_contact=True) 
        keyboard0.add(button_phone) 
        self.bot.send_message(message.chat.id, 'Отправьте номер своего телефона', reply_markup=keyboard0)

    def send_price_request(self, message):
        self.bot.send_message(message.chat.id, 'Сколько хочешь?')

    def send_final_message(self, message, phone):
        self.phone = phone
        self.bot.send_message(message.chat.id, 'Отлично, Вы зарегистрированы!!!', reply_markup=types.ReplyKeyboardRemove(selective=False))