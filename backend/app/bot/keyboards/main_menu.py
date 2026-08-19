from aiogram.types import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def admin_main_menu() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="👥 Користувачі",
                ),
                KeyboardButton(
                    text="📦 Замовлення",
                ),
            ],
            [
                KeyboardButton(
                    text="📊 Статистика",
                ),
                KeyboardButton(
                    text="👤 Профіль",
                ),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію...",
    )


def admin_staff_menu() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="➕ Додати менеджера",
                ),
                KeyboardButton(
                    text="➕ Додати кур'єра",
                ),
            ],
            [
                KeyboardButton(
                    text="⬅️ Назад",
                ),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію...",
    )


def admin_users_menu() -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="➕ Створити менеджера",
                ),
                KeyboardButton(
                    text="➕ Створити кур'єра",
                ),
            ],
            [
                KeyboardButton(
                    text="👨‍💼 Менеджери",
                ),
                KeyboardButton(
                    text="🚴 Кур'єри",
                ),
            ],
            [
                KeyboardButton(
                    text="⬅️ Назад",
                ),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію...",
    )


def courier_main_menu(courier=None) -> ReplyKeyboardMarkup:
    from app.models.user import CourierAvailability

    # Determine shift button based on courier availability
    shift_button_text = "🟢 Почати зміну"
    if courier and hasattr(courier, "availability"):
        if courier.availability in (CourierAvailability.AVAILABLE, CourierAvailability.BUSY):
            shift_button_text = "🔴 Завершити зміну"

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text=shift_button_text,
                ),
            ],
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
        ],
        resize_keyboard=True,
        input_field_placeholder="Оберіть дію...",
    )


def manager_main_menu(active_count: int = 0, all_count: int = 0, incoming_count: int = 0) -> ReplyKeyboardMarkup:

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📦 Створити заявку",
                ),
                KeyboardButton(
                    text="🛒 Замовити товар",
                ),
            ],
            [
                KeyboardButton(
                    text=f"🟡 Активні замовлення ({active_count})",
                ),
            ],
            [
                KeyboardButton(
                    text=f"📋 Всі замовлення ({all_count})",
                ),
            ],
            [
                KeyboardButton(
                    text=f"📥 До нас їдуть ({incoming_count})",
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