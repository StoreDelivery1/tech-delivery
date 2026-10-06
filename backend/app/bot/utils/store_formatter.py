from app.models.store import Store, StoreNetwork
from app.core.store_location_mapping import STORE_ID_DISPLAY_NAMES

_NETWORK_LABELS = {
    StoreNetwork.APPLE_ROOM: "🍏 Appleroom",
    StoreNetwork.JABKO: "🍎 Ябко",
}


def display_store_name(store: Store | None) -> str:
    if store is None:
        return "—"

    return STORE_ID_DISPLAY_NAMES.get(getattr(store, "id", None), store.name)


def format_store_name(store: Store | None) -> str:
    """Format a store's display name with its network prefix, e.g. '🍎 Ябко — Форум'."""
    if store is None:
        return "—"

    network_name = _NETWORK_LABELS.get(store.network, "🏪 Невідома мережа")
    return f"{network_name} — {display_store_name(store)}"
