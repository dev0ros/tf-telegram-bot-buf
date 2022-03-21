import telebot
import sqlite3
from telebot import types
import pymorphy2
import re
from telebot import apihelper

TOKEN = '5203136995:AAEkKXLQNSLOxDwQerjSTBlF0OZYqiwu4YA'
bot = telebot.TeleBot(TOKEN)
# Раскомментировать для подключения через носок
#apihelper.proxy = {'https':'socks5://45.55.32.201:5884'}

conn = sqlite3.connect('database.db', check_same_thread=False)
cursor = conn.cursor()

morph = pymorphy2.MorphAnalyzer()

# Кнопки для клиентской части
start_button = types.KeyboardButton("/start_buffer")#"Начать буферизацию сообщений") #yes
make_theme_btn = types.KeyboardButton("/add_theme")#"Создать тему")#yes
print_count_messages_btn = types.KeyboardButton("/count_msgs")#"Количество сообщений на темы")
check_themes_button = types.KeyboardButton("/dump_theme")#"Предложения на тему")
back_button = types.KeyboardButton("/back")#"Назад")

to_middle_button = types.KeyboardButton("/settings")#"Настройки")
### необходимо добавить выбор кнопки на каждую тему
stop_button = types.KeyboardButton("/stop")#"Остановить работу бота")
add_theme_button = types.KeyboardButton("/choose_theme")#'Ввести название темы')#yes

# механизм включения стартовой клавиатуры
start_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
start_keyboard.add(start_button)
start_keyboard.add(stop_button)
start_keyboard.add(to_middle_button)
### нужна кнопка и интерфейс для создания новой темы с добавлением ключевых слов

# механизм включения основной клавиатуры
middle_keyboard = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
middle_keyboard.add(make_theme_btn)
middle_keyboard.add(print_count_messages_btn)
middle_keyboard.add(check_themes_button)
middle_keyboard.add(back_button)

### понадобится клавиатуры с кнопками для выбора темы
# механизмы создания новой темы
make_theme_keyboard = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
make_theme_keyboard.add(add_theme_button)

# variable to switch off message saving if not needed
is_writing = False

# Start
@bot.message_handler(commands=['start'])
def start_helper(message):
    start_message = "Привет! Я помогу тебе с буферизацией сообщений!"
    bot.send_message(message.chat.id, message.chat.type)
    bot.send_message(message.chat.id, start_message, reply_markup=start_keyboard)

# Begin Buf
#@bot.message_handler(regexp="Начать буферизацию сообщений")
@bot.message_handler(commands=['start_buffer'])
def begin_bufferis(message):
    global is_writing
    is_writing = True
    start_message = "Здесь будет буферизация сообщений"
    if str(message.chat.type) == 'private':
        bot.send_message(message.chat.id, start_message, reply_markup=middle_keyboard)
    else:
        msg = bot.send_message(message.chat.id, 'Буферизация канала')
        bot.register_next_step_handler(msg, check_messages)

# Создание темы
#@bot.message_handler(regexp="Создать тему")
@bot.message_handler(commands=['add_theme'])
def make_theme(message):
    start_message = "Введите название темы;ключевое слово"
    msg = bot.send_message(message.chat.id, start_message)
    bot.register_next_step_handler(msg, make_theme2)

def make_theme2(message):
    text_message = message.text.split(';')
    name_theme = text_message[0]
    keyword_theme = text_message[1].lower()

    to_make_theme(name_theme, keyword_theme, message)

    bot.send_message(message.chat.id, 'Тема успешно создана!', reply_markup=middle_keyboard)

#@bot.message_handler(regexp="Предложения на тему")
#MAKE BY THEME NAMES

@bot.message_handler(commands=['dump_theme'])
def get_sentences_theme(message):
    global list_keywords
    list_keywords, rows_ = get_list_keywords(message)
    themes_keyboard = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for i in list_keywords:  
        themes_keyboard.add(types.KeyboardButton("/"+i))
    themes_keyboard.add(to_middle_button)
    start_message = "Выберите топик"
    bot.send_message(message.chat.id, start_message, reply_markup=themes_keyboard)

#@bot.message_handler(regexp="Количество сообщений на темы")
@bot.message_handler(commands=['count_msgs'])
def get_count_messages(message):
    checked_themes_dict = dict()
    ct_temp = []
    # вытащить из базы данных сообщения на темы
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM messages_table WHERE sender = '"+message.from_user.username+"'")
    rows = cursor.fetchall()
    print(rows)
    for row in rows:
       ct_temp.append(row[0])
    for i in ct_temp:
        if i in checked_themes_dict:
            continue
        checked_themes_dict[i] = 0
        for j in ct_temp:
            if i == j:  checked_themes_dict[i] += 1
    message_count_info = ""
    for i in checked_themes_dict:
        message_count_info += "Тема " + i + ": " + str(checked_themes_dict[i]) + "\n"

    bot.send_message(message.chat.id, message_count_info, reply_markup=middle_keyboard)
    # пусть данные будут находиться в одном списке
    # просчитаем по определенной теме каждое сообщение и будет проверять, нет ли такого уже в ctl
    # данные будут храниться по принципу ключ-значение, где ключем будет название темы, значением количество сообщением на эту тему
    #bot.send_message(message.chat.id, 'a', reply_markup=start_keyboard)
    
#@bot.message_handler(regexp="Назад")
@bot.message_handler(commands=['back'])
def back_button_handler_middle(message):
    start_message = "Стартовое меню"
    bot.send_message(message.chat.id, start_message, reply_markup=start_keyboard)
    
#@bot.message_handler(regexp="Настройки")
@bot.message_handler(commands=['settings'])
def settings_button_handler_start(message):
    start_message = "Меню настроек"
    bot.send_message(message.chat.id, start_message, reply_markup=middle_keyboard)
    
#@bot.message_handler(regexp="Остановить работу бота")
@bot.message_handler(commands=['stop'])
def stop_bot(message):
    global is_writing
    is_writing = False
    start_message = "Всего доброго!"
    bot.send_message(message.chat.id, start_message, reply_markup=start_keyboard)
    #bot.stop_polling()

@bot.message_handler(regexp="/")
def get_sentences_by_topic_theme(message):
    message.text=message.text[1:]
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM messages_table WHERE instr(message_t,'"+message.text+"') AND sender = '"+message.from_user.username+"'")
    rows_ = cursor.fetchall()
    print(rows_)
    for row in rows_:
        bot.send_message(message.chat.id,"Тема: "+ row[1]+"; " + row[2]+ "\n Отправитель: @"+row[5], reply_markup=middle_keyboard)
    
# функции для буферизации канала
@bot.message_handler(content_types=["text"])
def check_messages(message):
    global is_writing
    if is_writing:
        list_keywords, rows_ = get_list_keywords(message)
        temp_theme_name = None
        for i in list_keywords:
            for j in rows_:
                index_, theme_name, keyword_, sender = j;
                if keyword_ == i:
                    temp_theme_name = theme_name
            temp_message_text = message.text
            temp_message_text = re.sub('\W+', ' ', temp_message_text)
            #print(temp_message_text)
            temp_message_text = temp_message_text.split(' ')
            for k in range(len(temp_message_text)):
                p = morph.parse(temp_message_text[k])[0]
                temp_message_text[k] = p.normal_form
                #print(temp_message_text[k])
            print(i)
            if i in temp_message_text:
                #print(i)
                send_data_message(temp_theme_name, message.text, message.date, message.from_user.username, message.id, message.chat.id, message)
            #print(list_keywords)
        #bot.send_message(message.chat.id, message.text)
    
# функции для работы с базой данных
def to_make_theme(theme_name: str, key_word: str, message):
    cursor.execute('INSERT INTO themes_table (name, key_word, sender) VALUES (?, ?, ?)', (theme_name, key_word,message.from_user.username))
    conn.commit()

def get_list_keywords(message):
    cursor = conn.cursor()
    cursor.execute("SELECT key_word FROM themes_table WHERE sender = '"+message.from_user.username+"'")
    rows = cursor.fetchall()
    cursor.execute("SELECT * FROM themes_table WHERE sender = '"+message.from_user.username+"'")
    rows_ = cursor.fetchall()
    list_keywords = []
    for row in rows:
        list_keywords.append(row[0])
    print(list(set(list_keywords)))
    print(rows_)
    return list(set(list_keywords)), rows_

def send_data_message(theme_name: str, text_message: str, author_message: str, id_message:int, date_message:str, channel_name:str, message):
    cursor.execute('INSERT INTO messages_table (name, message_t, date_message, author_message, id_message, channel_name, sender) VALUES (?, ?, ?, ?, ?, ?, ?)', (theme_name, text_message, date_message, author_message, id_message, channel_name, message.from_user.username))
    conn.commit()
#get_list_keywords()
bot.infinity_polling()


# сделать проверку на повторяющиеся значения в таблице
# улучшить интерфейс взаимодействия между пользователем и ботом
# перенести бота на Yandex Cloud
# подключить Yandex Database
# добавить проверку слов с помощью естественного языка
# рефакторинг кода на ООП
# Add offset for parse failing (https://api.telegram.org/bot5203136995:AAEkKXLQNSLOxDwQerjSTBlF0OZYqiwu4YA/getupdates?offset=333551457)
