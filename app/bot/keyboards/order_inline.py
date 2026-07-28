from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def accept_order_keyboard(
    order_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Прийняти",
                    callback_data=f"accept:{order_id}",
                )
            ]
        ]
    )


def picked_up_keyboard(
    order_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="� Забрав товар",
                    callback_data=f"pickup:{order_id}",
                )
            ]
        ]
    )


def delivering_keyboard(
    order_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚚 В дорозі",
                    callback_data=f"delivering:{order_id}",
                )
            ]
        ]
    )


def delivered_keyboard(
    order_id: int,
) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📍 Передано магазину",
                    callback_data=f"delivered:{order_id}",
                )
            ]
        ]
    )