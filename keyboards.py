from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup


main_keyboard = InlineKeyboardMarkup(
    buttons = [
        [
            # InlineKeyboardButton(text="Создать свой профиль", callback_data="profile"),
            # InlineKeyboardButton(text="Посмотреть свой профиль", callback_data="dislike")
        ],
        [
            InlineKeyboardButton(text="Поиск новых знакомств!", callback_data="profiles")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)
