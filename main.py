import sqlite3
import os
import keyboards
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import ParseMode
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

bot = Bot(token="your_token")
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS profiles (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    age INTEGER,
                    country TEXT,
                    gender TEXT,
                    photo TEXT
                )''')
conn.commit()


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("Привет! Для начала работы с ботом введите /profile чтобы создать свою анкету."
                         ,reply_markup=keyboards.main_keyboard)


@dp.message_handler(commands=["profile"])
async def create_profile(message: types.Message):
    await message.answer("Введите свое имя:")
    await ProfileForm.name.set()


class ProfileForm(StatesGroup):
    name = State()
    age = State()
    country = State()
    gender = State()
    photo = State()


@dp.message_handler(state=ProfileForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer("Введите свой возраст:")
    await ProfileForm.age.set()


@dp.message_handler(state=ProfileForm.age)
async def process_age(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['age'] = message.text
    await message.answer("Введите свою страну:")
    await ProfileForm.country.set()


@dp.message_handler(state=ProfileForm.country)
async def process_country(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['country'] = message.text
    await message.answer("Введите свой пол:")
    await ProfileForm.gender.set()


@dp.message_handler(state=ProfileForm.gender)
async def process_gender(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gender'] = message.text
    await message.answer("Отправьте свое фото:")
    await ProfileForm.photo.set()


@dp.message_handler(content_types=types.ContentType.PHOTO, state=ProfileForm.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    photo_file = await bot.get_file(photo.file_id)
    file_ext = os.path.splitext(photo_file.file_path)[-1]
    file_name = f"photo_{message.from_user.id}{file_ext}"
    photo_path = os.path.join("photos", file_name)
    await photo_file.download(photo_path)
    async with state.proxy() as data:
        data['photo'] = photo_path
    await message.answer("Фотография сохранена! Анкета создана!")
    await save_profile(message.from_user.id, data)
    await state.finish()


async def save_profile(user_id, data):
    cursor.execute('''INSERT OR REPLACE INTO profiles (user_id, name, age, country, gender, photo)
                      VALUES (?, ?, ?, ?, ?, ?)''',
                   (user_id, data['name'], data['age'], data['country'], data['gender'], data['photo']))
    conn.commit()


@dp.message_handler(commands=["my_profile"])
async def view_own_profile(message: types.Message):
    profile = await get_profile(message.from_user.id)
    if profile:
        user_id, name, age, country, gender, photo_path = profile
        with open(photo_path, 'rb') as photo_file:
            await bot.send_photo(message.from_user.id, photo_file, caption=format_profile(profile))
    else:
        await message.answer("У вас еще нет анкеты. Создайте ее с помощью команды /profile.")


async def get_profile(user_id):
    cursor.execute('''SELECT * FROM profiles WHERE user_id=?''', (user_id,))
    return cursor.fetchone()


def format_profile(profile):
    user_id, name, age, country, gender, photo = profile
    return f"Имя: {name}\nВозраст: {age}\nСтрана: {country}\nПол: {gender}"


@dp.message_handler(commands=["profiles"])
async def view_profiles(message: types.Message):
    await message.answer("Выберите, как вы хотите просмотреть анкеты:",

                         )


@dp.message_handler(Text(equals="Поиск по параметрам"))
async def search_profiles(message: types.Message):
    await message.answer("Выберите параметры для поиска:",
                         reply_markup=types.ReplyKeyboardMarkup(
                             keyboard=[
                                 [types.KeyboardButton(text="Страна")],
                                 [types.KeyboardButton(text="Пол")],
                                 [types.KeyboardButton(text="Возраст")]
                             ],
                             resize_keyboard=True
                         ))


class ProfileFilterForm(StatesGroup):
    country = State()
    gender = State()
    age = State()


@dp.message_handler(Text(equals="Страна"))
async def process_country_filter(message: types.Message):
    await message.answer("Введите страну:")
    await ProfileFilterForm.country.set()


@dp.message_handler(Text(equals="Пол"))
async def process_gender_filter(message: types.Message):
    await message.answer("Введите пол (мужской/женский):")
    await ProfileFilterForm.gender.set()


@dp.message_handler(Text(equals="Возраст"))
async def process_age_filter(message: types.Message):
    await message.answer("Введите возраст:")
    await ProfileFilterForm.age.set()


@dp.message_handler(state=ProfileFilterForm.country)
async def process_country_for_filter(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['country'] = message.text
    profiles = await search_profiles_in_database(data)
    if profiles:
        for profile in profiles:
            await message.answer(format_profile(profile))
    else:
        await message.answer("По вашему запросу анкет не найдено.")
    await state.finish()


@dp.message_handler(state=ProfileFilterForm.gender)
async def process_gender_for_filter(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['gender'] = message.text.lower()
    profiles = await search_profiles_in_database(data)
    if profiles:
        for profile in profiles:
            await message.answer(format_profile(profile))
    else:
        await message.answer("По вашему запросу анкет не найдено.")
    await state.finish()


@dp.message_handler(state=ProfileFilterForm.age)
async def process_age_for_filter(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['age'] = message.text
    profiles = await search_profiles_in_database(data)
    if profiles:
        for profile in profiles:
            await message.answer(format_profile(profile))
    else:
        await message.answer("По вашему запросу анкет не найдено.")
    await state.finish()



async def search_profiles_in_database(params):
    if 'country' in params:
        cursor.execute('''SELECT * FROM profiles WHERE country=?''', (params['country'],))
    elif 'gender' in params:
        cursor.execute('''SELECT * FROM profiles WHERE gender=?''', (params['gender'],))
    elif 'age' in params:
        cursor.execute('''SELECT * FROM profiles WHERE age=?''', (params['age'],))
    return cursor.fetchall()


@dp.message_handler(Text(equals="Случайный профиль"))
async def random_profile(message: types.Message):
    profile = await get_random_profile()
    if profile:
        await send_profile(message, profile)
        await message.answer("Хотите увидеть следующий профиль?", reply_markup=next_profile_keyboard())
    else:
        await message.answer("Не удалось найти случайный профиль.")


async def send_profile(message, profile):
    user_id, name, age, country, gender, photo_path = profile
    with open(photo_path, 'rb') as photo_file:
        await bot.send_photo(message.chat.id, photo_file)
        await message.answer(format_profile(profile))

async def get_random_profile():
    cursor.execute('''SELECT * FROM profiles ORDER BY RANDOM() LIMIT 1''')
    return cursor.fetchone()


def next_profile_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Случайный профиль"))
    return keyboard


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.INFO)
    from aiogram import executor

    executor.start_polling(dp, skip_updates=True)
