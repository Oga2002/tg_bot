import telebot
from telebot import types
from datetime import datetime, timedelta
import time


# Импортируем sqlite3 для работы с базой данных
import sqlite3


role_commands = {
    "сотрудник": [
        ("/tasks", "Посмотреть список задач"),
        ("/events", "Посмотреть календарь событий"),
        ("/contacts", "Найти контакты сотрудников"),
        ("/faq", "Получить ответы на часто задаваемые вопросы")
    ],
    "руководитель": [
        ("/tasks", "Посмотреть список задач"),
        ("/events", "Посмотреть календарь событий"),
        ("/contacts", "Найти контакты сотрудников"),
        ("/reports", "Получить отчеты о ходе выполнения задач")
    ],
    "администратор": [
        ("/tasks", "Посмотреть список задач"),
        ("/events", "Посмотреть календарь событий"),
        ("/contacts", "Найти контакты сотрудников"),
        ("/users", "Управлять пользователями"),
        ("/settings", "Настроить бота")
    ]
}

# Инициализация бота
bot = telebot.TeleBot("6955334520:AAHmzsW94i4x442at_XKUhynxNt7kZfe3L0")



# Словарь для хранения идентификаторов пользователей и их ролей
user_data = {}
user_role = {}
old_tasks = []

# Функция для отображения меню команд для сотрудника
def show_employee_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton("/help - Получить справку"),
        types.KeyboardButton("/tasks - Просмотреть задачи"),
        types.KeyboardButton("/faq - Часто задаваемые вопросы"),
        types.KeyboardButton("/contacts - Контактная информация"),
        types.KeyboardButton("/events - Просмотреть события"),
        types.KeyboardButton("/out - Выйти из учётной записи.")
    ]
    keyboard.add(*buttons)
    bot.send_message(chat_id, "Доступные команды для сотрудника:", reply_markup=keyboard)

# Функция для отображения меню команд для руководителя
def show_manager_menu(chat_id):
    keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    buttons = [
        types.KeyboardButton("/help - Получить справку"),
        types.KeyboardButton("/tasks - Просмотреть задачи"),
        types.KeyboardButton("/add_task - Создать новую задачу"),
        types.KeyboardButton("/faq - Часто задаваемые вопросы"),
        types.KeyboardButton("/contacts - Контактная информация"),
        types.KeyboardButton("/events - Просмотреть события"),
        types.KeyboardButton("/add_event - Создать новое событие"),
        types.KeyboardButton("/out - Выйти из учётной записи")
    ]
    keyboard.add(*buttons)
    bot.send_message(chat_id, "Доступные команды для руководителя:", reply_markup=keyboard)


# Обработчик команды /out
@bot.message_handler(commands=['out'])
def out(message):
    global user_role
    user_role = {}
    bot.send_message(message.chat.id, "Вы вышли ")

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    if not user_role:
        bot.send_message(message.chat.id, "Введите ваше имя пользователя (username):")
        bot.register_next_step_handler(message, authenticate_username)
    else:
        bot.send_message(message.chat.id, "Вы уже авторизованы")
        if user_role['role'] == "сотрудник":
            commands_menu = "Доступные команды:\n"
            commands_menu += "/help - Получить справку\n"
            commands_menu += "/tasks - Просмотреть задачи\n"
            commands_menu += "/faq - Часто задаваемые вопросы\n"
            commands_menu += "/contacts - Контактная информация\n"
            commands_menu += "/events - Просмотреть события\n"
            bot.send_message(message.chat.id, commands_menu)
        elif user_role['role'] == "руководитель":
            commands_menu = "Доступные команды:\n"
            commands_menu += "/help - Получить справку\n"
            commands_menu += "/tasks - Просмотреть задачи\n"
            commands_menu += "/faq - Часто задаваемые вопросы\n"
            commands_menu += "/contacts - Контактная информация\n"
            commands_menu += "/events - Просмотреть события\n"
            bot.send_message(message.chat.id, commands_menu)

# Функция для проверки аутентификации пользователя
def authenticate_user(username, password):
    try:
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()
        cursor.execute("SELECT id, first_name, last_name, role FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user  # Возвращает кортеж (id, first_name, last_name, role) или None, если пользователь не найден
    except Exception as e:
        print(f"Ошибка аутентификации: {e}")
        return None

# Обработчик для аутентификации имени пользователя
def authenticate_username(message):
    username = message.text.strip()
    bot.send_message(message.chat.id, "Введите ваш пароль:")
    bot.register_next_step_handler(message, lambda msg: authenticate_password(msg, username))

# Функция для успешной аутентификации
def successful_authentication(message, user):
    global user_role  # Объявляем переменную user_role как глобальную
    user_id, first_name, last_name, role = user
    bot.send_message(message.chat.id, f"Авторизация успешна! Добро пожаловать, {first_name} {last_name}! Ваша роль: {role}.")
    user_role = {'user_id': user_id, 'role': role, 'name': first_name + " " + last_name, 'tg_id': message.from_user.id}
    print(user_role)
    if user_role['role'] == "сотрудник":
        show_employee_menu(message.chat.id)
    elif user_role['role'] == "руководитель":
        show_manager_menu(message.chat.id)

    # После успешной аутентификации включаем отслеживание новых задач
    # Запуск функции проверки новых задач
    while True:
        track_new_tasks()
        time.sleep(10)  # Интервал проверки (в секундах)

# Обработчик для аутентификации пароля
def authenticate_password(message, username):
    password = message.text.strip()
    user = authenticate_user(username, password)
    if user:
        successful_authentication(message, user)  # Вызов функции успешной аутентификации
    else:
        bot.send_message(message.chat.id, "Неверное имя пользователя или пароль. Попробуйте еще раз.")

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help(message):
    try:
        role = user_role["role"]
        # Формирование текста помощи
        help_text = "Я могу помочь тебе со следующими задачами:\n\n"
        for command in role_commands[role]:
            help_text += f"{command} - ...\n"
        bot.send_message(message.chat.id, help_text)
    except KeyError:
        bot.send_message(message.chat.id, "Для доступа к командам необходимо авторизоваться.")



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
                event_info = (
                    f"*{event[1]}*\n\n"  # Название события (жирный)
                    f"_{event[2]}_\n\n"  # Описание события (курсив)
                    f"Дата и время: {event[3]}\n"  # Дата и время события
                    f"Местоположение: {event[4]}"  # Местоположение события
                )
                bot.send_message(message.chat.id, event_info, parse_mode="Markdown")
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


@bot.message_handler(commands=['tasks'])
def tasks(message):
    if user_role['role'] == "руководитель":
        # Получаем список задач из базы данных
        tasks = get_tasks1()

        if tasks:
            response = "Список задач:\n"
            for task in tasks:
                # Получаем имя и фамилию пользователя по его user_id
                user_name = get_user_name(task[1])
                # Формируем информацию о задаче
                task_info = (
                    f"Название задачи: {task[2]}\n"
                    f"{task[3]}_\n"
                    f"Исполнитель: {user_name}\n"
                    f"Срок выполнения: {task[4]}\n"
                    f"Статус: {task[5]}\n\n"
                )
                response += task_info
            bot.send_message(message.chat.id, response)
        else:
            bot.send_message(message.chat.id, "Список задач пуст.")

    elif user_role['role'] == "сотрудник":
        # Получаем список задач из базы данных
        tasks = get_tasks2()

        if tasks:
            response = "Список задач:\n"
            for task in tasks:
                task_info = f"Название: {task[2]}\n\n_{task[3]}_\n\n Срок выполнения: {task[4]}\n Статус: {task[5]}\n\n"
                response += task_info
            bot.send_message(message.chat.id, response)

            # Просим пользователя выбрать задачу
            bot.send_message(message.chat.id, "Выберите задачу, чтобы изменить ее статус:")
            show_task_buttons(message, tasks)
        else:
            bot.send_message(message.chat.id, "Список задач пуст.")


# Функция для отображения кнопок с выбором задачи
def show_task_buttons(message, tasks):
    keyboard = types.InlineKeyboardMarkup()
    for task in tasks:
        keyboard.add(types.InlineKeyboardButton(text=task[2], callback_data=f"select_task:{task[0]}"))
    bot.send_message(message.chat.id, "Выберите задачу:", reply_markup=keyboard)

# Обработчик для выбора задачи
@bot.callback_query_handler(func=lambda call: call.data.startswith("select_task"))
def select_task(call):
    try:
        task_id = int(call.data.split(":")[1])
        user_id = user_role['user_id']

        # Проверяем, есть ли такая задача у данного пользователя
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id))
        task = cursor.fetchone()
        cursor.close()
        connection.close()

        if task:
            # Запоминаем выбранную задачу для последующего обновления статуса
            user_data[call.message.chat.id] = {"task_id": task_id}

            # Просим пользователя выбрать новый статус
            bot.send_message(call.message.chat.id, "Выберите новый статус для задачи:",
                             reply_markup=create_status_keyboard())
        else:
            bot.send_message(call.message.chat.id, "Вы не можете выбрать эту задачу.")
    except Exception as e:
        print(f"Ошибка при выборе задачи: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка при выборе задачи.")

# Функция для создания клавиатуры с кнопками статусов
def create_status_keyboard():
    keyboard = types.InlineKeyboardMarkup()
    for status in ["В процессе", "Выполнена", "Отложена", "Отменена", "Ожидает подтверждения", "На утверждении"]:
        keyboard.add(types.InlineKeyboardButton(text=status, callback_data=f"change_status:{status}"))
    return keyboard

# Обработчик для изменения статуса задачи
@bot.callback_query_handler(func=lambda call: call.data.startswith("change_status"))
def change_status(call):
    try:
        new_status = call.data.split(":")[1]
        task_id = user_data.get(call.message.chat.id, {}).get("task_id")

        if task_id:
            # Обновляем статус задачи в базе данных
            connection = sqlite3.connect("tg_bot.db")
            cursor = connection.cursor()
            cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
            connection.commit()
            cursor.close()
            connection.close()

            # Отправляем сообщение об успешном обновлении статуса
            bot.send_message(call.message.chat.id, f"Статус задачи успешно изменен на {new_status}.")
        else:
            bot.send_message(call.message.chat.id, "Не удалось определить выбранную задачу.")
    except Exception as e:
        print(f"Ошибка при изменении статуса задачи: {e}")
        bot.send_message(call.message.chat.id, "Произошла ошибка при изменении статуса задачи.")



def get_tasks1():
    try:
        # Подключение к базе данных
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()

        # Запрос к базе данных для получения задач
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()

        # Закрытие соединения с базой данных
        cursor.close()
        connection.close()

        return tasks
    except Exception as e:
        print(f"Ошибка при получении списка задач: {e}")
        return None

def get_user_name(user_id):
    try:
        # Подключение к базе данных
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()

        # Проверка наличия столбца user_id
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        user_id_exists = any(column[1] == 'user_id' for column in columns)

        if not user_id_exists:
            return "Неизвестный пользователь"

        # Запрос к базе данных для получения имени и фамилии пользователя по его user_id
        cursor.execute("SELECT first_name, last_name FROM users WHERE user_id = ?", (user_id,))
        user_data = cursor.fetchone()

        # Закрытие соединения с базой данных
        cursor.close()
        connection.close()

        if user_data:
            user_name = f"{user_data[0]} {user_data[1]}"
            return user_name
        else:
            return "Неизвестный пользователь"
    except Exception as e:
        print(f"Ошибка при получении имени пользователя: {e}")
        return "Неизвестный пользователь"


def get_tasks2():
    try:
        # Подключение к базе данных
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()

        # Запрос к базе данных для получения задач
        cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_role['user_id']}")
        tasks = cursor.fetchall()

        # Закрытие соединения с базой данных
        cursor.close()
        connection.close()

        return tasks
    except Exception as e:
        print(f"Ошибка при получении списка задач: {e}")
        return None

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
    cursor.execute("SELECT id, first_name, last_name FROM users WHERE role = 'сотрудник'")
    users = cursor.fetchall()
    cursor.close()
    connection.close()
    return users


# Обработчик команды /add_task
@bot.message_handler(commands=["add_task"])
def add_task(message):
    # Проверяем роль пользователя
    if user_role["role"] == "руководитель":
        # Получаем список пользователей из базы данных
        users = get_users()

        # Сохраняем список пользователей для последующего использования
        user_data[message.chat.id] = {'users': users}

        # Запрашиваем у пользователя выбор пользователя
        bot.send_message(message.chat.id, "Выберите пользователя из списка:")
        show_users(message)
    else:
        # Если роль пользователя не "руководитель", отправляем сообщение о запрете доступа
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")



# Функция для отображения списка пользователей
def show_users(message):
    users = user_data[message.chat.id]['users']
    markup = types.ReplyKeyboardMarkup(row_width=1)
    for user_id, first_name, last_name in users:
        button_text = f"{first_name} {last_name} (user_id: {user_id})"
        markup.add(types.KeyboardButton(button_text))
    bot.send_message(message.chat.id, "Выберите пользователя из списка:", reply_markup=markup)
    bot.register_next_step_handler(message, handle_user_selection)


# Регистрируем обработчик нажатия на кнопку выбора пользователя
def handle_user_selection(message):
    users = user_data[message.chat.id]['users']
    for user_id, first_name, last_name in users:
        button_text = f"{first_name} {last_name} (user_id: {user_id})"
        if message.text == button_text:
            user_data[message.chat.id]['user_id'] = user_id
            bot.send_message(message.chat.id, f"Выбран пользователь: {first_name} {last_name} (user_id: {user_id})",
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
    if user_role['role'] == "сотрудник":
        show_employee_menu(message.chat.id)
    elif user_role['role'] == "руководитель":
        show_manager_menu(message.chat.id)

# Функция для проверки новых задач
def track_new_tasks():
    global old_tasks
    connection = sqlite3.connect("tg_bot.db")
    cursor = connection.cursor()
    result = []
    # Запрос для выборки новых задач
    cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_role['user_id']}")
    new_tasks = cursor.fetchall()
    for task in new_tasks:
        if task not in old_tasks:
            result.append(task)
            old_tasks.append(task)
    cursor.close()
    connection.close()

    # Отправка уведомлений о новых задачах
    for task in result:
        task_info = f" Новая задача:\n\nНазвание: {task[2]}\n\n_{task[3]}_\n\nСрок выполнения: {task[4]}\n\n"
        bot.send_message(user_role['tg_id'], task_info)

# Функция для добавления события в таблицу events
def add_event(title, description, date_time, location):
    try:
        # Подключение к базе данных
        connection = sqlite3.connect("tg_bot.db")
        cursor = connection.cursor()

        # Вставка нового события в таблицу events
        cursor.execute("INSERT INTO events (title, description, date_time, location) VALUES (?, ?, ?, ?)",
                       (title, description, date_time, location))
        connection.commit()

        # Закрытие соединения с базой данных
        cursor.close()
        connection.close()

        return True  # Успешно добавлено
    except Exception as e:
        print(f"Ошибка при добавлении события: {e}")
        return False  # Ошибка при добавлении

# Обработчик команды /add_event
@bot.message_handler(commands=['add_event'])
def add_event_handler(message):
    # Проверяем роль пользователя
    if user_role["role"] == "руководитель":
        bot.send_message(message.chat.id, "Введите название события:")
        bot.register_next_step_handler(message, get_title)
    else:
        # Если роль пользователя не "руководитель", отправляем сообщение о запрете доступа
        bot.send_message(message.chat.id, "У вас нет доступа к этой команде.")


# Функция для получения названия события
def get_title(message):
    title = message.text.strip()
    bot.send_message(message.chat.id, "Введите описание события:")
    bot.register_next_step_handler(message, lambda msg: get_description(msg, title))

# Функция для получения описания события
def get_description(message, title):
    description = message.text.strip()
    bot.send_message(message.chat.id, "Введите дату и время события (в формате YYYY-MM-DD HH:MM):")
    bot.register_next_step_handler(message, lambda msg: get_date_time(msg, title, description))

# Функция для получения даты и времени события
def get_date_time(message, title, description):
    date_time = message.text.strip()
    bot.send_message(message.chat.id, "Введите место проведения события:")
    bot.register_next_step_handler(message, lambda msg: get_location(msg, title, description, date_time))

# Функция для получения места проведения события
def get_location(message, title, description, date_time):
    location = message.text.strip()
    save_event(message, title, description, date_time, location)

# Функция для сохранения события в базу данных
def save_event(message, title, description, date_time, location):
    if add_event(title, description, date_time, location):
        bot.send_message(message.chat.id, "Событие успешно добавлено!")
    else:
        bot.send_message(message.chat.id, "Ошибка при добавлении события. Попробуйте еще раз.")

# Обработчик сообщений с недействительными командами
@bot.message_handler(func=lambda message: True)
def handle_invalid_command(message):
    bot.send_message(message.chat.id, "Извините, такой команды не существует. "
                                      "Пожалуйста, воспользуйтесь командой /help для получения списка доступных команд.")

bot.polling(none_stop=True)