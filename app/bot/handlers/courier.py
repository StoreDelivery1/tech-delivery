from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.order_inline import accept_order_keyboard
from app.bot.utils.order_formatter import format_order
from app.database.session import SessionLocal
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
