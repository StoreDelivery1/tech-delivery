from app.models.store import Store, StoreNetwork

_NETWORK_LABELS = {
    StoreNetwork.APPLE_ROOM: "🍏 Appleroom",
    StoreNetwork.JABKO: "🍎 Ябко",
}


def format_store_name(store: Store | None) -> str:
    """Format a store's display name with its network prefix, e.g. '🍎 Ябко — Форум'."""
    if store is None:
        return "—"

    network_name = _NETWORK_LABELS.get(store.network, "🏪 Невідома мережа")
    return f"{network_name} — {store.name}"
