import telebot
import buttons
import database
from telebot.types import ReplyKeyboardRemove
from geopy.geocoders import Nominatim


# Создаем подключение к боту
bot = telebot.TeleBot('5899210772:AAFYWIzpfutI2obBL2UevixJOVS2OUyNv44')
geolocator = Nominatim(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36')

# Словарь для временных данных
users = {}


#database.add_product_to_sklad('Картошка', 55, 7000, 'Супер самый лучший', 'https://www.google.com/imgres?imgurl=https%3A%2F%2Fwww.applesfromny.com%2Fwp-content%2Fuploads%2F2020%2F05%2F20Ounce_NYAS-Apples2.png&tbnid=ktcxvF5LaXyVXM&vet=12ahUKEwiF4uu0oZP_AhUJwyoKHUtdC-AQMygBegUIARDDAQ..i&imgrefurl=https%3A%2F%2Fwww.applesfromny.com%2Fvarieties%2F&docid=C0ERe9pIHvHfgM&w=2400&h=1889&q=apples&ved=2ahUKEwiF4uu0oZP_AhUJwyoKHUtdC-AQMygBegUIARDDAQ')


# обработка команды старт
@bot.message_handler(commands=['start'])
def start_message(message):
    # Получить телеграм айди
    user_id = message.from_user.id
    print(user_id)
    # Проверка пользователя
    checker = database.check_user(user_id)

    # если пользователь есть в базе
    if checker:
        # Получим актуальный список продуктов
        products = database.get_pr_name_id()

        # отправим сообщение с меню
        bot.send_message(user_id, 'Привет', reply_markup=ReplyKeyboardRemove())
        bot.send_message(user_id,
                         'Выберите пункт меню',
                         reply_markup=buttons.main_menu_kb(products))

    # Если нет пользователя в базе
    elif not checker:
        bot.send_message(user_id, 'привет\nотправь свое имя')

        # переход на этап получения имени
        bot.register_next_step_handler(message, get_name)


# Этап получения имени
def get_name(message):
    # Сохраним телеграмм айди в переменную
    user_id = message.from_user.id

    # Сохраним имя в переменную
    username = message.text

    # Отправим ответ
    bot.send_message(user_id,
                     'Отправьте теперь свой номер телефона',
                     reply_markup=buttons.phone_number_kb())

    # переход на этап получения номера телефона
    bot.register_next_step_handler(message, get_number, username)


# Этап получения номера телефона
def get_number(message, name):
    # Сохраним телеграмм айди в переменную
    user_id = message.from_user.id

    # проверяем отправил ли пользователь контакт
    if message.contact:
        # Сохраним контакт
        phone_number = message.contact.phone_number

        # сохраняем его в базе
        database.register_user(user_id, name, phone_number, 'Not yet')
        bot.send_message(user_id, 'Вы успешно зарегистрированы', reply_markup=ReplyKeyboardRemove())

        # И открываем меню
        products = database.get_pr_name_id()
        bot.send_message(user_id,
                         'Выберите пункт меню',
                         reply_markup=buttons.main_menu_kb(products))

    # А если не отправил контакт то еще раз попросим отправить
    elif not message.contact:
        bot.send_message(user_id,
                         'отправьте контакт используя кнопку',
                         reply_markup=buttons.phone_number_kb())

        # Обратно на этап получения номера телефона
        bot.register_next_step_handler(message, get_number, name)


# Обработчик выбора количества
@bot.callback_query_handler(lambda call: call.data in ['increment', 'decrement', 'to_cart', 'back'])
def get_user_product_count(call):
    # Сохраним айди пользователя
    user_id = call.message.chat.id

    # Если пользователь нажал на +
    if call.data == 'increment':
        actual_count = users[user_id]['pr_count']

        users[user_id]['pr_count'] += 1
        # Меняем значение кнопки
        bot.edit_message_reply_markup(chat_id=user_id,
                                      message_id=call.message.message_id,
                                      reply_markup=buttons.choose_product_count('increment', actual_count))

    # decrement
    # Если пользователь нажал на -
    elif call.data == 'decrement':
        actual_count = users[user_id]['pr_count']

        users[user_id]['pr_count'] -= 1
        # Меняем значение кнопки
        bot.edit_message_reply_markup(chat_id=user_id,
                                      message_id=call.message.message_id,
                                      reply_markup=buttons.choose_product_count('decrement', actual_count))

    # back
    # Если пользователь нажал 'назад'
    elif call.data == 'back':
        # Обнуляем
#        users[user_id]['pr_count'] = 0
        # Получаем меню
        products = database.get_pr_name_id()
        # меняем на меню
        bot.edit_message_text('Выберите пункт меню',
                              user_id,
                              call.message.message_id,
                              reply_markup=buttons.main_menu_kb(products))

    # Если нажал Добавить в корзину
    elif call.data == 'to_cart':
        # Получаем данные
        product_count = users[user_id]['pr_count']
        user_product = users[user_id]['pr_name']

        # Добавляем в базу(корзина пользователя)
        database.add_product_to_cart(user_id, user_product, product_count)

        # Получаем обратно меню
        products = database.get_pr_name_id()
        # меняем на меню
        bot.edit_message_text('Продукт добавлен в корзину\nЧто-нибудь еще?',
                              user_id,
                              call.message.message_id,
                              reply_markup=buttons.main_menu_kb(products))


# Обработчик кнопок (Оформить заказ, Корзина)
@bot.callback_query_handler(lambda call: call.data in ['order', 'cart', 'clear_cart'])
def main_menu_handle(call):
    user_id = call.message.chat.id
    message_id = call.message.message_id

    # Если нажал на кнопку: Оформить заказ
    if call.data == 'order':
        # Удалим сообщение с верхними кнопками
        bot.delete_message(user_id, message_id)

        # отправим текст на "Отправьте локацию"
        bot.send_message(user_id,
                         'Отправьте локацию',
                         reply_markup=buttons.location_kb())

        # Переход на этап сохранение локации
        bot.register_next_step_handler(call.message, get_location)
# Если нажал на кнопку Корзина
    elif call.data =='cart':
        user_cart = database.get_exact_user_cart(user_id)
        # Формируем сообщение со всеми данными
        full_text = 'Ваша корзина:\n\n'
        total_amount = 0
        for i in user_cart:
            full_text += f'{i[0]} x {i[1]} = {i[2]}\n'
            total_amount += i[2]
        # Итог и Адрес
        full_text += f'\nИтог: {total_amount}'
        # отправляем ответ пользователю
        bot.edit_message_text(full_text, user_id, message_id,
                              reply_markup=buttons.get_cart_kb())

    #  Если нажал очистить корзину
    elif call.data =='clear_cart':
        # вызов функции очистки корзины
        database.delete_product_from_cart(user_id)
    #  отправим ответ
        bot.edit_message_text('Ваша корзина очищена',user_id, message_id,
                              reply_markup=buttons.main_menu_kb(database.get_pr_name_id()))

# Функция сохранения локации пользователя
def get_location(message):
    user_id = message.from_user.id
    # отправил ли локацию
    if message.location:
        # Сохранить в переменные координаты
        latitude = message.location.latitude
        longitude = message.location.longitude

        # Преобразуем координаты на нормальный адрес
        address = 'geolocator.reverse((latitude, longitude)).address'

        # Запрос подтверждения заказа
        # получим корзину пользователя
        user_cart = database.get_exact_user_cart(user_id)
        # Формируем сообщение со всеми данными
        full_text = 'Ваш заказ\n\n'
        user_info = database.get_user_number_name(user_id)
        full_text += f'Имя: {user_info[0]}\nНомер телефона: {user_info[1]}\n\n'
        total_amount = 0
        for i in user_cart:
            full_text += f'{i[0]} x {i[1]} = {i[2]}\n'
            total_amount +=i[2]
        # Итог и Адрес
        full_text += f'\nИтог: {total_amount}\nАдрес: {address}'

        bot.send_message(user_id, full_text, reply_markup=buttons.get_accept_kb())
        # Переход на этап подтверждение
        bot.register_next_step_handler(message, get_accept, address, full_text)


# функция сохранения статуса заказа
def get_accept(message, address, full_text):
    user_id = message.from_user.id
    message_id = message.id
    user_answer = message.text
    products = database.get_pr_name_id()

    if user_answer == 'Подтвердить':
        #Clear recycle
        database.delete_product_from_cart(user_id)

        #Send message to Admin about
        bot.send_message(117657882, full_text.replace('Ваш','Новый'))
        bot.send_message(user_id, 'Ваш заказ обрабатывается\nдождитесь звонка оператора'
                         , reply_markup=ReplyKeyboardRemove())
        bot.send_message(user_id,'_', reply_markup=buttons.main_menu_kb(products))

    elif user_answer == 'Отменить':

        bot.send_message(user_id, 'Заказ отменен', reply_markup=ReplyKeyboardRemove())
        bot.send_message(user_id, '_', reply_markup=buttons.main_menu_kb(products))



# Обработчик выбора товара
@bot.callback_query_handler(lambda call: int(call.data) in database.get_pr_id())
def get_user_product(call):
    # Сохраним айди пользователя
    user_id = call.message.chat.id

    # Сохраним продукт во временный словарь
    # call.data - значение нажатой кнопки(инлайн)
    users[user_id] = {'pr_name': call.data, 'pr_count': 1}

    # Сохраним айди сообщения
    message_id = call.message.message_id

    # Поменять кнопки на выбор количества
    bot.edit_message_text('Выберите количество',
                          chat_id=user_id, message_id=message_id,
                          reply_markup=buttons.choose_product_count())


# Запуск
bot.polling()


#        bot.delete_message(user_id, message_id)