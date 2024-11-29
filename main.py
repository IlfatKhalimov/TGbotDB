import sqlalchemy
import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import random
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

Base = declarative_base()


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


class Dictionary(Base):
    __tablename__ = "dictionary"

    id = sq.Column(sq.Integer, primary_key=True)
    russian = sq.Column(sq.String(length=40), nullable=False)
    english = sq.Column(sq.String(length=40), nullable=False)

    def __str__(self):
        return f'{self.id}: {self.russian}: {self.english}'


class User(Base):
    __tablename__ = "user"

    id = sq.Column(sq.Integer, primary_key=True)
    token = sq.Column(sq.String(length=100), unique=True)

    def __str__(self):
        return f'{self.id}: {self.token}'


class Udictionary(Base):
    __tablename__ = "udictionary"

    id = sq.Column(sq.Integer, primary_key=True)
    did = sq.Column(sq.Integer, sq.ForeignKey("dictionary.id"), nullable=False)
    uid = sq.Column(sq.Integer, sq.ForeignKey("user.id"), nullable=False)

    dictionary = relationship(Dictionary, backref="udictionary")
    user = relationship(User, backref="udictionary")

    def __str__(self):
        return f'{self.id}: {self.did}: {self.uid}'


def fillin_dict():
    word1 = Dictionary(russian='Мир', english='Peace')
    word2 = Dictionary(russian='Привет', english='Hello')
    word3 = Dictionary(russian='Белый', english='White')
    word4 = Dictionary(russian='Зеленый', english='Green')
    word5 = Dictionary(russian='Черный', english='Black')
    word6 = Dictionary(russian='Красный', english='Red')
    word7 = Dictionary(russian='Он', english='He')
    word8 = Dictionary(russian='Она', english='She')
    word9 = Dictionary(russian='Мы', english='We')
    word10 = Dictionary(russian='Они', english='They')
    word11 = Dictionary(russian='Машина', english='Car')
    session.add_all([word1, word2, word3, word4, word5, word6, word7, word8, word9, word10, word11])
    session.commit()


def fillin_u_dict(tb):
    global user_id  # Идентификатор пользователя, создаваемый при записи ТГ-токена в БД
    user_begin = True  # Фиксируем, что новый пользователь начал работу
    u_bot_token = User(token=tb)
    session.add(u_bot_token)
    session.commit()
    usr_added = session.query(User).filter(User.token == tb)
    for u in usr_added.all():
        user_id = u.id
        fillwords = session.query(Dictionary)
        for d in fillwords.all():
            # print(d.id, d.russian, d.english)
            u_word = Udictionary(did=d.id, uid=u.id)  # Записываем в таблицу Udictionary идентификаторы слов из таблицы
            # Dictionary с идентификатором пользователя
            session.add(u_word)
    session.commit()
    print('Udictionary заполнен')
    return user_begin


print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = input("Введите ваш ТГ-токен: ")
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []
next_word = ''
user_id = 0
user_new = True


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    global buttons, next_word, user_new
    buttons = []
    others = []
    begin_range = 1
    end_range = begin_range + 4
    four_words = False
    target_word = ''
    translate = ''
    i = 1
    cid = message.chat.id
    if user_new:  # if user is new
        bot.send_message(cid, "Привет 👋 Давай попрактикуемся в английском языке. Тренировки можешь проходить в "
                              "удобном для себя темпе. У тебя есть возможность использовать тренажёр, как конструктор, "
                              "и собирать свою собственную базу для обучения. Для этого воспрользуйся инструментами:"
                         + '\n' + "   добавить слово ➕"
                         + '\n' + "   удалить слово 🔙"
                         + '\n' + "Ну что, начнём ⬇️")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    uwords = (
        session.query(Udictionary.id, Dictionary.russian, Dictionary.english).join(Dictionary).join(User).filter
        (User.token == token_bot))  # Делаем запрос всех слов, которые изучает пользователь с тоеном token_bot
    first_word = []
    second_word = []
    third_word = []
    row_count = 0
    for row in uwords.all():  # Запоминаем первые три слова из запроса, чтобы зациклить проверку слов пользователем
        row_count = row_count + 1
        if row_count == 1:
            first_word = row.english
        elif row_count == 2:
            second_word = row.english
        elif row_count == 3:
            third_word = row.english
    print('количество слов в словаре пользователя: ', row_count)
    for w in uwords.all():
        if next_word == w.english:  # Определяем четыре слова, которые помещаются на кнопки ТГ-бота
            four_words = True
        if user_new or four_words:
            if i == begin_range:
                target_word = w.english
                translate = w.russian
                i = i + 1
                # print(w.russian, w.english)
            elif begin_range < i < end_range:
                if i == begin_range + 1:
                    next_word = w.english  # Запоминаем следующее слово, которое станет целевым при нажатии "Дальше"
                # print(w.russian, w.english)
                others.append(w.english)
                i = i + 1
            else:
                four_words = False
    if len(others) == 2:  # Переход с последних изучаемых слов на первые - зацикливаем проверку слов пользователем
        others.append(first_word)
    elif len(others) == 1:
        others.append(first_word)
        others.append(second_word)
    elif len(others) == 0:
        others.append(first_word)
        others.append(second_word)
        others.append(third_word)
        next_word = first_word
    # print(len(others), next_word)
    user_new = False

    target_word_btn = types.KeyboardButton(target_word)
    buttons.append(target_word_btn)
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])

    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        fillwords = session.query(Dictionary).filter(Dictionary.english == data['target_word'])
        for d in fillwords.all():
            session.query(Udictionary).filter(Udictionary.did == d.id, Udictionary.uid == user_id).delete()
            # Удаляем указанное слово (идентификатор did) из таблицы Udictionary с идентификатором текущего пользователя
        session.commit()
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    global next_word
    # Сохраняем текущее слово, чтобы продолжить проверку пользователя с него же
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        next_word = data['target_word']

    cid = message.chat.id

    # Спрашиваем английское слово
    word_query = bot.send_message(cid, 'Введите английское слово:')
    bot.register_next_step_handler(word_query, word_write)

def word_write(message):
    english_word = message.text  # Сохраняем английское слово
    cid = message.chat.id

    # Спрашиваем перевод
    translate_query = bot.send_message(cid, 'Введите русский перевод слова:')
    bot.register_next_step_handler(translate_query, translate_write, english_word)

def translate_write(message, english_word):
    global user_id
    russian_translation = message.text  # Сохраняем перевод
    cid = message.chat.id

    # Записываем полученные данные в базу данных
    word = Dictionary(russian=russian_translation, english=english_word)
    session.add(word)
    new_word = session.query(Dictionary).filter(Dictionary.english == english_word)
    new_word_id = 0
    for w in new_word.all():
        new_word_id = w.id  # Запоминаем идентификатор введенного слова пользователем и записываем его в таблицу
        # Udictionary
    user_word = Udictionary(did=new_word_id, uid=user_id)
    session.add(user_word)
    session.commit()
    bot.send_message(cid, 'Слово успешно добавлено!')

    create_cards(message)


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)


if __name__ == '__main__':
    DSN = "postgresql://postgres:bazadannykh@localhost:5432/training_dictionary_db"
    engine = sqlalchemy.create_engine(DSN)
    create_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    create_tables(engine)

    fillin_dict()  # Записываем начальный набор слов в базу данных - заполняем словарь

    # user_first = fillin_u_dict('Token1')
    # user_second = fillin_u_dict('Token2')
    user_new = fillin_u_dict(token_bot)  # Запрашиваем токен ТГ-бота пользователя и создаем отношение Udictionary,
    # связывающее словарь с пользователем

    bot.add_custom_filter(custom_filters.StateFilter(bot))
    bot.infinity_polling(skip_pending=True)