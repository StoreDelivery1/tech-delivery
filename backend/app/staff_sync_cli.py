import argparse
import json
import logging
import sys

from app.database.session import SessionLocal
from app.services.google_sheets_service import GoogleSheetsService
from app.services.staff_sync_service import sync_staff_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync staff from Google Sheets")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Commit changes to the database. Default is read-only dry-run.",
    )
    parser.add_argument(
        "--only-username",
        help="Restrict this run to the single matching Google Sheet username.",
    )
    parser.add_argument(
        "--store-id",
        type=int,
        help="Override the location mapping for a targeted username only.",
    )
    args = parser.parse_args()
    if args.store_id is not None and args.only_username is None:
        parser.error("--store-id requires --only-username")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    db = None
    try:
        values = GoogleSheetsService.read_staff_rows()
        db = SessionLocal()
        report = sync_staff_rows(
            db,
            values,
            dry_run=not args.apply,
            only_username=args.only_username,
            store_id_override=args.store_id,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        if db is not None:
            db.rollback()
        print(
            json.dumps(
                {"errors": [{"type": type(exc).__name__}]},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1
    finally:
        if db is not None:
            db.close()


if __name__ == "__main__":
    raise SystemExit(main())