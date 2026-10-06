import argparse
import logging
import threading
from time import monotonic
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from app.core.config import settings
from app.database.session import SessionLocal, engine
from app.services.google_sheets_service import GoogleSheetsService
from app.services.staff_sync_service import SyncReport, sync_staff_rows

logger = logging.getLogger(__name__)

_JOB_ID = "google_sheets_staff_sync"
_POSTGRES_ADVISORY_LOCK_ID = 748392165
_SYNC_RUN_LOCK = threading.Lock()


def _acquire_distributed_lock():
    if engine.dialect.name != "postgresql":
        logger.warning(
            "PostgreSQL advisory lock unavailable for dialect %s; "
            "using the in-process sync lock only",
            engine.dialect.name,
        )
        return None, True

    connection = engine.connect()
    try:
        acquired = connection.execute(
            text("SELECT pg_try_advisory_lock(:lock_id)"),
            {"lock_id": _POSTGRES_ADVISORY_LOCK_ID},
        ).scalar_one()
        connection.commit()
    except Exception:
        connection.close()
        raise

    if not acquired:
        connection.close()
        return None, False
    return connection, True


def run_scheduled_staff_sync() -> SyncReport | None:
    started_at = monotonic()
    logger.info("Scheduled Google Sheets staff sync started.")

    if not _SYNC_RUN_LOCK.acquire(blocking=False):
        logger.warning("Scheduled staff sync skipped: another run is active in this process.")
        logger.info("Scheduled staff sync finished in %.2f seconds.", monotonic() - started_at)
        return None

    session = None
    lock_connection = None
    lock_acquired = False
    try:
        lock_connection, lock_acquired = _acquire_distributed_lock()
        if not lock_acquired:
            logger.info("Scheduled staff sync skipped: another process holds the PostgreSQL lock.")
            return None

        values = GoogleSheetsService.read_staff_rows()
        session = SessionLocal()
        report = sync_staff_rows(session, values, dry_run=False)
        logger.info(
            "Scheduled staff sync completed in %.2f seconds: "
            "created=%d updated=%d blocked=%d skipped=%d errors=%d details=%s",
            monotonic() - started_at,
            report.created,
            report.updated,
            report.blocked,
            report.skipped,
            len(report.errors),
            report.errors,
        )
        return report
    except Exception:
        if session is not None:
            session.rollback()
        logger.exception(
            "Scheduled Google Sheets staff sync failed after %.2f seconds.",
            monotonic() - started_at,
        )
        return None
    finally:
        if session is not None:
            session.close()
        if lock_connection is not None:
            try:
                unlocked = lock_connection.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": _POSTGRES_ADVISORY_LOCK_ID},
                ).scalar_one()
                lock_connection.commit()
                if not unlocked:
                    logger.warning("PostgreSQL staff sync advisory lock was not held at release.")
            except Exception:
                logger.exception("Failed to release PostgreSQL staff sync advisory lock.")
            finally:
                lock_connection.close()
        _SYNC_RUN_LOCK.release()
        logger.info("Scheduled staff sync job finished in %.2f seconds.", monotonic() - started_at)


def build_staff_sync_scheduler() -> BackgroundScheduler:
    if not 0 <= settings.STAFF_SYNC_HOUR <= 23:
        raise ValueError("STAFF_SYNC_HOUR must be between 0 and 23")
    if not 0 <= settings.STAFF_SYNC_MINUTE <= 59:
        raise ValueError("STAFF_SYNC_MINUTE must be between 0 and 59")

    timezone = ZoneInfo(settings.STAFF_SYNC_TIMEZONE)
    scheduler = BackgroundScheduler(timezone=timezone)
    scheduler.add_job(
        run_scheduled_staff_sync,
        trigger=CronTrigger(
            hour=settings.STAFF_SYNC_HOUR,
            minute=settings.STAFF_SYNC_MINUTE,
            timezone=timezone,
        ),
        id=_JOB_ID,
        name="Daily Google Sheets staff sync",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    return scheduler


def start_staff_sync_scheduler() -> BackgroundScheduler | None:
    scheduler = None
    try:
        scheduler = build_staff_sync_scheduler()
        scheduler.start()
        job = scheduler.get_job(_JOB_ID)
        logger.info(
            "Staff sync scheduled daily at %02d:%02d %s; next run: %s",
            settings.STAFF_SYNC_HOUR,
            settings.STAFF_SYNC_MINUTE,
            settings.STAFF_SYNC_TIMEZONE,
            job.next_run_time if job else "unknown",
        )
        return scheduler
    except Exception:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)
        logger.exception("Could not start staff sync scheduler; bot will continue without it.")
        return None


def get_next_staff_sync_run():
    scheduler = build_staff_sync_scheduler()
    scheduler.start(paused=True)
    try:
        job = scheduler.get_job(_JOB_ID)
        return job.next_run_time if job is not None else None
    finally:
        scheduler.shutdown(wait=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Safely inspect the staff sync schedule")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Print the next scheduled run without executing synchronization.",
    )
    args = parser.parse_args()
    if not args.check:
        parser.error("The scheduler runs inside the bot process; use --check for a safe schedule check")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        next_run = get_next_staff_sync_run()
        print(
            f"Staff sync scheduled daily at {settings.STAFF_SYNC_HOUR:02d}:"
            f"{settings.STAFF_SYNC_MINUTE:02d} {settings.STAFF_SYNC_TIMEZONE}; "
            f"next run: {next_run}; synchronization was not executed."
        )
        return 0
    except Exception:
        logger.exception("Staff sync schedule check failed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())