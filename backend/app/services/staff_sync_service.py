import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass, field

from sqlalchemy.orm import Session

from app.core.store_location_mapping import (
    CREATE_REQUIRED_SHEET_LOCATIONS,
    NON_STORE_COURIER_DEPARTMENTS,
    SHEET_LOCATION_STORE_IDS,
    UNRESOLVED_SHEET_LOCATIONS,
)
from app.models.store import Store
from app.models.user import User, UserRole, UserStatus
from app.services.activation_service import ActivationService
from app.services.store_service import StoreService

logger = logging.getLogger(__name__)

_HEADER_ALIASES = {
    "full_name": {"піб", "п.і.б.", "повне ім'я"},
    "username": {"telegram username", "username", "телеграм username"},
    "store": {"магазин", "локація"},
    "position": {"посада"},
    "dismissed": {"звільнений", "звільнений так/ні"},
    "telegram_id": {"telegram id", "telegram_id", "телеграм id"},
    "schedule": {"графік"},
}
_REQUIRED_HEADERS = set(_HEADER_ALIASES)
_YES_VALUES = {"так"}
_NO_VALUES = {"ні"}
_SCHEDULE_SPLIT = re.compile(r"[,;/|\s]+")


@dataclass(frozen=True)
class StaffRow:
    row_number: int
    full_name: str
    username: str | None
    store_name: str
    position: str
    dismissed: bool
    telegram_id: int | None
    telegram_id_missing: bool
    schedule: tuple[str, ...]
    errors: tuple[str, ...] = ()


@dataclass
class SyncReport:
    rows_found: int = 0
    created: int = 0
    updated: int = 0
    blocked: int = 0
    skipped: int = 0
    schedules_validated: int = 0
    alias_rows_available: int = 0
    alias_rows_processed: int = 0
    non_store_department_rows: int = 0
    missing_telegram_ids: list[str] = field(default_factory=list)
    location_issues: list[str] = field(default_factory=list)
    unresolved_locations: dict[str, int] = field(default_factory=dict)
    create_required_locations: dict[str, int] = field(default_factory=dict)
    targeted_preview: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize_text(value: str) -> str:
    value = value.strip().casefold()
    for apostrophe in ("’", "‘", "ʼ", "`", "´"):
        value = value.replace(apostrophe, "'")
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"\s*-\s*", " - ", value)
    return " ".join(value.split())


def _normalize_header(value: str) -> str:
    value = value.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return " ".join(value.casefold().split())


def _resolve_headers(header_row: list[str]) -> dict[str, int]:
    aliases = {
        alias: field_name
        for field_name, field_aliases in _HEADER_ALIASES.items()
        for alias in field_aliases
    }
    resolved: dict[str, int] = {}
    for index, raw_header in enumerate(header_row):
        normalized_header = _normalize_header(str(raw_header))
        field_name = (
            "dismissed"
            if "звільнений" in normalized_header
            else aliases.get(normalized_header)
        )
        if field_name is not None:
            if field_name in resolved:
                raise ValueError(f"Duplicate column for {field_name}")
            resolved[field_name] = index

    missing = _REQUIRED_HEADERS - resolved.keys()
    if missing:
        raise ValueError(
            "Missing required columns: " + ", ".join(sorted(missing))
        )
    return resolved


def _cell(cells: list[str], indexes: dict[str, int], field_name: str) -> str:
    index = indexes[field_name]
    if index >= len(cells) or cells[index] is None:
        return ""
    return str(cells[index]).strip()


def _parse_telegram_id(value: str) -> int | None:
    if not value:
        return None
    if not re.fullmatch(r"[0-9]+", value):
        raise ValueError("Telegram ID must contain digits only")
    telegram_id = int(value)
    if telegram_id <= 0:
        raise ValueError("Telegram ID must be positive")
    return telegram_id


def _parse_schedule(value: str) -> tuple[str, ...]:
    if not value:
        raise ValueError("Schedule is empty")
    tokens = tuple(token.upper() for token in _SCHEDULE_SPLIT.split(value.strip()) if token)
    invalid = [token for token in tokens if token not in {"Р", "З", "ВХ"}]
    if not tokens or invalid:
        raise ValueError("Schedule must contain only Р, З and/or ВХ")
    return tokens


def parse_staff_rows(values: list[list[str]]) -> tuple[list[StaffRow], int]:
    if not values:
        raise ValueError("Google Sheet is empty")

    indexes = _resolve_headers([str(value) for value in values[0]])
    parsed: list[StaffRow] = []
    rows_found = 0

    for row_number, raw_cells in enumerate(values[1:], start=2):
        cells = [str(value) if value is not None else "" for value in raw_cells]
        if not any(value.strip() for value in cells):
            continue
        rows_found += 1

        full_name = _cell(cells, indexes, "full_name")
        username = _cell(cells, indexes, "username").lstrip("@") or None
        store_name = _cell(cells, indexes, "store")
        position = _cell(cells, indexes, "position")
        dismissal_value = _normalize_text(_cell(cells, indexes, "dismissed"))
        telegram_value = _cell(cells, indexes, "telegram_id")
        schedule_value = _cell(cells, indexes, "schedule")
        errors: list[str] = []

        if not full_name:
            errors.append("Full name is empty")
        if not store_name:
            errors.append("Location is empty")
        if not position:
            errors.append("Position is empty")
        if dismissal_value in _YES_VALUES:
            dismissed = True
        elif dismissal_value in _NO_VALUES:
            dismissed = False
        else:
            dismissed = False
            errors.append("Dismissed must be Так or Ні")

        try:
            telegram_id = _parse_telegram_id(telegram_value)
        except ValueError as exc:
            telegram_id = None
            errors.append(str(exc))

        try:
            schedule = _parse_schedule(schedule_value)
        except ValueError as exc:
            schedule = ()
            errors.append(str(exc))

        parsed.append(
            StaffRow(
                row_number=row_number,
                full_name=full_name,
                username=username,
                store_name=store_name,
                position=position,
                dismissed=dismissed,
                telegram_id=telegram_id,
                telegram_id_missing=not telegram_value,
                schedule=schedule,
                errors=tuple(errors),
            )
        )

    return parsed, rows_found


def role_for_position(position: str) -> UserRole:
    normalized_position = _normalize_text(position)
    if normalized_position in {"кур'єр", "водій - кур'єр"}:
        return UserRole.COURIER
    return UserRole.SELLER


def _normalized_location(value: str) -> str:
    return " ".join(value.casefold().split())


def _location_matches(stores: list[Store], name: str) -> list[Store]:
    normalized_name = _normalized_location(name)
    return [
        store
        for store in stores
        if _normalized_location(store.name) == normalized_name
    ]


def _resolve_location(
    stores_by_id: dict[int, Store],
    stores: list[Store],
    location_name: str,
) -> tuple[Store | None, str, str | None]:
    unresolved_reason = UNRESOLVED_SHEET_LOCATIONS.get(location_name)
    if unresolved_reason is not None:
        return None, "unresolved", unresolved_reason

    if location_name in NON_STORE_COURIER_DEPARTMENTS:
        return None, "non_store_courier_department", None

    if location_name in CREATE_REQUIRED_SHEET_LOCATIONS:
        return None, "create_required", "Store metadata is required; automatic creation is disabled."

    store_id = SHEET_LOCATION_STORE_IDS.get(location_name)
    if store_id is not None:
        store = stores_by_id.get(store_id)
        if store is None:
            return None, "unresolved", f"Configured alias points to missing Store ID {store_id}."
        return store, "alias", None

    matches = _location_matches(stores, location_name)
    if len(matches) == 1:
        return matches[0], "exact", None
    if len(matches) > 1:
        return None, "unresolved", f"Multiple existing Store records match this name ({len(matches)} matches)."
    return None, "unknown", "No existing Store match; automatic creation is disabled."


def sync_staff_rows(
    db: Session,
    values: list[list[str]],
    *,
    dry_run: bool = True,
    only_username: str | None = None,
    store_id_override: int | None = None,
) -> SyncReport:
    rows, rows_found = parse_staff_rows(values)
    if store_id_override is not None and only_username is None:
        raise ValueError("--store-id requires --only-username")
    if only_username is not None:
        normalized_username = only_username.strip().lstrip("@").casefold()
        if not normalized_username:
            raise ValueError("--only-username cannot be empty")
        rows = [
            row
            for row in rows
            if row.username is not None
            and row.username.lstrip("@").casefold() == normalized_username
        ]
        if len(rows) != 1:
            raise ValueError(
                f"Expected exactly one Sheet row for username {only_username!r}; found {len(rows)}"
            )
        rows_found = 1

    report = SyncReport(rows_found=rows_found)
    stores = StoreService.get_stores(db)
    stores_by_id = {store.id: store for store in stores}
    override_store = None
    if store_id_override is not None:
        override_store = stores_by_id.get(store_id_override)
        if override_store is None:
            raise ValueError(f"Store ID {store_id_override} does not exist")

    report.alias_rows_available = sum(
        1
        for row in rows
        if SHEET_LOCATION_STORE_IDS.get(row.store_name) in stores_by_id
    )
    valid_ids = [row.telegram_id for row in rows if row.telegram_id is not None]
    duplicate_ids = {
        telegram_id
        for telegram_id, count in Counter(valid_ids).items()
        if count > 1
    }

    for row in rows:
        row_label = f"row {row.row_number} ({row.full_name or 'no name'})"
        if row.telegram_id_missing:
            report.missing_telegram_ids.append(row_label)
            if row.errors:
                report.errors.append(f"{row_label}: {'; '.join(row.errors)}")
            report.skipped += 1
            logger.warning("Skipped %s: Telegram ID is missing", row_label)
            continue
        if row.errors:
            report.errors.append(f"{row_label}: {'; '.join(row.errors)}")
            report.skipped += 1
            logger.warning("Skipped %s: %s", row_label, "; ".join(row.errors))
            continue
        if row.telegram_id is None:
            report.errors.append(f"{row_label}: Telegram ID is invalid")
            report.skipped += 1
            continue
        if row.telegram_id in duplicate_ids:
            message = f"{row_label}: duplicate Telegram ID {row.telegram_id} in sheet"
            report.errors.append(message)
            report.skipped += 1
            logger.warning("Skipped %s", message)
            continue

        if override_store is not None:
            store, resolution, resolution_reason = override_store, "store_override", None
        else:
            store, resolution, resolution_reason = _resolve_location(
                stores_by_id,
                stores,
                row.store_name,
            )
        if resolution == "non_store_courier_department":
            report.non_store_department_rows += 1
            logger.info(
                "Classified %s as COURIER department; no Store lookup or Store.id assignment",
                row_label,
            )
        elif store is None:
            if resolution == "unresolved":
                report.unresolved_locations[row.store_name] = (
                    report.unresolved_locations.get(row.store_name, 0) + 1
                )
            if resolution == "create_required":
                report.create_required_locations[row.store_name] = (
                    report.create_required_locations.get(row.store_name, 0) + 1
                )
            message = f"{row_label}: location {row.store_name!r} unresolved: {resolution_reason}"
            report.location_issues.append(message)
            report.skipped += 1
            logger.warning("Skipped %s", message)
            continue

        if resolution == "alias":
            report.alias_rows_processed += 1
            logger.info(
                "Resolved Sheet location alias for %s: %r -> Store ID %s",
                row_label,
                row.store_name,
                store.id,
            )

        report.schedules_validated += 1
        logger.info(
            "Validated schedule for %s: %s",
            row_label,
            ", ".join(row.schedule),
        )

        user = ActivationService.get_by_telegram(db, row.telegram_id)
        desired_status = UserStatus.INACTIVE if row.dismissed else UserStatus.ACTIVE
        desired_role = (
            UserRole.COURIER
            if resolution == "non_store_courier_department"
            else role_for_position(row.position)
        )
        effective_role = (
            user.role
            if user is not None and user.role == UserRole.ADMIN
            else desired_role
        )
        action = "update" if user is not None else "create"
        if only_username is not None:
            report.targeted_preview.append(
                {
                    "action": action,
                    "sheet_row": row.row_number,
                    "telegram_id": row.telegram_id,
                    "username": row.username,
                    "full_name": row.full_name,
                    "position": row.position,
                    "source_location": row.store_name,
                    "store_id": store.id if store is not None else None,
                    "store_name": store.name if store is not None else None,
                    "role": effective_role.value,
                    "status": desired_status.value,
                    "existing_user_id": user.id if user is not None else None,
                    "preserve_admin_role": user is not None and user.role == UserRole.ADMIN,
                }
            )

        if user is None:
            report.created += 1
            if row.dismissed:
                report.blocked += 1
            logger.info(
                "%s create Telegram ID %s as %s (%s)",
                "Would" if dry_run else "Will",
                row.telegram_id,
                effective_role.value,
                row.store_name,
            )
            if not dry_run:
                db.add(
                    User(
                        telegram_id=row.telegram_id,
                        username=row.username,
                        full_name=row.full_name,
                        role=desired_role,
                        status=desired_status,
                        store_id=store.id if store is not None else None,
                    )
                )
            continue

        report.updated += 1
        if row.dismissed:
            report.blocked += 1
        logger.info(
            "%s update Telegram ID %s (%s)",
            "Would" if dry_run else "Will",
            row.telegram_id,
            row.store_name,
        )
        if not dry_run:
            user.full_name = row.full_name
            if row.username is not None:
                user.username = row.username
            if user.role != UserRole.ADMIN:
                user.role = desired_role
            user.status = desired_status
            user.store_id = store.id if store is not None else None

    if not dry_run:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

    return report