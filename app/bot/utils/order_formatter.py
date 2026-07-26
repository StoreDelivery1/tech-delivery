from app.models.order import Order


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
        f"🏪 <b>Звідки:</b> {order.from_store.name}\n"
        f"📍 <b>Куди:</b> {order.to_store.name}\n\n"
        f"📝 <b>Опис:</b>\n"
        f"{order.description}\n\n"
        f"⚖️ <b>Вага:</b> "
        f"{order.estimated_weight or '-'} кг\n"
        f"{priority} <b>Пріоритет:</b> "
        f"{order.priority.value}"
    )