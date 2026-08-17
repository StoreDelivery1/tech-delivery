from app.models.order import Order
from app.bot.utils.store_formatter import format_store_name


def format_order(order: Order) -> str:
    priority_icons = {
        "LOW": "🟢",
        "NORMAL": "🟡",
        "HIGH": "🟠",
        "URGENT": "🔴",
    }

    priority = priority_icons.get(
        order.priority.value,
        "⚪",
    )

    return (
        f"📦 <b>Замовлення {order.number}</b>\n\n"
        f"🏪 <b>Звідки:</b> {format_store_name(order.from_store)}\n"
        f"📍 <b>Куди:</b> {format_store_name(order.to_store)}\n\n"
        f"📝 <b>Опис:</b>\n"
        f"{order.description}\n\n"
        f"📏 <b>Розмір:</b> "
        f"{getattr(order, 'size', None).value if getattr(order, 'size', None) else '-'}\n"
        f"{priority} <b>Пріоритет:</b> "
        f"{order.priority.value}"
    )