from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def courier_main_menu() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📦 Вільні замовлення",
                ),
            ],
            [
                KeyboardButton(
                    text="📋 Мої замовлення",
                ),
            ],
            [
                KeyboardButton(
                    text="👤 Профіль",
                ),
                KeyboardButton(
                    text="📊 Статистика",
                ),
            ],
            [
                KeyboardButton(
                    text="🟢 Я онлайн",
                ),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію...",
    )


def manager_main_menu() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="➕ Створити замовлення",
                ),
            ],
            [
                KeyboardButton(
                    text="📋 Мої замовлення",
                ),
            ],
            [
                KeyboardButton(
                    text="👥 Кур'єри",
                ),
                KeyboardButton(
                    text="📊 Статистика",
                ),
            ],
            [
                KeyboardButton(
                    text="👤 Профіль",
                ),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію...",
    )