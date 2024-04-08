import telebot
from telebot import types
from datetime import datetime, timedelta


# Импортируем sqlite3 для работы с базой данных
import sqlite3

user_data = {}

# Инициализация бота
bot = telebot.TeleBot("6955334520:AAHmzsW94i4x442at_XKUhynxNt7kZfe3L0")

# Глобальная переменная для хранения состояния меню
show_menu = False


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id,
                     'Привет! Я корпоративный телеграм-бот. Для получения помощи используй команду /help')


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help(message):
    help_text = "Я могу помочь тебе со следующими задачами:\n\n" \
                "/tasks - посмотреть список задач\n" \
                "/events - посмотреть календарь событий\n" \
                "/contacts - найти контакты сотрудников\n" \
                "/faq - получить ответы на часто задаваемые вопросы\n"\
                "/add_task - добавить задание"
    bot.send_message(message.chat.id, help_text)


# Обработчик команды /events
@bot.message_handler(commands=['events'])
def events(message):
    # Получаем список событий из базы данных
    events = get_events()

    if events:
        # Удаляем прошедшие события
        remove_expired_events()

        # Отправляем пользователю сообщение с оставшимися событиями
        remaining_events = get_events()
        if remaining_events:
            bot.send_message(message.chat.id, "Список предстоящих событий:")
            for event in remaining_events:
                event_info = f"📅 *{event[1]}*\n\n_{event[2]}_\n\n🕒 *Дата и время:* {event[3]}\n📍 *Местоположение:* {event[4]}"
                bot.send_message(message.chat.id, event_info, parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "К сожалению, нет предстоящих событий.")
    else:
        bot.send_message(message.chat.id, "К сожалению, нет предстоящих событий.")

# Функция для получения списка событий из базы данных
def get_events():
    try:
        # Подключение к базе данных
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()

        # Запрос к базе данных для получения событий
        cursor.execute("SELECT * FROM events")
        events = cursor.fetchall()

        # Закрытие соединения с базой данных
        cursor.close()
        connection.close()

        return events
    except Exception as e:
        print(f"Ошибка при получении списка событий: {e}")
        return None

# Функция для удаления прошедших событий из базы данных
def remove_expired_events():
    try:
        # Подключение к базе данных
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()

        # Определение времени, прошедшего на один день
        one_day_ago = datetime.now() - timedelta(days=1)

        # Удаление событий, у которых date_time прошел на один день или более
        cursor.execute("DELETE FROM events WHERE date_time < ?", (one_day_ago,))
        connection.commit()

        # Закрытие соединения с базой данных
        cursor.close()
        connection.close()

    except Exception as e:
        print(f"Ошибка при удалении прошедших событий: {e}")

@bot.message_handler(commands=['contacts'])
def contacts(message):
    # Отправляем сообщение с запросом имени и фамилии сотрудника
    bot.send_message(message.chat.id, "Введите имя и фамилию сотрудника (например, Иван Иванов):")

    # Регистрируем следующий шаг обработки сообщения
    bot.register_next_step_handler(message, find_contact)

# Функция для поиска контактов сотрудников по имени и фамилии
def find_contact(message):
    # Получаем имя и фамилию сотрудника из сообщения пользователя
    name = message.text.strip()

    # Подключаемся к базе данных
    connection = sqlite3.connect("tg_bot.db")
    cursor = connection.cursor()

    # Ищем контакты сотрудника по имени и фамилии в таблице Контакты
    cursor.execute("SELECT first_name, last_name, email, phone FROM contacts WHERE first_name || ' ' || last_name LIKE ?", ('%' + name + '%',))
    contacts_entries = cursor.fetchall()

    # Формируем ответ на запрос контактов
    if contacts_entries:
        response = "Найденные контакты сотрудника:\n\n"
        for first_name, last_name, email, phone in contacts_entries:
            response += f"Имя: {first_name} {last_name}\nEmail: {email}\nТелефон: {phone}\n\n"
    else:
        response = "Контакты сотрудника не найдены."

    # Отправляем ответ пользователю
    bot.send_message(message.chat.id, response)

    # Закрываем соединение с базой данных
    cursor.close()
    connection.close()




@bot.message_handler(commands=['faq'])
def faq(message):
    # Подключаемся к базе данных
    connection = sqlite3.connect("tg_bot.db")
    cursor = connection.cursor()

    # Получаем ответы на часто задаваемые вопросы из таблицы FAQ
    cursor.execute("SELECT question, answer FROM FAQ")
    faq_entries = cursor.fetchall()

    # Формируем ответ на команду /faq
    response = "Часто задаваемые вопросы и ответы:\n\n"
    for question, answer in faq_entries:
        response += f"Вопрос: {question}\nОтвет: {answer}\n\n"

    # Отправляем ответ пользователю
    bot.send_message(message.chat.id, response)

    # Закрываем соединение с базой данных
    cursor.close()
    connection.close()



# Функция для получения списка пользователей из базы данных
def get_users():
    connection = sqlite3.connect("tg_bot.db")
    cursor = connection.cursor()
    cursor.execute("SELECT id, username FROM users")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return users


# Обработчик команды /add_task
@bot.message_handler(commands=["add_task"])
def add_task(message):
    # Получаем список пользователей из базы данных
    users = get_users()

    # Сохраняем список пользователей для последующего использования
    user_data[message.chat.id] = {'users': users}

    # Запрашиваем у пользователя выбор пользователя
    bot.send_message(message.chat.id, "Выберите пользователя из списка:")
    show_users(message)


# Функция для отображения списка пользователей
def show_users(message):
    users = user_data[message.chat.id]['users']
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for user_id, username in users:
        button_text = f"{username} (user_id: {user_id})"
        markup.add(types.KeyboardButton(button_text))
    bot.send_message(message.chat.id, "Выберите пользователя из списка:", reply_markup=markup)


# Регистрируем обработчик нажатия на кнопку выбора пользователя
@bot.message_handler(func=lambda message: True)
def handle_user_selection(message):
    users = user_data[message.chat.id]['users']
    for user_id, username in users:
        button_text = f"{username} (user_id: {user_id})"
        if message.text == button_text:
            user_data[message.chat.id]['user_id'] = user_id
            bot.send_message(message.chat.id, f"Выбран пользователь: {username} (user_id: {user_id})",
                             reply_markup=types.ReplyKeyboardRemove())
            ask_title(message)


def ask_title(message):
    bot.send_message(message.chat.id, "Введите название задачи:")
    bot.register_next_step_handler(message, ask_description)

def ask_description(message):
    user_data[message.chat.id]['title'] = message.text
    bot.send_message(message.chat.id, "Введите описание задачи:")
    bot.register_next_step_handler(message, ask_deadline)

# Функция для запроса срока выполнения задачи у пользователя
def ask_deadline(message):
    user_data[message.chat.id]['description'] = message.text
    bot.send_message(message.chat.id, "Введите срок выполнения задачи (YYYY-MM-DD):")
    bot.register_next_step_handler(message, ask_status)

# Функция для запроса статуса задачи у пользователя
def ask_status(message):
    try:
        task_data = user_data[message.chat.id]

        # Получение введенного пользователем срока выполнения задачи
        task_data['deadline'] = message.text

        # Список возможных статусов задачи
        statuses = ["В процессе", "Выполнена", "Отложена", "Отменена", "Ожидает подтверждения", "На утверждении"]

        # Создание клавиатуры с кнопками для каждого статуса
        markup = types.ReplyKeyboardMarkup(row_width=1)
        for status in statuses:
            markup.add(types.KeyboardButton(status))

        # Отправка сообщения с запросом выбора статуса
        bot.send_message(message.chat.id, "Выберите статус задачи из списка:", reply_markup=markup)
        bot.register_next_step_handler(message, save_task)

    except Exception as e:
        # В случае возникновения ошибки, уведомляем пользователя
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")



# Функция для сохранения задачи в базе данных
def save_task(message):
    try:
        task_data = user_data[message.chat.id]

        # Подключение к базе данных
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()

        # Добавление новой задачи в таблицу tasks
        cursor.execute("INSERT INTO tasks (user_id, title, description, deadline, status) VALUES (?, ?, ?, ?, ?)",
                       (task_data['user_id'], task_data['title'], task_data['description'], task_data['deadline'], message.text))
        connection.commit()

        # Закрытие соединения с базой данных
        cursor.close()
        connection.close()

        # Уведомление пользователя об успешном добавлении задачи
        bot.send_message(message.chat.id, "Задача успешно добавлена!", reply_markup=types.ReplyKeyboardRemove())

    except Exception as e:
        # В случае возникновения ошибки, уведомляем пользователя
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")



# Обработчик команды /menu
@bot.message_handler(commands=['menu'])
def menu(message):
    global show_menu
    show_menu = True
    send_menu(message.chat.id)


# Функция для отправки меню
def send_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(row_width=2)
    tasks_button = types.KeyboardButton('/tasks')
    events_button = types.KeyboardButton('/events')
    contacts_button = types.KeyboardButton('/contacts')
    faq_button = types.KeyboardButton('/faq')
    markup.add(tasks_button, events_button, contacts_button, faq_button)

    bot.send_message(chat_id, "Выберите нужную функцию:", reply_markup=markup)


# Обработчик нажатия на кнопку "Меню"
@bot.message_handler(func=lambda message: message.text == 'Меню')
def handle_menu(message):
    send_menu(message.chat.id)


# Удаляем клавиатуру после выбора функции
@bot.message_handler(func=lambda message: True)
def hide_menu(message):
    global show_menu
    if show_menu:
        bot.send_message(message.chat.id, "Чтобы вернуться к меню, используйте команду /menu",
                         reply_markup=types.ReplyKeyboardRemove())
        show_menu = False









bot.polling(none_stop=True)
