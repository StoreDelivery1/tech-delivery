from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

courier_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="📦 Вільні заявки",
            )
        ],
        [
            KeyboardButton(
                text="🚚 Мої доставки",
            )
        ],
        [
            KeyboardButton(
                text="🟢 Я онлайн",
            ),
            KeyboardButton(
                text="🔴 Я офлайн",
            ),
        ],
        [
            KeyboardButton(
                text="👤 Профіль",
            )
        ],
    ],
    resize_keyboard=True,
)