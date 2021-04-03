from telebot import types

class customer:
    type_ = 'need'
    bot = None
    transmission = None
    category = None
    phone = None
    location = None
    location_togo = None
    price = None
    chat_id = None
    default_price = None
    username = None
    progress = ''

    def __init__(self, bot, default_price):
        self.bot = bot # устанавливаем имя
        self.default_price = default_price

    def __str__(self):
        return "из заказчика: type_ - %s, transmission - %s, category - %s, phone - %s, location - %s, location_togo - %s, price - %s, chat_id - %s, username - %s" % (self.type_, self.transmission, self.category, self.phone, self.location, self.location_togo, self.price, self.chat_id, self.username)

    def update_progress(self, state):
        self.progress = state

    def send_transmission_request(self, message):
        self.chat_id = message.chat.id
        self.username = message.chat.username
        keyboard = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton('АКПП', callback_data='АКПП')
        item2 = types.InlineKeyboardButton('МКПП', callback_data='МКПП')
        keyboard.add(item1, item2)
        self.bot.send_message(message.chat.id, 'Какая у вас коробка передач?', reply_markup=keyboard)

    def send_category_request(self, transmission, chat_id):
        self.transmission = transmission
        keyboard = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton('A', callback_data='A')
        item2 = types.InlineKeyboardButton('B', callback_data='B')
        item3 = types.InlineKeyboardButton('C', callback_data='C')
        item4 = types.InlineKeyboardButton('D', callback_data='D')
        item5 = types.InlineKeyboardButton('E', callback_data='E')
        keyboard.add(item1, item2, item3, item4, item5, row_width=5)
        self.bot.send_message(chat_id, 'К какой категории относится Ваш автомобиль', reply_markup=keyboard)

    def send_phone_request(self, message, category):
        self.category = category
        keyboard0 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=False) 
        button_phone = types.KeyboardButton(text='Отправить номер телефона', request_contact=True) 
        keyboard0.add(button_phone) 
        self.bot.send_message(message.chat.id, 'Отправьте номер своего телефона', reply_markup=keyboard0)

    def send_location_request(self, message, phone):
        self.phone = phone
        keyboard0 = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=False)
        button_geo = types.KeyboardButton(text='Отправить местоположение', request_location=True)
        keyboard0.add(button_geo) 
        self.bot.send_message(message.chat.id, 'Укажите свое местоположение', reply_markup=keyboard0)

    def send_location_togo_request(self, message, location):
        rk = types.ReplyKeyboardRemove(selective=False)
        self.location = location
        self.bot.send_message(message.chat.id, 'Куда поедем? Отправьте геопозицию пожалуйста', reply_markup=rk)

    def send_price_request(self, message, location_togo):
        self.location_togo = location_togo
        keyboard = types.InlineKeyboardMarkup()
        item1 = types.InlineKeyboardButton(self.default_price, callback_data=self.default_price)
        item2 = types.InlineKeyboardButton(self.default_price+500, callback_data=self.default_price+500)
        item3 = types.InlineKeyboardButton(self.default_price+1000, callback_data=self.default_price+1000)
        item4 = types.InlineKeyboardButton(self.default_price+1500, callback_data=self.default_price+1500)
        item5 = types.InlineKeyboardButton(self.default_price+2000, callback_data=self.default_price+2000)
        item6 = types.InlineKeyboardButton("10000", callback_data=10000)
        item7 = types.InlineKeyboardButton(f"Своя сумма, но не меньше {self.default_price}", callback_data='own')
        keyboard.add(item1, item2, item3, item4, item5, item6, item7, row_width=3)
        self.bot.send_message(message.chat.id, 'Укажите сумму', reply_markup=keyboard)

    def send_own_price_request(self, message, location_togo):
        if message.text.isdigit() and int(message.text) >= self.default_price:
            self.send_final_message(message.text, message.chat.id)
        elif message.text.isdigit() and int(message.text) < self.default_price:
            self.send_reprice_message(message, self.location_togo)
        else:
            self.bot.send_message(message.chat.id, f'Выберите из предложенного, либо укажите цифрами, но не менее {self.default_price}')
            self.send_price_request(message, self.location_togo)

    def send_reprice_message(self, message, location_togo):
        self.bot.send_message(message.chat.id, f'Слишком мало, укажите цену больше {self.default_price}')
        self.send_price_request(message, self.location_togo)

    def send_final_message(self, text, chat_id):
        self.price = int(text)
        self.update_progress('send final')
        self.bot.send_message(chat_id, 'В обработке!!!')