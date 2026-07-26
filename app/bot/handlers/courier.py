from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.order_inline import (
    accept_order_keyboard,
    delivered_keyboard,
    delivering_keyboard,
    picked_up_keyboard,
)
from app.bot.utils.order_formatter import format_order
from app.database.session import SessionLocal
from app.models.order import OrderStatus
from app.services.activation_service import ActivationService
from app.services.courier_service import CourierService

router = Router()


def is_free_orders_button(text: str | None) -> bool:
    return text in {"📦 Вільні заявки", "📦 Вільні замовлення"}


@router.message(F.text.in_({"📦 Вільні заявки", "📦 Вільні замовлення"}))
async def free_orders_handler(message: Message):
    print(f"ROUTER: courier | {message.text}")
    db = SessionLocal()

    try:
        courier = ActivationService.get_by_telegram(
            db,
            message.from_user.id,
        )

        if courier is None:
            await message.answer("❌ Користувача не знайдено")
            return

        open_orders = CourierService.get_open_orders(db)

        if not open_orders:
            await message.answer("📭 Наразі немає доступних заявок.")
            return

        for order in open_orders:
            await message.answer(
                format_order(order),
                reply_markup=accept_order_keyboard(order.id),
            )

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    finally:
        db.close()


@router.message(F.text == "📋 Мої замовлення")
async def my_orders_handler(message: Message):
    db = SessionLocal()

    try:
        courier = ActivationService.get_by_telegram(
            db,
            message.from_user.id,
        )

        if courier is None:
            await message.answer("❌ Користувача не знайдено")
            return

        my_orders = CourierService.get_orders(db, courier.id)

        if not my_orders:
            await message.answer("📭 У вас немає активних замовлень.")
            return

        for order in my_orders:
            keyboard = None
            if order.status == OrderStatus.ACCEPTED:
                keyboard = picked_up_keyboard(order.id)
            elif order.status == OrderStatus.PICKED_UP:
                keyboard = delivering_keyboard(order.id)
            elif order.status == OrderStatus.DELIVERING:
                keyboard = delivered_keyboard(order.id)

            await message.answer(
                format_order(order),
                reply_markup=keyboard,
            )

    except ValueError as e:
        await message.answer(f"❌ {str(e)}")
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("accept:"))
async def accept_order_callback(callback: CallbackQuery):
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        courier = ActivationService.get_by_telegram(
            db,
            callback.from_user.id,
        )

        if courier is None:
            await callback.answer("❌ Користувача не знайдено", show_alert=True)
            return

        CourierService.accept_order(
            db=db,
            order_id=order_id,
            courier_id=courier.id,
        )

        await callback.message.edit_text(
            "✅ Замовлення успішно прийнято.",
            reply_markup=None,
        )
        await callback.answer()

    except (ValueError, TypeError) as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("pickup:"))
async def pickup_order_callback(callback: CallbackQuery):
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        courier = ActivationService.get_by_telegram(
            db,
            callback.from_user.id,
        )

        if courier is None:
            await callback.answer("❌ Користувача не знайдено", show_alert=True)
            return

        CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=courier.id,
            new_status=OrderStatus.PICKED_UP,
        )

        await callback.message.edit_text("✅ Статус оновлено.", reply_markup=None)
        await callback.answer()

    except (ValueError, TypeError) as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("delivering:"))
async def delivering_order_callback(callback: CallbackQuery):
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        courier = ActivationService.get_by_telegram(
            db,
            callback.from_user.id,
        )

        if courier is None:
            await callback.answer("❌ Користувача не знайдено", show_alert=True)
            return

        CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=courier.id,
            new_status=OrderStatus.DELIVERING,
        )

        await callback.message.edit_text("✅ Статус оновлено.", reply_markup=None)
        await callback.answer()

    except (ValueError, TypeError) as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()


@router.callback_query(lambda callback: callback.data and callback.data.startswith("delivered:"))
async def delivered_order_callback(callback: CallbackQuery):
    db = SessionLocal()

    try:
        order_id = int(callback.data.split(":", 1)[1])

        courier = ActivationService.get_by_telegram(
            db,
            callback.from_user.id,
        )

        if courier is None:
            await callback.answer("❌ Користувача не знайдено", show_alert=True)
            return

        CourierService.change_status(
            db=db,
            order_id=order_id,
            courier_id=courier.id,
            new_status=OrderStatus.DELIVERED,
        )

        await callback.message.edit_text("✅ Доставлено.", reply_markup=None)
        await callback.answer()

    except (ValueError, TypeError) as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)
    finally:
        db.close()
